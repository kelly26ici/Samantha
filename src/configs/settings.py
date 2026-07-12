# src/comfigs/settings.py

import os 
from dotenv import load_dotenv

#======================================================
#                      BODY
#======================================================


load_dotenv()


#======================================================
#                      LLMS
#======================================================


GROQ_API_KEY=os.getenv("GROQ_API_KEY")

GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")


#======================================================
#                    WHATSAPP 
#======================================================


META_VERIFY_TOKEN=os.getenv("META_VERIFY_TOKEN", "")

META_APP_SECRET=os.getenv("META_APP_SECRET", "")

META_ACCESS_TOKEN=os.getenv("META_ACCESS_TOKEN", "")

META_PHONE_NUMBER_ID=os.getenv("META_PHONE_NUMBER_ID", "")

META_GRAPH_API_VERSION=os.getenv("META_GRAPH_API_VERSION", "v23.0")

META_GRAPH_BASE_URL=os.getenv("META_GRAPH_BASE_URL", "https://graph.facebook.com")

MAX_HISTORY = int(os.getenv("MAX_HISTORY", "10"))


#======================================================
#                     QDRANT                          #
#======================================================


QDRANT_API_KEY = os.getenv("SAMANTHA_API_KEY")

QDRANT_URL = "https://a5a1a881-af3a-425a-9066-bbb0cf7bcc7d.eu-west-1-0.aws.cloud.qdrant.io"


#======================================================
#                     MPESA
#======================================================


CONSUMER_SECRET=os.getenv("CONSUMER_SECRET")

CONSUMER_KEY=os.getenv("CONSUMER_KEY")

PASSKEY=os.getenv("PASSKEY")


#======================================================
#                     TOOLS
#======================================================


#TAVILY
