import os 
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY=os.getenv("GROQ_API_KEY")


QDRANT_API_KEY = os.getenv("SAMANTHA_API_KEY")

QDRANT_URL = "https://a5a1a881-af3a-425a-9066-bbb0cf7bcc7d.eu-west-1-0.aws.cloud.qdrant.io"
