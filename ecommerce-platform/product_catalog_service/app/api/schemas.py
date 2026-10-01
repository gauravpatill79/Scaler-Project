from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---- Requests ----

class CreateProductRequest(BaseModel):
    sku: str
    name: str
    description: str = ""
    price: Decimal = Field(gt=0)
    category_id: str
    image_urls: list[str] = Field(default_factory=list)
    specifications: dict[str, str] = Field(default_factory=dict)


class UpdatePriceRequest(BaseModel):
    price: Decimal = Field(gt=0)


class AdjustStockRequest(BaseModel):
    delta: int


class CreateCategoryRequest(BaseModel):
    name: str
    parent_id: str | None = None


# ---- Responses ----

class ProductImageResponse(BaseModel):
    url: str
    is_primary: bool


class ProductResponse(BaseModel):
    id: str
    sku: str
    name: str
    description: str
    price: Decimal
    currency: str
    category_id: str
    status: str
    stock_quantity: int
    images: list[ProductImageResponse]
    specifications: dict[str, str]
    created_at: datetime


class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    parent_id: str | None


class SearchResultResponse(BaseModel):
    id: str
    name: str
    price: float
    currency: str
    image_url: str | None
    in_stock: bool
