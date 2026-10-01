"""
Cart is the aggregate root (DDD terminology): CartItem has no independent
identity or repository of its own — it is only ever created, modified, or
removed through Cart's methods, which is what keeps invariants like "one
entry per product_id" and "quantity >= 1" from being violated by code
outside this module.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.domain.enums import CartStatus
from app.domain.exceptions import EmptyCartError, InvalidQuantityError, ItemNotInCartError


def _new_id() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CartItem:
    product_id: str
    name_snapshot: str
    price_snapshot: Decimal
    quantity: int
    added_at: datetime = field(default_factory=_utcnow)

    def line_total(self) -> Decimal:
        return self.price_snapshot * self.quantity


@dataclass
class Cart:
    user_id: str
    id: str = field(default_factory=_new_id)
    items: list[CartItem] = field(default_factory=list)
    status: CartStatus = CartStatus.ACTIVE
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def _find_item(self, product_id: str) -> CartItem | None:
        return next((i for i in self.items if i.product_id == product_id), None)

    def add_item(self, product_id: str, name: str, price: Decimal, quantity: int) -> None:
        if quantity < 1:
            raise InvalidQuantityError(quantity)

        existing = self._find_item(product_id)
        if existing is not None:
            existing.quantity += quantity
            existing.price_snapshot = price  # refreshed to current catalog price on every add
            existing.name_snapshot = name
        else:
            self.items.append(
                CartItem(product_id=product_id, name_snapshot=name, price_snapshot=price, quantity=quantity)
            )
        self.updated_at = _utcnow()

    def update_quantity(self, product_id: str, quantity: int) -> None:
        if quantity < 1:
            raise InvalidQuantityError(quantity)

        item = self._find_item(product_id)
        if item is None:
            raise ItemNotInCartError(product_id)
        item.quantity = quantity
        self.updated_at = _utcnow()

    def remove_item(self, product_id: str) -> None:
        item = self._find_item(product_id)
        if item is None:
            raise ItemNotInCartError(product_id)
        self.items.remove(item)
        self.updated_at = _utcnow()

    def clear(self) -> None:
        self.items = []
        self.updated_at = _utcnow()

    def mark_checked_out(self) -> None:
        if not self.items:
            raise EmptyCartError(self.user_id)
        self.status = CartStatus.CHECKED_OUT
        self.updated_at = _utcnow()

    def subtotal(self) -> Decimal:
        return sum((item.line_total() for item in self.items), Decimal("0"))

    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)
