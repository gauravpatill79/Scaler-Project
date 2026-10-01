from __future__ import annotations

from functools import lru_cache

from app.infrastructure.messaging.event_publisher import EventPublisher, KafkaEventPublisher
from app.infrastructure.search.elasticsearch_adapter import (
    ElasticsearchProductIndexer,
    ElasticsearchProductSearchAdapter,
    ProductSearchPort,
    SearchIndexer,
)
from app.repository.interfaces import CategoryRepository, ProductRepository
from app.repository.mysql_repository import MySQLCategoryRepository, MySQLProductRepository
from app.services.category_service import CategoryService
from app.services.product_service import ProductService
from app.services.search_service import ProductSearchService


@lru_cache
def get_product_repository() -> ProductRepository:
    return MySQLProductRepository()


@lru_cache
def get_category_repository() -> CategoryRepository:
    return MySQLCategoryRepository()


@lru_cache
def get_search_indexer() -> SearchIndexer:
    return ElasticsearchProductIndexer()


@lru_cache
def get_search_port() -> ProductSearchPort:
    return ElasticsearchProductSearchAdapter()


@lru_cache
def get_event_publisher() -> EventPublisher:
    return KafkaEventPublisher()


def get_product_service() -> ProductService:
    return ProductService(get_product_repository(), get_search_indexer(), get_event_publisher())


def get_category_service() -> CategoryService:
    return CategoryService(get_category_repository())


def get_search_service() -> ProductSearchService:
    return ProductSearchService(get_search_port())
