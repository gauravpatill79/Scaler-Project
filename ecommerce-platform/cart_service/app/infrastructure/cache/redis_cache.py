"""
Cache-Aside pattern: CartService checks RedisCartCache first on a read; on a
miss it falls back to MongoCartRepository and populates the cache. Every
write goes through Mongo first (source of truth) and then refreshes the
cache — the cache never diverges from Mongo for longer than one request.
"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal

from app.domain.enums import CartStatus
from app.domain.models import Cart, CartItem

_DEFAULT_TTL_SECONDS = 1800  # cart cache entries expire independently of cart lifecycle


class CartCache(ABC):
    @abstractmethod
    def get(self, user_id: str) -> Cart | None: ...

    @abstractmethod
    def set(self, cart: Cart) -> None: ...

    @abstractmethod
    def invalidate(self, user_id: str) -> None: ...


def _serialize(cart: Cart) -> str:
    body = asdict(cart)
    body["status"] = cart.status.value
    body["created_at"] = cart.created_at.isoformat()
    body["updated_at"] = cart.updated_at.isoformat()
    for item in body["items"]:
        item["price_snapshot"] = str(item["price_snapshot"])
        item["added_at"] = item["added_at"].isoformat() if isinstance(item["added_at"], datetime) else item["added_at"]
    return json.dumps(body)


def _deserialize(raw: str) -> Cart:
    body = json.loads(raw)
    items = [
        CartItem(
            product_id=i["product_id"],
            name_snapshot=i["name_snapshot"],
            price_snapshot=Decimal(i["price_snapshot"]),
            quantity=i["quantity"],
            added_at=datetime.fromisoformat(i["added_at"]),
        )
        for i in body["items"]
    ]
    return Cart(
        id=body["id"],
        user_id=body["user_id"],
        items=items,
        status=CartStatus(body["status"]),
        created_at=datetime.fromisoformat(body["created_at"]),
        updated_at=datetime.fromisoformat(body["updated_at"]),
    )


class RedisCartCache(CartCache):
    def __init__(self, host: str | None = None, port: int = 6379, ttl_seconds: int = _DEFAULT_TTL_SECONDS):
        import redis

        self._client = redis.Redis(
            host=host or os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", str(port))),
            decode_responses=True,
        )
        self._ttl = ttl_seconds

    def _key(self, user_id: str) -> str:
        return f"cart:{user_id}"

    def get(self, user_id: str) -> Cart | None:
        raw = self._client.get(self._key(user_id))
        return _deserialize(raw) if raw else None

    def set(self, cart: Cart) -> None:
        self._client.setex(self._key(cart.user_id), self._ttl, _serialize(cart))

    def invalidate(self, user_id: str) -> None:
        self._client.delete(self._key(user_id))


class InMemoryCartCache(CartCache):
    def __init__(self):
        self._store: dict[str, Cart] = {}

    def get(self, user_id: str) -> Cart | None:
        return self._store.get(user_id)

    def set(self, cart: Cart) -> None:
        self._store[cart.user_id] = cart

    def invalidate(self, user_id: str) -> None:
        self._store.pop(user_id, None)
