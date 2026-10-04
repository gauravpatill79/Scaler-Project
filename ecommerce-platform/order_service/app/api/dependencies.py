from __future__ import annotations

from functools import lru_cache

from app.infrastructure.clients.cart_client import CartServiceClient, HttpCartServiceClient
from app.infrastructure.clients.product_catalog_client import HttpProductCatalogClient, ProductCatalogClient
from app.infrastructure.messaging.event_publisher import EventPublisher, KafkaEventPublisher
from app.repository.interfaces import OrderRepository
from app.repository.mysql_repository import MySQLOrderRepository
from app.services.order_service import OrderService


@lru_cache
def get_order_repository() -> OrderRepository:
    return MySQLOrderRepository()


@lru_cache
def get_cart_client() -> CartServiceClient:
    return HttpCartServiceClient()


@lru_cache
def get_product_catalog_client() -> ProductCatalogClient:
    return HttpProductCatalogClient()


@lru_cache
def get_event_publisher() -> EventPublisher:
    return KafkaEventPublisher()


def get_order_service() -> OrderService:
    return OrderService(
        get_order_repository(), get_cart_client(), get_product_catalog_client(), get_event_publisher()
    )
