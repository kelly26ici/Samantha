from groq import Groq
from src.configs.settings import GROQ_API_KEY
from src.configs.prompts import system_prompt

client = Groq(api_key=GROQ_API_KEY)


def ask_groq(history: list[dict]) -> str:
    """
    history: this customer's own conversation, as a list of
    {"role": "user"/"assistant", "content": ...} dicts (no system message).
    Returns the assistant's reply text. Does NOT mutate history itself —
    caller is responsible for appending the reply.
    """
    messages = [{"role": "system", "content": system_prompt}] + history

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
    )

    return response.choices[0].message.content