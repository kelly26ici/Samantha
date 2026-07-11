import os
import hmac
import hashlib
import httpx
from fastapi import FastAPI, Request, Response
from src.services.llm import ask_groq

app = FastAPI()

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("META_APP_SECRET", "")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID", "")
GRAPH_VERSION = os.getenv("META_GRAPH_API_VERSION", "v23.0")
GRAPH_BASE = os.getenv("META_GRAPH_BASE_URL", "https://graph.facebook.com")

# Per-customer conversation history: { phone_number: [ {role, content}, ... ] }
# NOTE: this resets on every Render restart/redeploy. Fine for testing;
# swap for Redis (you already use it in Samantha) for anything persistent.
conversations: dict[str, list[dict]] = {}
MAX_HISTORY = 10  # keep last N messages per customer to control token usage


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
            sender = msg["from"]  # this is the customer's phone number — our key
            msg_type = msg["type"]
            print(f"From {sender}, type: {msg_type}")

            if msg_type == "text":
                user_text = msg["text"]["body"]
                print("Text body:", user_text)

                reply_text = await get_reply_for_customer(sender, user_text)
                print("Reply:", reply_text)

                await send_whatsapp_message(sender, reply_text)

    except (KeyError, IndexError) as e:
        print("Parse error (probably a status update, not a message):", e)

    return Response(status_code=200)


async def get_reply_for_customer(sender: str, user_text: str) -> str:
    """Builds a reply using THIS customer's own conversation history only."""
    history = conversations.setdefault(sender, [])

    history.append({"role": "user", "content": user_text})

    reply_text = ask_groq(history)  # pass full per-customer history, not just the raw string

    history.append({"role": "assistant", "content": reply_text})

    # trim so it doesn't grow unbounded
    if len(history) > MAX_HISTORY:
        conversations[sender] = history[-MAX_HISTORY:]

    return reply_text


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