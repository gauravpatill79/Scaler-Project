"""
place_order is the checkout orchestrator described in the HLD's Part 3 flow.
Cart Service's price snapshot is treated as provisional, not authoritative —
every item is re-validated against Product Catalog Service at this moment,
since price or availability may have changed since the item was added to
the cart. MySQL remains the only write that can fail a request; the Cart
Service checkout call and the Kafka publish afterward are both best-effort
and logged on failure, matching the pattern used in the earlier services.
"""
from __future__ import annotations

import logging

from app.domain.enums import OrderEventType, OrderStatus
from app.domain.exceptions import EmptyOrderError, OrderNotFoundError, ProductNotPurchasableError
from app.domain.models import Order, OrderItem, ShippingAddress
from app.infrastructure.clients.cart_client import CartServiceClient
from app.infrastructure.clients.product_catalog_client import ProductCatalogClient
from app.infrastructure.messaging.event_publisher import EventPublisher, OrderEvent
from app.repository.interfaces import OrderRepository

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(
        self,
        repo: OrderRepository,
        cart_client: CartServiceClient,
        product_client: ProductCatalogClient,
        publisher: EventPublisher,
    ):
        self._repo = repo
        self._cart_client = cart_client
        self._product_client = product_client
        self._publisher = publisher

    def _safe_publish(self, topic: str, event: OrderEvent) -> None:
        try:
            self._publisher.publish(topic, event)
        except Exception:
            logger.exception("Failed to publish %s event for order %s", topic, event.order_id)

    def _safe_cart_checkout(self, user_id: str) -> None:
        try:
            self._cart_client.checkout(user_id)
        except Exception:
            logger.exception("Order placed for user %s but Cart Service checkout call failed", user_id)

    def place_order(self, user_id: str, address: ShippingAddress) -> Order:
        cart = self._cart_client.get_cart(user_id)
        if not cart.items:
            raise EmptyOrderError(user_id)

        order_items: list[OrderItem] = []
        for cart_item in cart.items:
            product = self._product_client.get_product(cart_item.product_id)
            if not product.is_purchasable:
                raise ProductNotPurchasableError(cart_item.product_id)
            order_items.append(
                OrderItem(
                    product_id=product.product_id,
                    name_snapshot=product.name,
                    price_snapshot=product.price,
                    quantity=cart_item.quantity,
                )
            )

        order = Order(user_id=user_id, items=order_items, address=address)
        self._repo.save(order)  # source of truth — if this raises, the request correctly fails

        self._safe_cart_checkout(user_id)
        self._safe_publish(
            OrderEventType.ORDER_CREATED.value,
            OrderEvent(
                OrderEventType.ORDER_CREATED,
                order.id,
                {"user_id": user_id, "total_amount": str(order.total()), "currency": order.currency},
            ),
        )
        return order

    def get_order(self, order_id: str) -> Order:
        order = self._repo.find_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order

    def list_orders(self, user_id: str, limit: int = 50, offset: int = 0) -> list[Order]:
        return self._repo.find_by_user(user_id, limit, offset)

    def _transition_and_save(self, order: Order, target: OrderStatus, event_type: OrderEventType, extra_payload: dict | None = None) -> Order:
        previous_status = order.status
        order.transition_to(target)
        self._repo.save(order, previous_status=previous_status)
        self._safe_publish(
            event_type.value,
            OrderEvent(event_type, order.id, extra_payload or {}),
        )
        return order

    def handle_payment_confirmed(self, order_id: str) -> Order:
        order = self.get_order(order_id)
        return self._transition_and_save(order, OrderStatus.PAID, OrderEventType.ORDER_PAID)

    def handle_payment_failed(self, order_id: str) -> Order:
        order = self.get_order(order_id)
        return self._transition_and_save(order, OrderStatus.PAYMENT_FAILED, OrderEventType.ORDER_PAYMENT_FAILED)

    def start_processing(self, order_id: str) -> Order:
        order = self.get_order(order_id)
        return self._transition_and_save(order, OrderStatus.PROCESSING, OrderEventType.ORDER_PROCESSING)

    def mark_shipped(self, order_id: str, tracking_number: str) -> Order:
        order = self.get_order(order_id)
        order.attach_tracking_number(tracking_number)
        return self._transition_and_save(
            order, OrderStatus.SHIPPED, OrderEventType.ORDER_SHIPPED, {"tracking_number": tracking_number}
        )

    def mark_delivered(self, order_id: str) -> Order:
        order = self.get_order(order_id)
        return self._transition_and_save(order, OrderStatus.DELIVERED, OrderEventType.ORDER_DELIVERED)

    def cancel_order(self, order_id: str) -> Order:
        order = self.get_order(order_id)
        return self._transition_and_save(order, OrderStatus.CANCELLED, OrderEventType.ORDER_CANCELLED)
