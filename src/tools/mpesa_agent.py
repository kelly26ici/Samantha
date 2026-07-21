# Samantha/src/payments/mpesa_agent.py

"""
M-Pesa payment integration for Samantha.

Exposes two tools for the LLM agent:
    - send_stk_push(payload: MpesaPaymentSchema) -> STKPushResult
    - check_transaction_status(checkout_request_id: str) -> TransactionStatus

Everything else (auth, C2B registration, callback handling, persistence)
is internal plumbing the agent never touches directly.
I'm doing a pretty good job here. I'm a genius!
"""

import base64
import datetime
import re
import logging
from enum import Enum
from typing import Literal, Dict, Any, Optional

from pydantic import BaseModel, Field, field_validator
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import TransportError, TimeoutException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.clients.httpx_client import httpx
import src.configs.settings as settings
from src.configs.settings import (
    CONSUMER_KEY,
    CONSUMER_SECRET,
    MPESA_BASE_URL,
    PASSKEY,
    CALLBACK_URL,
    RENDER_BASE_URL,
)
SHORTCODE = settings.SHORTCODE
C2B_CONFIRMATION_URL = f"{RENDER_BASE_URL}/mpesa/c2b/confirmation"
C2B_VALIDATION_URL = f"{RENDER_BASE_URL}/mpesa/c2b/validation"

logger = logging.getLogger("mpesa_agent")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class MpesaPaymentSchema(BaseModel):
    """Input for the send_stk_push tool."""

    Amount: int = Field(..., gt=0, description="Whole-number amount to charge, in KES")
    PartyA: str = Field(..., description="Payer's phone number, format 254XXXXXXXXX")
    AccountReference: str = Field(..., max_length=12, description="Short reference for the transaction, max 12 chars")
    TransactionDesc: str = Field(..., max_length=13, description="Short description of what's being paid for, max 13 chars")
    TransactionType: Literal["CustomerPayBillOnline", "CustomerBuyGoodsOnline"] = Field(
        default="CustomerPayBillOnline",
        description="CustomerBuyGoodsOnline for till numbers, CustomerPayBillOnline for paybills",
    )

    @field_validator("PartyA")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.fullmatch(r"254\d{9}", v):
            raise ValueError("Phone number must be in format 254XXXXXXXXX")
        return v


