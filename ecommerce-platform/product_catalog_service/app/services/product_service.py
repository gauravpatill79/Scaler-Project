"""
ProductService owns the "dual write" — every mutation writes to MySQL
(source of truth) first. Once that commit succeeds, the request is
considered successful: Elasticsearch indexing and Kafka publishing are
best-effort side effects, wrapped so a failure in either NEVER rolls back
or fails a request that already has a durable, correct MySQL row. Each
failure is logged with enough context (product id, operation) for a
reconciliation job or on-call engineer to replay it — favouring MySQL as
the sole authority over strict dual-write consistency.
"""
from __future__ import annotations

import logging
from decimal import Decimal

from app.domain.builders import ProductBuilder
from app.domain.enums import ProductEventType
from app.domain.exceptions import DuplicateSkuError, ProductNotFoundError
from app.domain.models import Product
from app.infrastructure.messaging.event_publisher import EventPublisher, ProductEvent
from app.infrastructure.search.elasticsearch_adapter import SearchIndexer
from app.repository.interfaces import ProductRepository

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, repo: ProductRepository, indexer: SearchIndexer, publisher: EventPublisher):
        self._repo = repo
        self._indexer = indexer
        self._publisher = publisher

    # ---- best-effort side effects: MySQL is already committed by the time
    # these run, so a failure here is logged and swallowed, never raised ----

    def _safe_index(self, product: Product) -> None:
        try:
            self._indexer.index(product)
        except Exception:
            logger.exception("Failed to index product %s in search — MySQL write already committed", product.id)

    def _safe_remove_from_index(self, product_id: str) -> None:
        try:
            self._indexer.remove(product_id)
        except Exception:
            logger.exception("Failed to remove product %s from search index", product_id)

    def _safe_publish(self, topic: str, event: ProductEvent) -> None:
        try:
            self._publisher.publish(topic, event)
        except Exception:
            logger.exception("Failed to publish %s event for product %s", topic, event.product_id)

    def create_product(
        self,
        sku: str,
        name: str,
        price: Decimal,
        category_id: str,
        description: str = "",
        image_urls: list[str] | None = None,
        specifications: dict[str, str] | None = None,
    ) -> Product:
        if self._repo.exists_by_sku(sku):
            raise DuplicateSkuError(sku)

        builder = ProductBuilder().with_basic_info(sku, name, price, description).with_category(category_id)
        if image_urls:
            builder = builder.with_images(image_urls)
        if specifications:
            builder = builder.with_specifications(specifications)
        product = builder.build()

        self._repo.save(product)  # source of truth — if this raises, the request correctly fails
        self._safe_index(product)
        self._safe_publish(
            ProductEventType.PRODUCT_CREATED.value,
            ProductEvent(ProductEventType.PRODUCT_CREATED, product.id, {"sku": product.sku}),
        )
        return product

    def get_product(self, product_id: str) -> Product:
        product = self._repo.find_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        return product

    def list_by_category(self, category_id: str, limit: int = 50, offset: int = 0) -> list[Product]:
        return self._repo.find_by_category(category_id, limit, offset)

    def update_price(self, product_id: str, new_price: Decimal) -> Product:
        product = self.get_product(product_id)
        old_price = product.price
        product.update_price(new_price)
        self._persist_and_reindex(product)

        self._safe_publish(
            ProductEventType.PRODUCT_PRICE_CHANGED.value,
            ProductEvent(
                ProductEventType.PRODUCT_PRICE_CHANGED,
                product.id,
                {"old_price": str(old_price), "new_price": str(new_price)},
            ),
        )
        return product

    def adjust_stock(self, product_id: str, delta: int) -> Product:
        """Called by Order Management Service (via Kafka consumer, not shown
        here) when an order is placed/cancelled, per the HLD's event flow."""
        product = self.get_product(product_id)
        product.adjust_stock(delta)
        self._persist_and_reindex(product)

        self._safe_publish(
            ProductEventType.PRODUCT_STOCK_CHANGED.value,
            ProductEvent(
                ProductEventType.PRODUCT_STOCK_CHANGED,
                product.id,
                {"delta": delta, "new_quantity": product.stock_quantity},
            ),
        )
        return product

    def publish_product(self, product_id: str) -> Product:
        product = self.get_product(product_id)
        product.publish()
        self._persist_and_reindex(product)
        return product

    def discontinue_product(self, product_id: str) -> None:
        product = self.get_product(product_id)
        product.discontinue()
        self._repo.save(product)
        self._safe_remove_from_index(product.id)
        self._safe_publish(
            ProductEventType.PRODUCT_DISCONTINUED.value,
            ProductEvent(ProductEventType.PRODUCT_DISCONTINUED, product.id, {}),
        )

    def _persist_and_reindex(self, product: Product) -> None:
        self._repo.save(product)  # source of truth — if this raises, the request correctly fails
        self._safe_index(product)
        self._safe_publish(
            ProductEventType.PRODUCT_UPDATED.value,
            ProductEvent(ProductEventType.PRODUCT_UPDATED, product.id, {"status": product.status.value}),
        )
