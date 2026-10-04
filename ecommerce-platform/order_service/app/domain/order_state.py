"""
State pattern: each OrderStatus has a corresponding state object that knows
only which statuses it can legally move to. Order.transition_to() consults
the current status's state object instead of embedding an if/elif chain of
transition rules — adding a new status later means adding one new state
class and registering it, not touching the validation logic itself.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.enums import OrderStatus


class OrderState(ABC):
    @abstractmethod
    def allowed_next_states(self) -> set[OrderStatus]: ...


class PendingPaymentState(OrderState):
    def allowed_next_states(self) -> set[OrderStatus]:
        return {OrderStatus.PAID, OrderStatus.PAYMENT_FAILED, OrderStatus.CANCELLED}


class PaidState(OrderState):
    def allowed_next_states(self) -> set[OrderStatus]:
        return {OrderStatus.PROCESSING, OrderStatus.CANCELLED}


class ProcessingState(OrderState):
    def allowed_next_states(self) -> set[OrderStatus]:
        return {OrderStatus.SHIPPED, OrderStatus.CANCELLED}


class ShippedState(OrderState):
    def allowed_next_states(self) -> set[OrderStatus]:
        return {OrderStatus.DELIVERED}


class TerminalState(OrderState):
    """Shared by DELIVERED, CANCELLED, and PAYMENT_FAILED — none permit
    further transitions in this LLD pass."""

    def allowed_next_states(self) -> set[OrderStatus]:
        return set()


STATE_REGISTRY: dict[OrderStatus, OrderState] = {
    OrderStatus.PENDING_PAYMENT: PendingPaymentState(),
    OrderStatus.PAID: PaidState(),
    OrderStatus.PROCESSING: ProcessingState(),
    OrderStatus.SHIPPED: ShippedState(),
    OrderStatus.DELIVERED: TerminalState(),
    OrderStatus.CANCELLED: TerminalState(),
    OrderStatus.PAYMENT_FAILED: TerminalState(),
}


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    return target in STATE_REGISTRY[current].allowed_next_states()
