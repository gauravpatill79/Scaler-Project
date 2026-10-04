from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ShippingAddressRequest(BaseModel):
    line1: str
    line2: str | None = None
    city: str
    state: str
    postal_code: str
    country: str


class PlaceOrderRequest(BaseModel):
    address: ShippingAddressRequest


class MarkShippedRequest(BaseModel):
    tracking_number: str


class OrderItemResponse(BaseModel):
    product_id: str
    name_snapshot: str
    price_snapshot: Decimal
    quantity: int
    line_total: Decimal


class OrderResponse(BaseModel):
    id: str
    user_id: str
    status: str
    items: list[OrderItemResponse]
    total_amount: Decimal
    currency: str
    tracking_number: str | None
    created_at: datetime
    updated_at: datetime
