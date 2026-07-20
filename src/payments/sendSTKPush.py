# Samantha/src/payments/sendSTKPush.py

import base64
import datetime
from src.clients.httpx_client import httpx
from src.payments.access_token import generate_access_token
from src.payments.mpesa_schema import MpesaPaymentSchema
from src.configs.settings import SHORTCODE, PASSKEY, CALLBACK_URL, MPESA_BASE_URL


async def send_stk_push(payload: MpesaPaymentSchema) -> dict:

    generated_access_token = await generate_access_token()

    url = f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{SHORTCODE}{PASSKEY}{timestamp}".encode("utf-8")).decode("utf-8")

    body_payload = payload.model_dump()
    body_payload.update({
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "PartyB": SHORTCODE,
        "PhoneNumber": payload.PartyA,
        "CallBackURL": CALLBACK_URL,
    })

    headers = {
        "Authorization": f"Bearer {generated_access_token}",
        "Content-Type": "application/json",
    }

    try:
        response = await httpx.post(url=url, headers=headers, json=body_payload)
        response.raise_for_status()
        body = response.json()
    except httpx.HTTPStatusError as e:
        raise Exception(f"M-Pesa STK push request failed: {e.response.status_code} {e.response.text}") from e
    except httpx.RequestError as e:
        raise Exception(f"M-Pesa STK push request error: {e}") from e

    if body.get("ResponseCode") != "0":
        raise Exception(f"M-Pesa rejected STK push: {body}")

    return body