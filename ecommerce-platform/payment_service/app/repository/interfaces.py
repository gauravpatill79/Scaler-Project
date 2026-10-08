from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.enums import PaymentStatus
from app.domain.models import Payment


class PaymentRepository(ABC):
    @abstractmethod
    def save(self, payment: Payment, previous_status: PaymentStatus | None = None) -> None: ...

    @abstractmethod
    def find_by_id(self, payment_id: str) -> Payment | None: ...

    @abstractmethod
    def find_by_order_id(self, order_id: str) -> Payment | None: ...
