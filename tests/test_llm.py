from src.services.llm import ask_groq

exit_choices=["exit", "quit"]

while True:
  user_input=input("Kelly: ")
  print("\n")
  if user_input.strip().lower() in exit_choices:
    print("Goodbye")
    break
  if not user_input.strip():
    continue
      
  response=ask_groq(user_input)
  print(f"Samantha: {response}\n\n")