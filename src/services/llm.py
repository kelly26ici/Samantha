from groq import Groq
from src.configs.settings import GROQ_API_KEY
from src.configs.prompts import system_prompt

client=Groq(api_key=GROQ_API_KEY)

messages=[
    {
      "role": "system",
      "content": system_prompt
    },
  ]

def groq_llm(user_input: str):
  
  response=client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=messages)
    
  reply= response.choices[0].message.content
  
  messages.append(
    {
      "role": "assistant",
      "content": reply
    }
    )
  
  return reply
  
print(messages)