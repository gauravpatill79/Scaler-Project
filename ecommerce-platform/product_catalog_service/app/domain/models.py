from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.domain.enums import ProductStatus
from app.domain.exceptions import InsufficientStockError, InvalidPriceError


def _new_id() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Category:
    """Nodes form a tree via parent_id — a lightweight Composite: the
    repository resolves children, so Category itself stays a plain record."""
    name: str
    slug: str
    id: str = field(default_factory=_new_id)
    parent_id: str | None = None


@dataclass
class ProductImage:
    product_id: str
    url: str
    id: str = field(default_factory=_new_id)
    is_primary: bool = False
    sort_order: int = 0


@dataclass
class ProductSpecification:
    product_id: str
    spec_key: str
    spec_value: str


@dataclass
class Product:
    sku: str
    name: str
    price: Decimal
    category_id: str
    id: str = field(default_factory=_new_id)
    description: str = ""
    currency: str = "INR"
    status: ProductStatus = ProductStatus.DRAFT
    stock_quantity: int = 0
    images: list[ProductImage] = field(default_factory=list)
    specifications: list[ProductSpecification] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    # ---- behaviour lives on the entity ----

    def is_purchasable(self) -> bool:
        return self.status == ProductStatus.ACTIVE and self.stock_quantity > 0

    def publish(self) -> None:
        self.status = ProductStatus.ACTIVE if self.stock_quantity > 0 else ProductStatus.OUT_OF_STOCK
        self.updated_at = _utcnow()

    def discontinue(self) -> None:
        self.status = ProductStatus.DISCONTINUED
        self.updated_at = _utcnow()

    def update_price(self, new_price: Decimal) -> None:
        if new_price <= 0:
            raise InvalidPriceError(new_price)
        self.price = new_price
        self.updated_at = _utcnow()

    def adjust_stock(self, delta: int) -> None:
        """delta is negative for a decrement (e.g. an order), positive for
        a restock. Raises if a decrement would push stock below zero."""
        new_quantity = self.stock_quantity + delta
        if new_quantity < 0:
            raise InsufficientStockError(self.id, requested=abs(delta), available=self.stock_quantity)
        self.stock_quantity = new_quantity
        if self.stock_quantity == 0 and self.status == ProductStatus.ACTIVE:
            self.status = ProductStatus.OUT_OF_STOCK
        elif self.stock_quantity > 0 and self.status == ProductStatus.OUT_OF_STOCK:
            self.status = ProductStatus.ACTIVE
        self.updated_at = _utcnow()

    def primary_image_url(self) -> str | None:
        primary = next((img for img in self.images if img.is_primary), None)
        return primary.url if primary else (self.images[0].url if self.images else None)