class TransactionState(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class STKPushResult(BaseModel):
    """What send_stk_push returns to the agent."""

    checkout_request_id: str
    merchant_request_id: str
    customer_message: str
    state: TransactionState = TransactionState.PENDING


class TransactionStatus(BaseModel):
    """What check_transaction_status returns to the agent."""

    checkout_request_id: str
    state: TransactionState
    amount: Optional[float] = None
    mpesa_receipt: Optional[str] = None
    phone_number: Optional[str] = None
    result_desc: Optional[str] = None


class C2BRegisterSchema(BaseModel):
    ShortCode: str = SHORTCODE
    ResponseType: Literal["Cancelled", "Completed"] = "Completed"
    ConfirmationURL: str = C2B_CONFIRMATION_URL
    ValidationURL: str = C2B_VALIDATION_URL


# --------------------------------------------------------------------------
# Persistence layer — maps CheckoutRequestID -> transaction state, so the
# async callback from Daraja can be matched back to the right conversation.
#
# This is an in-memory placeholder. Swap TransactionStore's guts for your
# existing Upstash Redis client (same one used for the rolling conversation
# buffer) so state survives restarts and works across multiple workers.
# --------------------------------------------------------------------------

class TransactionStore:
    """Minimal async key-value interface. Replace with Redis in production."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    async def set(self, checkout_request_id: str, data: Dict[str, Any]) -> None:
        self._store[checkout_request_id] = data

    async def get(self, checkout_request_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get(checkout_request_id)

    async def update(self, checkout_request_id: str, **fields) -> None:
        record = self._store.get(checkout_request_id, {})
        record.update(fields)
        self._store[checkout_request_id] = record


transaction_store = TransactionStore()


# --------------------------------------------------------------------------
# Internal Daraja client — not exposed to the agent directly.
# --------------------------------------------------------------------------

# Only retry genuine transient failures. Retrying on rejections (bad auth,
# malformed payload, Daraja-side validation errors) wastes calls and, for
# send_stk_push specifically, risks firing a second STK prompt to a
# customer's phone for a push that may have already gone through.
TRANSIENT_ERRORS = (TransportError, TimeoutException)


class MpesaAgentClient:
    def __init__(self):
        self.base_url = MPESA_BASE_URL
        self.consumer_key = CONSUMER_KEY
        self.consumer_secret = CONSUMER_SECRET
        self.shortcode = SHORTCODE
        self.passkey = PASSKEY
        self.callback_url = CALLBACK_URL
        self.client = httpx

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(TRANSIENT_ERRORS),
    )
    async def generate_access_token(self) -> str:
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        encoded_credentials = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {encoded_credentials}"}

        response = await self.client.get(url=url, headers=headers)
        response.raise_for_status()
        body = response.json()

        access_token = body.get("access_token")
        if not access_token:
            raise ValueError(f"Missing access_token in response: {body}")

        return access_token

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(TRANSIENT_ERRORS),
    )
    async def register_c2b_urls(
        self, response_type: Literal["Cancelled", "Completed"] = "Completed"
    ) -> Dict[str, Any]:
        token = await self.generate_access_token()
        url = f"{self.base_url}/mpesa/c2b/v1/registerurl"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = C2BRegisterSchema(ResponseType=response_type).model_dump()

        response = await self.client.post(url=url, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()
        logger.info(f"C2B Registration Response: {body}")

        return body

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(TRANSIENT_ERRORS),
    )
    async def _stk_push(self, payload: MpesaPaymentSchema) -> Dict[str, Any]:
        token = await self.generate_access_token()
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode("utf-8")
        ).decode("utf-8")

        body_payload = payload.model_dump()
        body_payload.update(
            {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "PartyB": self.shortcode,
                "PhoneNumber": payload.PartyA,
                "CallBackURL": self.callback_url,
            }
        )

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        response = await self.client.post(url=url, headers=headers, json=body_payload)
        response.raise_for_status()
        body = response.json()

        if body.get("ResponseCode") != "0":
            raise ValueError(f"M-Pesa API rejected STK push: {body}")

        return body

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=6),
        retry=retry_if_exception_type(TRANSIENT_ERRORS),
    )
    async def _query_stk_status(self, checkout_request_id: str) -> Dict[str, Any]:
        token = await self.generate_access_token()
        url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode("utf-8")
        ).decode("utf-8")

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        response = await self.client.post(url=url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


_client = MpesaAgentClient()


# --------------------------------------------------------------------------
# Agent-facing tools
# --------------------------------------------------------------------------

async def send_stk_push(payload: MpesaPaymentSchema) -> STKPushResult:
    """
    Tool: Send an M-Pesa STK Push prompt to a customer's phone, asking them
    to authorize a payment.

    This only confirms Safaricom ACCEPTED the request — it does not mean
    the customer has paid yet. The actual result arrives asynchronously via
    callback, usually within 20-60 seconds. Use check_transaction_status
    with the returned checkout_request_id to poll for the outcome if the
    customer needs an immediate answer.

    Args:
        payload: Amount, PartyA (payer phone in 2547XXXXXXXX format),
            AccountReference, TransactionDesc, TransactionType.

    Returns:
        STKPushResult with checkout_request_id (save this to look up the
        outcome later) and a customer-facing status message.

    Raises:
        Exception if Safaricom rejects the request outright (bad
        shortcode, malformed payload, auth failure, etc).
    """
    body = await _client._stk_push(payload)

    checkout_request_id = body["CheckoutRequestID"]
    merchant_request_id = body["MerchantRequestID"]

    await transaction_store.set(
        checkout_request_id,
        {
            "state": TransactionState.PENDING.value,
            "merchant_request_id": merchant_request_id,
            "amount": payload.Amount,
            "phone_number": payload.PartyA,
            "account_reference": payload.AccountReference,
        },
    )

    logger.info(f"STK push sent: {checkout_request_id} for {payload.PartyA}, KES {payload.Amount}")

    return STKPushResult(
        checkout_request_id=checkout_request_id,
        merchant_request_id=merchant_request_id,
        customer_message=body.get("CustomerMessage", "Payment prompt sent to your phone."),
        state=TransactionState.PENDING,
    )


async def check_transaction_status(checkout_request_id: str) -> TransactionStatus:
    """
    Tool: Check the current status of a payment previously started with
    send_stk_push.

    Checks local state first (updated instantly by Daraja's callback when
    it arrives). Falls back to querying Daraja directly if no callback has
    landed yet — useful if the customer asks "did it go through?" before
    the callback has had time to arrive, or if a callback was missed.

    Args:
        checkout_request_id: The ID returned by send_stk_push.

    Returns:
        TransactionStatus with the current state (pending/success/
        failed/cancelled) and payment details if completed.
    """
    record = await transaction_store.get(checkout_request_id)

    if record and record.get("state") != TransactionState.PENDING.value:
        return TransactionStatus(
            checkout_request_id=checkout_request_id,
            state=TransactionState(record["state"]),
            amount=record.get("amount"),
            mpesa_receipt=record.get("mpesa_receipt"),
            phone_number=record.get("phone_number"),
            result_desc=record.get("result_desc"),
        )

    # No definitive local state yet — ask Daraja directly.
    try:
        body = await _client._query_stk_status(checkout_request_id)
    except Exception as e:
        logger.warning(f"Status query failed for {checkout_request_id}: {e}")
        return TransactionStatus(checkout_request_id=checkout_request_id, state=TransactionState.PENDING)

    result_code = body.get("ResultCode")
    if result_code is None:
        return TransactionStatus(checkout_request_id=checkout_request_id, state=TransactionState.PENDING)

    if str(result_code) == "0":
        state = TransactionState.SUCCESS
    elif str(result_code) == "1032":
        state = TransactionState.CANCELLED
    else:
        state = TransactionState.FAILED

    await transaction_store.update(
        checkout_request_id, state=state.value, result_desc=body.get("ResultDesc")
    )

    return TransactionStatus(
        checkout_request_id=checkout_request_id,
        state=state,
        result_desc=body.get("ResultDesc"),
        amount=record.get("amount") if record else None,
        phone_number=record.get("phone_number") if record else None,
    )


# --------------------------------------------------------------------------
# Webhook endpoints — Daraja calls these, the agent never does.
# --------------------------------------------------------------------------

app = FastAPI()


@app.post("/mpesa/callback")
async def handle_stk_callback(request: Request):
    """
    Daraja calls this asynchronously with the outcome of an STK push.
    Always acknowledge with 200 + ResultCode 0 regardless of the payment
    outcome — Daraja retries the webhook if it doesn't get a clean ack,
    which is not what we want for a failed/cancelled payment.
    """
    callback_data = await request.json()
    logger.info(f"STK Callback: {callback_data}")

    ack = JSONResponse(content={"ResultCode": 0, "ResultDesc": "Received"})

    stk_callback = callback_data.get("Body", {}).get("stkCallback", {})
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")

    if not checkout_request_id:
        logger.error(f"Callback missing CheckoutRequestID: {callback_data}")
        return ack

    if result_code != 0:
        result_desc = stk_callback.get("ResultDesc", "Unknown error")
        state = TransactionState.CANCELLED if result_code == 1032 else TransactionState.FAILED
        logger.info(f"STK {state.value}: {checkout_request_id} - {result_desc}")
        await transaction_store.update(
            checkout_request_id, state=state.value, result_desc=result_desc
        )
        return ack

    try:
        items = stk_callback["CallbackMetadata"]["Item"]
        metadata = {item["Name"]: item.get("Value") for item in items}
    except (KeyError, TypeError) as e:
        logger.error(f"Malformed callback metadata: {e} — payload: {callback_data}")
        await transaction_store.update(
            checkout_request_id, state=TransactionState.FAILED.value, result_desc="Malformed callback"
        )
        return ack

    await transaction_store.update(
        checkout_request_id,
        state=TransactionState.SUCCESS.value,
        mpesa_receipt=metadata.get("MpesaReceiptNumber"),
        amount=metadata.get("Amount"),
        phone_number=metadata.get("PhoneNumber"),
        result_desc="Payment received",
    )

    logger.info(f"STK Success: {checkout_request_id} — {metadata}")
    return ack


@app.post("/mpesa/c2b/validation")
async def handle_c2b_validation(request: Request):
    validation_data = await request.json()
    logger.info(f"C2B Validation Payload: {validation_data}")
    return JSONResponse(content={"ResultCode": 0, "ResultDesc": "Accepted"})


@app.post("/mpesa/c2b/confirmation")
async def handle_c2b_confirmation(request: Request):
    confirmation_data = await request.json()
    logger.info(f"C2B Confirmation Payload: {confirmation_data}")

    parsed_metadata = {
        "transaction_type": confirmation_data.get("TransactionType"),
        "transaction_id": confirmation_data.get("TransID"),
        "transaction_time": confirmation_data.get("TransTime"),
        "amount": confirmation_data.get("TransAmount"),
        "business_shortcode": confirmation_data.get("BusinessShortCode"),
        "account_reference": confirmation_data.get("BillRefNumber"),
        "invoice_number": confirmation_data.get("InvoiceNumber"),
        "phone_number": confirmation_data.get("MSISDN"),
        "first_name": confirmation_data.get("FirstName"),
    }
    logger.info(f"Parsed C2B Record: {parsed_metadata}")

    # TODO: persist this the same way STK results are — currently logged only
    return JSONResponse(content={"ResultCode": 0, "ResultDesc": "Completed"})