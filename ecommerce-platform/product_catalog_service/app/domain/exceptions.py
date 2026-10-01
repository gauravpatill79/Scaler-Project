class DomainError(Exception):
    http_status: int = 400


class ProductNotFoundError(DomainError):
    http_status = 404

    def __init__(self, identifier: str):
        super().__init__(f"Product '{identifier}' was not found")


class DuplicateSkuError(DomainError):
    http_status = 409

    def __init__(self, sku: str):
        super().__init__(f"A product with SKU '{sku}' already exists")


class CategoryNotFoundError(DomainError):
    http_status = 404

    def __init__(self, identifier: str):
        super().__init__(f"Category '{identifier}' was not found")


class InvalidPriceError(DomainError):
    http_status = 422

    def __init__(self, price):
        super().__init__(f"Price must be greater than zero, got {price}")


class InsufficientStockError(DomainError):
    http_status = 409

    def __init__(self, product_id: str, requested: int, available: int):
        super().__init__(
            f"Product '{product_id}' has only {available} units available, requested {requested}"
        )
