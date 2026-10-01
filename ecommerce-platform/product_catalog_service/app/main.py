from fastapi import FastAPI

from app.api.routes import router as product_router

app = FastAPI(title="Product Catalog Service", version="1.0.0")
app.include_router(product_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
