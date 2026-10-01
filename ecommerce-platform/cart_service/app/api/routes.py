from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_cart_service
from app.api.schemas import AddItemRequest, CartItemResponse, CartResponse, UpdateQuantityRequest
from app.domain.exceptions import DomainError
from app.domain.models import Cart
from app.services.cart_service import CartService

router = APIRouter(prefix="/api/v1/carts", tags=["Cart"])


def _to_response(cart: Cart) -> CartResponse:
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        status=cart.status.value,
        items=[
            CartItemResponse(
                product_id=i.product_id,
                name_snapshot=i.name_snapshot,
                price_snapshot=i.price_snapshot,
                quantity=i.quantity,
                line_total=i.line_total(),
            )
            for i in cart.items
        ],
        subtotal=cart.subtotal(),
        item_count=cart.item_count(),
        updated_at=cart.updated_at,
    )


@router.get("/{user_id}", response_model=CartResponse)
def get_cart(user_id: str, service: CartService = Depends(get_cart_service)):
    try:
        return _to_response(service.get_cart(user_id))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.post("/{user_id}/items", response_model=CartResponse, status_code=201)
def add_item(user_id: str, req: AddItemRequest, service: CartService = Depends(get_cart_service)):
    try:
        cart = service.add_item(user_id, req.product_id, req.quantity)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return _to_response(cart)


@router.patch("/{user_id}/items/{product_id}", response_model=CartResponse)
def update_quantity(
    user_id: str, product_id: str, req: UpdateQuantityRequest, service: CartService = Depends(get_cart_service)
):
    try:
        cart = service.update_quantity(user_id, product_id, req.quantity)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return _to_response(cart)


@router.delete("/{user_id}/items/{product_id}", response_model=CartResponse)
def remove_item(user_id: str, product_id: str, service: CartService = Depends(get_cart_service)):
    try:
        cart = service.remove_item(user_id, product_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return _to_response(cart)


@router.delete("/{user_id}", response_model=CartResponse)
def clear_cart(user_id: str, service: CartService = Depends(get_cart_service)):
    try:
        cart = service.clear_cart(user_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return _to_response(cart)


@router.post("/{user_id}/checkout", response_model=CartResponse)
def checkout(user_id: str, service: CartService = Depends(get_cart_service)):
    try:
        cart = service.mark_checked_out(user_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return _to_response(cart)
