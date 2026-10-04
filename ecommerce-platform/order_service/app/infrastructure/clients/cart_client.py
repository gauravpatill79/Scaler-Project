"""
Adapter pattern: isolates Order Service's domain from Cart Service's wire
format, same role as product_catalog_client.py plays for Product Catalog.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.exceptions import CartServiceUnreachableError


@dataclass
class CartItemSnapshot:
    product_id: str
    quantity: int


@dataclass
class CartSnapshot:
    user_id: str
    items: list[CartItemSnapshot]


class CartServiceClient(ABC):
    @abstractmethod
    def get_cart(self, user_id: str) -> CartSnapshot: ...

    @abstractmethod
    def checkout(self, user_id: str) -> None: ...


class HttpCartServiceClient(CartServiceClient):
    def __init__(self, base_url: str | None = None, timeout_seconds: float = 3.0):
        import httpx

        self._base_url = base_url or os.getenv("CART_SERVICE_URL", "http://cart-service:8003")
        self._timeout = timeout_seconds
        self._http = httpx

    def get_cart(self, user_id: str) -> CartSnapshot:
        try:
            response = self._http.get(f"{self._base_url}/api/v1/carts/{user_id}", timeout=self._timeout)
            response.raise_for_status()
        except self._http.HTTPError as exc:
            raise CartServiceUnreachableError(user_id) from exc

        body = response.json()
        items = [CartItemSnapshot(product_id=i["product_id"], quantity=i["quantity"]) for i in body["items"]]
        return CartSnapshot(user_id=user_id, items=items)

    def checkout(self, user_id: str) -> None:
        try:
            response = self._http.post(
                f"{self._base_url}/api/v1/carts/{user_id}/checkout", timeout=self._timeout
            )
            response.raise_for_status()
        except self._http.HTTPError as exc:
            raise CartServiceUnreachableError(user_id) from exc


class InMemoryCartServiceClient(CartServiceClient):
    def __init__(self, carts: dict[str, CartSnapshot] | None = None):
        self._carts = carts or {}
        self.checked_out: list[str] = []

    def register(self, snapshot: CartSnapshot) -> None:
        self._carts[snapshot.user_id] = snapshot

    def get_cart(self, user_id: str) -> CartSnapshot:
        return self._carts.get(user_id, CartSnapshot(user_id=user_id, items=[]))

    def checkout(self, user_id: str) -> None:
        self.checked_out.append(user_id)
