from src.configs.settings import MAX_HISTORY

_conversations: dict[str, list[dict]] = {}


def get_history(sender: str) -> list[dict]:
    """Returns this customer's history list."""
    return _conversations.setdefault(sender, [])


def append_user_message(sender: str, content: str) -> None:
    """Adds a user message."""

    history = get_history(sender)

    history.append(
        {
            "type": "user_input",
            "content": [
                {
                    "type": "text",
                    "text": content,
                }
            ],
        }
    )

    if len(history) > MAX_HISTORY:
        del history[:-MAX_HISTORY]


def append_interaction_steps(sender: str, steps) -> None:
    """
    Adds Gemini's returned interaction steps exactly as received.
    Do not modify them.
    """

    history = get_history(sender)

    for step in steps:
        history.append(step.model_dump())

    if len(history) > MAX_HISTORY:
        del history[:-MAX_HISTORY]