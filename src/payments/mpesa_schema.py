# Samantha/src/payments/mpesa_schema.py

from pydantic import BaseModel, Field, field_validator
from typing import Literal
import re


class MpesaPaymentSchema(BaseModel):

    Amount: int = Field(..., gt=0, description="Whole-number amount to charge, in KES")
    PartyA: str = Field(..., description="Payer's phone number, format 2547XXXXXXXX")
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
            raise ValueError("Phone number must be in format 2547XXXXXXXX")
        return v