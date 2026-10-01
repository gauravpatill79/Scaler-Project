from fastapi import FastAPI

from app.api.routes import router as cart_router

app = FastAPI(title="Cart Service", version="1.0.0")
app.include_router(cart_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
