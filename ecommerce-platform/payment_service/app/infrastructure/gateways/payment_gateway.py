"""
Strategy pattern: one gateway strategy per payment method, selected by
PaymentGatewayFactory. PaymentService depends only on PaymentGatewayStrategy
and never branches on method type itself — adding a new method (e.g. BNPL)
means a new strategy class and a factory registration, not a new if/elif in
the service layer.

These are simulated gateway integrations. No real PSP (Razorpay, Stripe,
etc.) is wired in — each strategy approves the charge and returns a
generated reference, standing in for what would be a real authorize/capture
call to that provider's SDK.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from app.domain.enums import PaymentMethod
from app.domain.exceptions import UnsupportedPaymentMethodError


@dataclass
class GatewayResult:
    success: bool
    gateway_reference: str | None = None
    failure_reason: str | None = None


class PaymentGatewayStrategy(ABC):
    @abstractmethod
    def charge(self, amount: Decimal, currency: str, payment_details: dict) -> GatewayResult: ...


class CardGatewayStrategy(PaymentGatewayStrategy):
    def charge(self, amount: Decimal, currency: str, payment_details: dict) -> GatewayResult:
        return GatewayResult(success=True, gateway_reference=f"CARD-{uuid.uuid4().hex[:10].upper()}")


class NetBankingGatewayStrategy(PaymentGatewayStrategy):
    def charge(self, amount: Decimal, currency: str, payment_details: dict) -> GatewayResult:
        return GatewayResult(success=True, gateway_reference=f"NB-{uuid.uuid4().hex[:10].upper()}")


class WalletGatewayStrategy(PaymentGatewayStrategy):
    def charge(self, amount: Decimal, currency: str, payment_details: dict) -> GatewayResult:
        return GatewayResult(success=True, gateway_reference=f"WLT-{uuid.uuid4().hex[:10].upper()}")


class UpiGatewayStrategy(PaymentGatewayStrategy):
    def charge(self, amount: Decimal, currency: str, payment_details: dict) -> GatewayResult:
        return GatewayResult(success=True, gateway_reference=f"UPI-{uuid.uuid4().hex[:10].upper()}")


class PaymentGatewayFactory:
    def __init__(self):
        self._strategies: dict[PaymentMethod, PaymentGatewayStrategy] = {
            PaymentMethod.CARD: CardGatewayStrategy(),
            PaymentMethod.NET_BANKING: NetBankingGatewayStrategy(),
            PaymentMethod.WALLET: WalletGatewayStrategy(),
            PaymentMethod.UPI: UpiGatewayStrategy(),
        }

    def get_strategy(self, method: PaymentMethod) -> PaymentGatewayStrategy:
        strategy = self._strategies.get(method)
        if strategy is None:
            raise UnsupportedPaymentMethodError(method.value)
        return strategy
