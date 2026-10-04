from fastapi import FastAPI

from app.api.routes import router as order_router

app = FastAPI(title="Order Management Service", version="1.0.0")
app.include_router(order_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
