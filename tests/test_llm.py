import asyncio

from src.services.llm import ask_gemini

exit_choices = ["exit", "quit"]


async def main():
    while True:
        user_input = input("Kelly: ")
        print()

        if user_input.strip().lower() in exit_choices:
            print("Goodbye")
            break

        if not user_input.strip():
            continue

        response = await ask_gemini(user_input)
        print(f"Samantha: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())