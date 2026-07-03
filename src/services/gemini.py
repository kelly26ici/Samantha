from google import genai
from src.configs.settings import GEMINI_API_KEY
from src.configs.constants import GEMINI_MODEL
client=genai.Client(api_key=GEMINI_API_KEY)

def ask_gemini(user_input: str):
  interactions=client.interactions.create(
    model=GEMINI_MODEL,
    input=user_input
    )
