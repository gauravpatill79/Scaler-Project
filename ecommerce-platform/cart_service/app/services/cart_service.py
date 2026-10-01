"""
MongoDB is the system of record for a cart. Redis is a cache-aside layer in
front of it (3.2's "quickly retrieve a user's cart" requirement). Every
mutation writes to Mongo first; if that succeeds, the cache is refreshed and
a Kafka event is published, both wrapped so a Redis or Kafka outage cannot
fail a request that already has a durable, correct Mongo document — the
same best-effort pattern used in Product Catalog Service.
"""
from __future__ import annotations

import logging

from app.domain.enums import CartEventType
from app.domain.exceptions import CartNotFoundError, ProductUnavailableError
from app.domain.models import Cart
from app.infrastructure.cache.redis_cache import CartCache
from app.infrastructure.clients.product_catalog_client import ProductCatalogClient
from app.infrastructure.messaging.event_publisher import CartEvent, EventPublisher
from app.repository.interfaces import CartRepository

logger = logging.getLogger(__name__)


class CartService:
    def __init__(
        self,
        repo: CartRepository,
        cache: CartCache,
        product_client: ProductCatalogClient,
        publisher: EventPublisher,
    ):
        self._repo = repo
        self._cache = cache
        self._product_client = product_client
        self._publisher = publisher

    def _safe_cache_set(self, cart: Cart) -> None:
        try:
            self._cache.set(cart)
        except Exception:
            logger.exception("Failed to update cart cache for user %s", cart.user_id)

    def _safe_cache_invalidate(self, user_id: str) -> None:
        try:
            self._cache.invalidate(user_id)
        except Exception:
            logger.exception("Failed to invalidate cart cache for user %s", user_id)

    def _safe_publish(self, topic: str, event: CartEvent) -> None:
        try:
            self._publisher.publish(topic, event)
        except Exception:
            logger.exception("Failed to publish %s event for user %s", topic, event.user_id)

    def get_cart(self, user_id: str) -> Cart:
        try:
            cached = self._cache.get(user_id)
            if cached is not None:
                return cached
        except Exception:
            logger.exception("Cart cache read failed for user %s, falling back to Mongo", user_id)

        cart = self._repo.find_by_user_id(user_id)
        if cart is None:
            raise CartNotFoundError(user_id)

        self._safe_cache_set(cart)
        return cart

    def _get_or_create_cart(self, user_id: str) -> Cart:
        cart = self._repo.find_by_user_id(user_id)
        return cart if cart is not None else Cart(user_id=user_id)

    def add_item(self, user_id: str, product_id: str, quantity: int) -> Cart:
        snapshot = self._product_client.get_product(product_id)
        if not snapshot.is_purchasable:
            raise ProductUnavailableError(product_id, "out of stock or not active")

        cart = self._get_or_create_cart(user_id)
        cart.add_item(product_id, snapshot.name, snapshot.price, quantity)
        self._repo.save(cart)
        self._safe_cache_set(cart)

        self._safe_publish(
            CartEventType.ITEM_ADDED.value,
            CartEvent(
                CartEventType.ITEM_ADDED,
                user_id,
                {"product_id": product_id, "quantity": quantity},
            ),
        )
        return cart

    def update_quantity(self, user_id: str, product_id: str, quantity: int) -> Cart:
        cart = self._repo.find_by_user_id(user_id)
        if cart is None:
            raise CartNotFoundError(user_id)

        cart.update_quantity(product_id, quantity)
        self._repo.save(cart)
        self._safe_cache_set(cart)

        self._safe_publish(
            CartEventType.ITEM_QUANTITY_UPDATED.value,
            CartEvent(
                CartEventType.ITEM_QUANTITY_UPDATED,
                user_id,
                {"product_id": product_id, "quantity": quantity},
            ),
        )
        return cart

    def remove_item(self, user_id: str, product_id: str) -> Cart:
        cart = self._repo.find_by_user_id(user_id)
        if cart is None:
            raise CartNotFoundError(user_id)

        cart.remove_item(product_id)
        self._repo.save(cart)
        self._safe_cache_set(cart)

        self._safe_publish(
            CartEventType.ITEM_REMOVED.value,
            CartEvent(CartEventType.ITEM_REMOVED, user_id, {"product_id": product_id}),
        )
        return cart

    def clear_cart(self, user_id: str) -> Cart:
        cart = self._repo.find_by_user_id(user_id)
        if cart is None:
            raise CartNotFoundError(user_id)

        cart.clear()
        self._repo.save(cart)
        self._safe_cache_set(cart)

        self._safe_publish(
            CartEventType.CART_CLEARED.value,
            CartEvent(CartEventType.CART_CLEARED, user_id, {}),
        )
        return cart

    def mark_checked_out(self, user_id: str) -> Cart:
        """Called by Order Management Service at the start of checkout (3.3)."""
        cart = self._repo.find_by_user_id(user_id)
        if cart is None:
            raise CartNotFoundError(user_id)

        cart.mark_checked_out()
        self._repo.save(cart)
        self._safe_cache_invalidate(user_id)

        self._safe_publish(
            CartEventType.CART_CHECKED_OUT.value,
            CartEvent(
                CartEventType.CART_CHECKED_OUT,
                user_id,
                {"item_count": cart.item_count(), "subtotal": str(cart.subtotal())},
            ),
        )
        return cart
