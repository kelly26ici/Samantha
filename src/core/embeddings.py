import os
from dotenv import load_dotenv
import requests
load_dotenv()

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/qwen/qwen3-embedding-0.6b"


def get_embeddings(text_chunks: list[str]):

    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        raise ValueError("CLOUDFLARE_ACCOUNT_ID and/or CLOUDFLARE_API_TOKEN missing in environment variables")

    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text_chunks
    }

    try:
        response = requests.post(
            CLOUDFLARE_API_URL,
            headers=headers,
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()["result"]["data"]

        print(f"Cloudflare Edge Error [{response.status_code}]: {response.text}")
        return []

    except requests.exceptions.RequestException as e:
        print(f"Network timeout/failure connecting to Cloudflare: {e}")
        return []