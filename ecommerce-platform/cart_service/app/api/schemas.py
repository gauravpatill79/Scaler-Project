from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AddItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)


class UpdateQuantityRequest(BaseModel):
    quantity: int = Field(ge=1)


class CartItemResponse(BaseModel):
    product_id: str
    name_snapshot: str
    price_snapshot: Decimal
    quantity: int
    line_total: Decimal


class CartResponse(BaseModel):
    id: str
    user_id: str
    status: str
    items: list[CartItemResponse]
    subtotal: Decimal
    item_count: int
    updated_at: datetime
