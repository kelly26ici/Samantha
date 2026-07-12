from google import genai

from src.configs.settings import GEMINI_API_KEY
from src.configs.prompts import system_prompt

client = genai.Client(api_key=GEMINI_API_KEY)


async def ask_gemini(history: list[dict]) -> str:
    interaction = await client.aio.interactions.create(
        model="gemini-3.5-flash",
        input=[
            {
                "role": "system",
                "content": system_prompt,
            },
            *history,
        ],
    )

    return interaction.output_text