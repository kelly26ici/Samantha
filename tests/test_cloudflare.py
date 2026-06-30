import os
import requests
from dotenv import load_dotenv

load_dotenv()

def verify_cloudflare_setup():
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    
    if not account_id or not api_token:
        print("❌ Setup Failure: Missing environment variables! Check Step 4.")
        return

    # Targeting the elite 0.6B Qwen3 embedding node
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/qwen/qwen3-embedding-0.6b"
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {"text": ["Testing my new Cloudflare AI agent memory pipeline."]}
    
    print("📡 Sending test payload to Cloudflare edge network...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        vector = data["result"]["data"][0]
        print("✅ Connection Successful!")
        print(f"Generated Vector Length: {len(vector)} dimensions")
        print(f"Sample Coordinates snippet: {vector[:3]}")
    else:
        print(f"❌ Connection Failed with status code: {response.status_code}")
        print(f"Error logs: {response.text}")

if __name__ == "__main__":
    verify_cloudflare_setup()
    