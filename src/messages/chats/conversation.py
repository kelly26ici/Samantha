from src.configs.settings import MAX_HISTORY

# Per-customer conversation history: { phone_number: [ {role, content}, ... ] }
# NOTE: resets on every Render restart/redeploy. Fine for testing; swap for
# Redis for anything persistent.
_conversations: dict[str, list[dict]] = {}


def get_history(sender: str) -> list[dict]:
    """Returns this customer's history list (creating it on first contact)."""
    return _conversations.setdefault(sender, [])


def append_message(sender: str, role: str, content: str) -> None:
    """Adds a turn and trims to the last MAX_HISTORY messages."""
    history = get_history(sender)
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY:
        _conversations[sender] = history[-MAX_HISTORY:]
        