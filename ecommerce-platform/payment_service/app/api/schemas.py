from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ProcessPaymentRequest(BaseModel):
    order_id: str
    user_id: str
    amount: Decimal = Field(gt=0)
    currency: str = "INR"
    method: Literal["CARD", "NET_BANKING", "WALLET", "UPI"]


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    user_id: str
    amount: Decimal
    currency: str
    method: str
    status: str
    gateway_reference: str | None
    receipt_number: str | None
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime


class ReceiptResponse(BaseModel):
    receipt_number: str
    payment_id: str
    order_id: str
    amount: Decimal
    currency: str
    method: str
    paid_at: datetime
