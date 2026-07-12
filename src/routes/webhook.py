# src/routes/webhook.py 

import asyncio
from fastapi import APIRouter, Request, Response

from src.configs.settings import META_VERIFY_TOKEN
from src.messages.webhook import process_webhook_event

router = APIRouter()


@router.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == META_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)


@router.post("/webhook")
async def receive_message(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    return await process_webhook_event(body, signature)