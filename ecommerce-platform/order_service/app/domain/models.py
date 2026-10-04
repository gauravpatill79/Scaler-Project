from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.domain.enums import OrderStatus
from app.domain.exceptions import InvalidOrderStateTransitionError
from app.domain.order_state import can_transition


def _new_id() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ShippingAddress:
    line1: str
    city: str
    state: str
    postal_code: str
    country: str
    line2: str | None = None


@dataclass
class OrderItem:
    product_id: str
    name_snapshot: str
    price_snapshot: Decimal
    quantity: int

    def line_total(self) -> Decimal:
        return self.price_snapshot * self.quantity


@dataclass
class Order:
    user_id: str
    items: list[OrderItem]
    address: ShippingAddress
    id: str = field(default_factory=_new_id)
    status: OrderStatus = OrderStatus.PENDING_PAYMENT
    currency: str = "INR"
    tracking_number: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def total(self) -> Decimal:
        return sum((item.line_total() for item in self.items), Decimal("0"))

    def transition_to(self, target: OrderStatus) -> None:
        if not can_transition(self.status, target):
            raise InvalidOrderStateTransitionError(self.status.value, target.value)
        self.status = target
        self.updated_at = _utcnow()

    def attach_tracking_number(self, tracking_number: str) -> None:
        self.tracking_number = tracking_number
        self.updated_at = _utcnow()
