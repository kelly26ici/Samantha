import json

from fastapi import Response

from src.messages.validator import verify_signature
from src.messages.parser import parse_incoming
from src.messages.router import dispatch


async def process_webhook_event(body: bytes, signature_header: str) -> Response:
    """Full pipeline for one POST /webhook call: verify -> parse -> dispatch.

    Always returns 200 once the signature check passes, even if a handler
    throws — returning non-200 makes Meta retry-deliver the same message,
    which just re-triggers the same failure (or double-sends once it's fixed).
    """
    if not verify_signature(body, signature_header):
        print("WARNING: signature verification failed")
        return Response(status_code=403)

    data = json.loads(body)

    message = parse_incoming(data)
    if message is None:
        return Response(status_code=200)  # status update, not a message

    try:
        await dispatch(message)
    except Exception as e:
        print(f"Error handling message from {message.sender}: {e}")

    return Response(status_code=200)
