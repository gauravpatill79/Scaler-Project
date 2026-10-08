from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.domain.enums import PaymentMethod, PaymentStatus
from app.domain.exceptions import RefundNotAllowedError


def _new_id() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_receipt_number() -> str:
    return f"RCPT-{uuid.uuid4().hex[:12].upper()}"


@dataclass
class Payment:
    order_id: str
    user_id: str
    amount: Decimal
    method: PaymentMethod
    id: str = field(default_factory=_new_id)
    currency: str = "INR"
    status: PaymentStatus = PaymentStatus.PENDING
    gateway_reference: str | None = None
    receipt_number: str | None = None
    failure_reason: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def mark_success(self, gateway_reference: str) -> None:
        self.status = PaymentStatus.SUCCESS
        self.gateway_reference = gateway_reference
        self.receipt_number = _new_receipt_number()
        self.failure_reason = None
        self.updated_at = _utcnow()

    def mark_failed(self, reason: str) -> None:
        self.status = PaymentStatus.FAILED
        self.failure_reason = reason
        self.updated_at = _utcnow()

    def mark_refunded(self) -> None:
        if self.status != PaymentStatus.SUCCESS:
            raise RefundNotAllowedError(self.id, self.status.value)
        self.status = PaymentStatus.REFUNDED
        self.updated_at = _utcnow()

    def is_successful(self) -> bool:
        return self.status == PaymentStatus.SUCCESS
