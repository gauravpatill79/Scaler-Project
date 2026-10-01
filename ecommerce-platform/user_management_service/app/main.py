from fastapi import FastAPI

from app.api.routes import router as user_router

app = FastAPI(title="User Management Service", version="1.0.0")
app.include_router(user_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
