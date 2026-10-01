"""
Adapter pattern: CartService depends on ProductCatalogClient, never on an
HTTP library or the Product Catalog Service's wire format directly. This is
also the anti-corruption layer between the two services' domain models —
Product Catalog's response shape can change without CartService's domain
model changing, as long as this adapter is updated to match.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from app.domain.exceptions import ProductCatalogUnreachableError, ProductUnavailableError


@dataclass
class ProductSnapshot:
    product_id: str
    name: str
    price: Decimal
    currency: str
    is_purchasable: bool


class ProductCatalogClient(ABC):
    @abstractmethod
    def get_product(self, product_id: str) -> ProductSnapshot: ...


class HttpProductCatalogClient(ProductCatalogClient):
    def __init__(self, base_url: str | None = None, timeout_seconds: float = 3.0):
        import httpx

        self._base_url = base_url or os.getenv("PRODUCT_CATALOG_SERVICE_URL", "http://product-catalog-service:8002")
        self._timeout = timeout_seconds
        self._http = httpx

    def get_product(self, product_id: str) -> ProductSnapshot:
        try:
            response = self._http.get(
                f"{self._base_url}/api/v1/products/{product_id}", timeout=self._timeout
            )
        except self._http.HTTPError as exc:
            raise ProductCatalogUnreachableError(product_id) from exc

        if response.status_code == 404:
            raise ProductUnavailableError(product_id, "product does not exist")
        response.raise_for_status()

        body = response.json()
        is_purchasable = body["status"] == "ACTIVE" and body["stock_quantity"] > 0
        return ProductSnapshot(
            product_id=body["id"],
            name=body["name"],
            price=Decimal(str(body["price"])),
            currency=body["currency"],
            is_purchasable=is_purchasable,
        )


class InMemoryProductCatalogClient(ProductCatalogClient):
    def __init__(self, catalog: dict[str, ProductSnapshot] | None = None):
        self._catalog = catalog or {}

    def register(self, snapshot: ProductSnapshot) -> None:
        self._catalog[snapshot.product_id] = snapshot

    def get_product(self, product_id: str) -> ProductSnapshot:
        snapshot = self._catalog.get(product_id)
        if snapshot is None:
            raise ProductUnavailableError(product_id, "product does not exist")
        return snapshot
