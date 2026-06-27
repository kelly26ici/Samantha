import os
import hmac
import hashlib
import httpx
from fastapi import FastAPI, Request, Response
from src.services.groq_service import ask_groq  # adjust path to wherever your snippet lives

app = FastAPI()

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("META_APP_SECRET", "")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID", "")
GRAPH_VERSION = os.getenv("META_GRAPH_API_VERSION", "v23.0")
GRAPH_BASE = os.getenv("META_GRAPH_BASE_URL", "https://graph.facebook.com")


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
        print("WARNING: signature verification failed")
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
                user_text = msg["text"]["body"]
                print("Text body:", user_text)

                reply_text = ask_groq(user_text)
                print("Groq reply:", reply_text)

                await send_whatsapp_message(sender, reply_text)

    except (KeyError, IndexError) as e:
        print("Parse error (probably a status update, not a message):", e)

    return Response(status_code=200)


async def send_whatsapp_message(to: str, text: str):
    url = f"{GRAPH_BASE}/{GRAPH_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        print("Send status:", resp.status_code, resp.text)


def verify_signature(payload: bytes, signature_header: str) -> bool:
    if not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(APP_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    received = signature_header.split("sha256=")[1]
    return hmac.compare_digest(expected, received)