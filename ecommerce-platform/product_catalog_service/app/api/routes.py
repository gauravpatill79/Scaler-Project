from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_category_service, get_product_service, get_search_service
from app.api.schemas import (
    AdjustStockRequest,
    CategoryResponse,
    CreateCategoryRequest,
    CreateProductRequest,
    ProductImageResponse,
    ProductResponse,
    SearchResultResponse,
    UpdatePriceRequest,
)
from app.domain.exceptions import DomainError
from app.domain.models import Product
from app.services.category_service import CategoryService
from app.services.product_service import ProductService
from app.services.search_service import ProductSearchService

router = APIRouter(prefix="/api/v1", tags=["Product Catalog"])


def _to_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        price=product.price,
        currency=product.currency,
        category_id=product.category_id,
        status=product.status.value,
        stock_quantity=product.stock_quantity,
        images=[ProductImageResponse(url=i.url, is_primary=i.is_primary) for i in product.images],
        specifications={s.spec_key: s.spec_value for s in product.specifications},
        created_at=product.created_at,
    )


@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(req: CreateProductRequest, service: ProductService = Depends(get_product_service)):
    try:
        product = service.create_product(
            sku=req.sku,
            name=req.name,
            price=req.price,
            category_id=req.category_id,
            description=req.description,
            image_urls=req.image_urls,
            specifications=req.specifications,
        )
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return _to_response(product)


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, service: ProductService = Depends(get_product_service)):
    try:
        return _to_response(service.get_product(product_id))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.get("/categories/{category_id}/products", response_model=list[ProductResponse])
def list_products_by_category(
    category_id: str,
    limit: int = Query(50, le=100),
    offset: int = 0,
    service: ProductService = Depends(get_product_service),
):
    return [_to_response(p) for p in service.list_by_category(category_id, limit, offset)]


@router.patch("/products/{product_id}/price", response_model=ProductResponse)
def update_price(product_id: str, req: UpdatePriceRequest, service: ProductService = Depends(get_product_service)):
    try:
        return _to_response(service.update_price(product_id, req.price))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.patch("/products/{product_id}/stock", response_model=ProductResponse)
def adjust_stock(product_id: str, req: AdjustStockRequest, service: ProductService = Depends(get_product_service)):
    try:
        return _to_response(service.adjust_stock(product_id, req.delta))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.post("/products/{product_id}/publish", response_model=ProductResponse)
def publish_product(product_id: str, service: ProductService = Depends(get_product_service)):
    try:
        return _to_response(service.publish_product(product_id))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(req: CreateCategoryRequest, service: CategoryService = Depends(get_category_service)):
    try:
        category = service.create_category(req.name, req.parent_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return CategoryResponse(id=category.id, name=category.name, slug=category.slug, parent_id=category.parent_id)


@router.get("/categories/tree")
def get_category_tree(root_id: str | None = None, service: CategoryService = Depends(get_category_service)):
    return service.get_tree(root_id)


@router.get("/search", response_model=list[SearchResultResponse])
def search_products(
    q: str = Query(..., min_length=1),
    category_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    service: ProductSearchService = Depends(get_search_service),
):
    return service.search(q, category_id=category_id, page=page, page_size=page_size)
