"""
Builder pattern: a Product has several optional, independently-assembled
parts (images, specifications) alongside required core fields. A fluent
builder keeps ProductService.create_product from hand-assembling a nested
object graph and makes construction order explicit and self-validating.
"""
from __future__ import annotations

from decimal import Decimal

from app.domain.exceptions import InvalidPriceError
from app.domain.models import Product, ProductImage, ProductSpecification


class ProductBuilder:
    def __init__(self):
        self._sku: str | None = None
        self._name: str | None = None
        self._description: str = ""
        self._price: Decimal | None = None
        self._currency: str = "INR"
        self._category_id: str | None = None
        self._images: list[ProductImage] = []
        self._specifications: list[ProductSpecification] = []

    def with_basic_info(self, sku: str, name: str, price: Decimal, description: str = "") -> "ProductBuilder":
        self._sku = sku
        self._name = name
        self._price = price
        self._description = description
        return self

    def with_currency(self, currency: str) -> "ProductBuilder":
        self._currency = currency
        return self

    def with_category(self, category_id: str) -> "ProductBuilder":
        self._category_id = category_id
        return self

    def with_images(self, urls: list[str], primary_index: int = 0) -> "ProductBuilder":
        self._images = [
            ProductImage(product_id="", url=url, is_primary=(i == primary_index), sort_order=i)
            for i, url in enumerate(urls)
        ]
        return self

    def with_specifications(self, specs: dict[str, str]) -> "ProductBuilder":
        self._specifications = [
            ProductSpecification(product_id="", spec_key=k, spec_value=v) for k, v in specs.items()
        ]
        return self

    def build(self) -> Product:
        if not self._sku or not self._name:
            raise ValueError("sku and name are required to build a Product")
        if self._price is None or self._price <= 0:
            raise InvalidPriceError(self._price)
        if not self._category_id:
            raise ValueError("category_id is required to build a Product")

        product = Product(
            sku=self._sku,
            name=self._name,
            description=self._description,
            price=self._price,
            currency=self._currency,
            category_id=self._category_id,
        )
        # Backfill product_id now that the Product (and its id) exists.
        for image in self._images:
            image.product_id = product.id
        for spec in self._specifications:
            spec.product_id = product.id
        product.images = self._images
        product.specifications = self._specifications
        return product
