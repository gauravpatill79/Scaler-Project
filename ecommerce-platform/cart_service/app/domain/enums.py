from enum import Enum


class CartStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CHECKED_OUT = "CHECKED_OUT"
    ABANDONED = "ABANDONED"


class CartEventType(str, Enum):
    ITEM_ADDED = "cart.item_added"
    ITEM_REMOVED = "cart.item_removed"
    ITEM_QUANTITY_UPDATED = "cart.item_quantity_updated"
    CART_CLEARED = "cart.cleared"
    CART_CHECKED_OUT = "cart.checked_out"
