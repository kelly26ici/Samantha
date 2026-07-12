from fastapi import FastAPI

from src.routes.webhook import router as webhook_router

app = FastAPI(
    title="Samantha API",
    version="1.0.0",
)

app.include_router(webhook_router)