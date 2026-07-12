# src/services/llm.py 

from google import genai

from src.configs.prompts import system_prompt
from src.configs.settings import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)


async def ask_gemini(history: list[dict]):
    interaction = await client.aio.interactions.create(
        model="gemini-3.5-flash",
        store=False,
        system_instruction=system_prompt,
        input=history,
    )

    return interaction