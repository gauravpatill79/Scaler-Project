from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_order_service
from app.api.schemas import (
    MarkShippedRequest,
    OrderItemResponse,
    OrderResponse,
    PlaceOrderRequest,
)
from app.domain.exceptions import DomainError
from app.domain.models import Order, ShippingAddress
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/v1", tags=["Orders"])


def _to_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status.value,
        items=[
            OrderItemResponse(
                product_id=i.product_id,
                name_snapshot=i.name_snapshot,
                price_snapshot=i.price_snapshot,
                quantity=i.quantity,
                line_total=i.line_total(),
            )
            for i in order.items
        ],
        total_amount=order.total(),
        currency=order.currency,
        tracking_number=order.tracking_number,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.post("/users/{user_id}/orders", response_model=OrderResponse, status_code=201)
def place_order(user_id: str, req: PlaceOrderRequest, service: OrderService = Depends(get_order_service)):
    address = ShippingAddress(**req.address.model_dump())
    try:
        order = service.place_order(user_id, address)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return _to_response(order)


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, service: OrderService = Depends(get_order_service)):
    try:
        return _to_response(service.get_order(order_id))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.get("/users/{user_id}/orders", response_model=list[OrderResponse])
def list_orders(
    user_id: str,
    limit: int = Query(50, le=100),
    offset: int = 0,
    service: OrderService = Depends(get_order_service),
):
    return [_to_response(o) for o in service.list_orders(user_id, limit, offset)]


@router.get("/orders/{order_id}/tracking")
def track_order(order_id: str, service: OrderService = Depends(get_order_service)):
    try:
        order = service.get_order(order_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return {
        "order_id": order.id,
        "status": order.status.value,
        "tracking_number": order.tracking_number,
        "updated_at": order.updated_at,
    }


@router.post("/orders/{order_id}/processing", response_model=OrderResponse)
def start_processing(order_id: str, service: OrderService = Depends(get_order_service)):
    try:
        return _to_response(service.start_processing(order_id))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.post("/orders/{order_id}/ship", response_model=OrderResponse)
def mark_shipped(order_id: str, req: MarkShippedRequest, service: OrderService = Depends(get_order_service)):
    try:
        return _to_response(service.mark_shipped(order_id, req.tracking_number))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.post("/orders/{order_id}/deliver", response_model=OrderResponse)
def mark_delivered(order_id: str, service: OrderService = Depends(get_order_service)):
    try:
        return _to_response(service.mark_delivered(order_id))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(order_id: str, service: OrderService = Depends(get_order_service)):
    try:
        return _to_response(service.cancel_order(order_id))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
