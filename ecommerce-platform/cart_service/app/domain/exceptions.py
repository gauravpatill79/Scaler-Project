class DomainError(Exception):
    http_status: int = 400


class CartNotFoundError(DomainError):
    http_status = 404

    def __init__(self, user_id: str):
        super().__init__(f"No cart found for user '{user_id}'")


class ItemNotInCartError(DomainError):
    http_status = 404

    def __init__(self, product_id: str):
        super().__init__(f"Product '{product_id}' is not in the cart")


class InvalidQuantityError(DomainError):
    http_status = 422

    def __init__(self, quantity: int):
        super().__init__(f"Quantity must be at least 1, got {quantity}")


class EmptyCartError(DomainError):
    http_status = 409

    def __init__(self, user_id: str):
        super().__init__(f"Cart for user '{user_id}' is empty")


class ProductUnavailableError(DomainError):
    http_status = 409

    def __init__(self, product_id: str, reason: str):
        super().__init__(f"Product '{product_id}' is unavailable: {reason}")


class ProductCatalogUnreachableError(DomainError):
    http_status = 503

    def __init__(self, product_id: str):
        super().__init__(f"Could not reach Product Catalog Service to validate product '{product_id}'")
