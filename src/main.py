from fastapi import FastAPI
from src.routes.webhook import router as webhook_router

app = FastAPI(title="WhatsApp AI Agent")

app.include_router(webhook_router)


@app.get("/")
def root():
    return {"status": "running"}