from src.messages.parser import IncomingMessage
from src.messages.chats.text_handler import handle_text

# Explicit registry, same pattern as src/tools/registry.py — add an entry
# here as each new handler (image, audio, interactive, ...) gets built out.
MESSAGE_HANDLERS = {
    "text": handle_text,
}


async def dispatch(message: IncomingMessage) -> None:
    handler = MESSAGE_HANDLERS.get(message.msg_type)
    if handler is None:
        print(f"No handler yet for message type '{message.msg_type}' from {message.sender}")
        return
    await handler(message.sender, message.raw)
    