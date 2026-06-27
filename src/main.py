import os
import hmac
import hashlib
from fastapi import FastAPI, Request, Response

app = FastAPI()

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("META_APP_SECRET", "")


@app.get("/")
def home():
    return {"status": "live"}


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)


@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.body()

    signature = request.headers.get("X-Hub-Signature-256", "")
    if APP_SECRET and not verify_signature(body, signature):
        return Response(status_code=403)

    data = await request.json()
    print("INCOMING:", data)

    try:
        entry = data["entry"][0]["changes"][0]["value"]
        messages = entry.get("messages")
        if messages:
            msg = messages[0]
            sender = msg["from"]
            msg_type = msg["type"]
            print(f"From {sender}, type: {msg_type}")
            if msg_type == "text":
                print("Text:", msg["text"]["body"])
            # TODO: route to Jarvis perceive step
    except (KeyError, IndexError):
        pass

    return Response(status_code=200)


def verify_signature(payload: bytes, signature_header: str) -> bool:
    if not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(APP_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    received = signature_header.split("sha256=")[1]
    return hmac.compare_digest(expected, received)