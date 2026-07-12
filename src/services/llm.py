from groq import Groq
from src.configs.settings import GROQ_API_KEY
from src.configs.prompts import system_prompt

client = Groq(api_key=GROQ_API_KEY)


async def ask_groq(history: list[dict]) -> str:
    """
    history: this customer's own conversation, as a list of
    {"role": "user"/"assistant", "content": ...} dicts (no system message).
    Returns the assistant's reply text. Does NOT mutate history itself —
    caller is responsible for appending the reply.
    """
    messages = [
      {
        "role": "system",
        "content": system_prompt
      }
    ] + history

    response = await client.chat.completions.create(
        model="gpt-oss-120b",
        messages=messages,
    )

    return response.choices[0].message.content