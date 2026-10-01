from __future__ import annotations

from decimal import Decimal

from bson.decimal128 import Decimal128

from app.domain.enums import CartStatus
from app.domain.models import Cart, CartItem
from app.infrastructure.db.database import Database
from app.repository.interfaces import CartRepository


def _item_to_document(item: CartItem) -> dict:
    return {
        "product_id": item.product_id,
        "name_snapshot": item.name_snapshot,
        "price_snapshot": Decimal128(item.price_snapshot),
        "quantity": item.quantity,
        "added_at": item.added_at,
    }


def _document_to_item(doc: dict) -> CartItem:
    return CartItem(
        product_id=doc["product_id"],
        name_snapshot=doc["name_snapshot"],
        price_snapshot=doc["price_snapshot"].to_decimal(),
        quantity=doc["quantity"],
        added_at=doc["added_at"],
    )


def _cart_to_document(cart: Cart) -> dict:
    return {
        "_id": cart.id,
        "user_id": cart.user_id,
        "items": [_item_to_document(i) for i in cart.items],
        "status": cart.status.value,
        "created_at": cart.created_at,
        "updated_at": cart.updated_at,
    }


def _document_to_cart(doc: dict) -> Cart:
    return Cart(
        id=doc["_id"],
        user_id=doc["user_id"],
        items=[_document_to_item(i) for i in doc["items"]],
        status=CartStatus(doc["status"]),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


class MongoCartRepository(CartRepository):
    def __init__(self, db: Database | None = None):
        self._db = db or Database.instance()

    def save(self, cart: Cart) -> None:
        self._db.carts.replace_one({"user_id": cart.user_id}, _cart_to_document(cart), upsert=True)

    def find_by_user_id(self, user_id: str) -> Cart | None:
        doc = self._db.carts.find_one({"user_id": user_id})
        return _document_to_cart(doc) if doc else None

    def delete(self, user_id: str) -> None:
        self._db.carts.delete_one({"user_id": user_id})
