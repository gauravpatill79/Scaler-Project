from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_payment_service
from app.api.schemas import PaymentResponse, ProcessPaymentRequest, ReceiptResponse
from app.domain.exceptions import DomainError
from app.domain.models import Payment
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


def _to_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        order_id=payment.order_id,
        user_id=payment.user_id,
        amount=payment.amount,
        currency=payment.currency,
        method=payment.method.value,
        status=payment.status.value,
        gateway_reference=payment.gateway_reference,
        receipt_number=payment.receipt_number,
        failure_reason=payment.failure_reason,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


@router.post("", response_model=PaymentResponse, status_code=201)
def process_payment(req: ProcessPaymentRequest, service: PaymentService = Depends(get_payment_service)):
    try:
        payment = service.process_payment(
            order_id=req.order_id,
            user_id=req.user_id,
            amount=req.amount,
            currency=req.currency,
            method=req.method,
        )
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return _to_response(payment)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: str, service: PaymentService = Depends(get_payment_service)):
    try:
        return _to_response(service.get_payment(payment_id))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.get("/by-order/{order_id}", response_model=PaymentResponse)
def get_payment_for_order(order_id: str, service: PaymentService = Depends(get_payment_service)):
    try:
        return _to_response(service.get_payment_for_order(order_id))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.get("/{payment_id}/receipt", response_model=ReceiptResponse)
def get_receipt(payment_id: str, service: PaymentService = Depends(get_payment_service)):
    try:
        return service.get_receipt(payment_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.post("/by-order/{order_id}/refund", response_model=PaymentResponse)
def refund_payment(order_id: str, service: PaymentService = Depends(get_payment_service)):
    try:
        return _to_response(service.refund_payment(order_id))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
