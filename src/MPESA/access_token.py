import asyncio
import base64
from src.configs.settings import CONSUMER_KEY, CONSUMER_SECRET
from src.clients.httpx import httpx


async def generate_access_token() -> str:
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    encoded_credentials = base64.b64encode(
        f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()
    ).decode()
    headers = {"Authorization": f"Basic {encoded_credentials}"}

    try:
        response = await httpx.get(url, headers=headers)
        response.raise_for_status()
        body = response.json()
    except httpx.HTTPStatusError as e:
        raise Exception(f"M-Pesa auth request failed: {e.response.status_code} {e.response.text}") from e
    except httpx.RequestError as e:
        raise Exception(f"M-Pesa auth request error: {e}") from e

    access_token = body.get("access_token")
    if not access_token:
        raise Exception(f"No access_token in M-Pesa response: {body}")

    return access_token