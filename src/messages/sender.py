from src.clients.httpx_client import client
from src.configs.settings import (
    META_ACCESS_TOKEN,
    META_PHONE_NUMBER_ID,
    META_GRAPH_API_VERSION,
    META_GRAPH_BASE_URL,
)


async def send_whatsapp_message(to: str, text: str) -> None:
    url = f"{META_GRAPH_BASE_URL}/{META_GRAPH_API_VERSION}/{META_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    resp = await client.post(url, headers=headers, json=payload)
    print("Send status:", resp.status_code, resp.text)
    