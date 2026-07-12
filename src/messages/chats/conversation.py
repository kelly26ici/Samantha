from src.configs.settings import MAX_HISTORY

# Per-customer conversation history: { phone_number: [interaction steps...] }
# NOTE: resets on every Render restart/redeploy. Fine for testing; swap for
# Redis for anything persistent.
_conversations: dict[str, list[dict]] = {}


def get_history(sender: str) -> list[dict]:
    """Returns this customer's history list (creating it on first contact)."""
    return _conversations.setdefault(sender, [])


def append_message(sender: str, role: str, content: str) -> None:
    """
    Keeps the original function interface.
    Stores messages in Gemini Interactions API format internally.
    """

    history = get_history(sender)

    history.append(
        {
            "type": "user_input" if role == "user" else "model_output",
            "content": [
                {
                    "type": "text",
                    "text": content,
                }
            ],
        }
    )

    if len(history) > MAX_HISTORY:
        _conversations[sender] = history[-MAX_HISTORY:]


def append_interaction_steps(sender: str, steps) -> None:
    """
    Stores Gemini returned interaction steps without changing them.
    Needed later for tool calling/function calling support.
    """

    history = get_history(sender)

    history.extend(
        step.model_dump() if hasattr(step, "model_dump") else step
        for step in steps
    )

    if len(history) > MAX_HISTORY:
        _conversations[sender] = history[-MAX_HISTORY:]