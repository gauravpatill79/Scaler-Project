from __future__ import annotations

from functools import lru_cache

from app.infrastructure.cache.redis_cache import CartCache, RedisCartCache
from app.infrastructure.clients.product_catalog_client import HttpProductCatalogClient, ProductCatalogClient
from app.infrastructure.messaging.event_publisher import EventPublisher, KafkaEventPublisher
from app.repository.interfaces import CartRepository
from app.repository.mongo_repository import MongoCartRepository
from app.services.cart_service import CartService


@lru_cache
def get_cart_repository() -> CartRepository:
    return MongoCartRepository()


@lru_cache
def get_cart_cache() -> CartCache:
    return RedisCartCache()


@lru_cache
def get_product_catalog_client() -> ProductCatalogClient:
    return HttpProductCatalogClient()


@lru_cache
def get_event_publisher() -> EventPublisher:
    return KafkaEventPublisher()


def get_cart_service() -> CartService:
    return CartService(
        get_cart_repository(), get_cart_cache(), get_product_catalog_client(), get_event_publisher()
    )
