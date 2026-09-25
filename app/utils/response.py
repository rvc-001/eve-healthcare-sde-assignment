"""
Response helper — mirrors Forehand's utils/response.ts (sendResponse function).

Forehand pattern:
    export const sendResponse = ({ success, message, data }) => ({ success, message, data })

Our Python equivalent is a typed dict builder used in all route handlers,
ensuring every API response has a consistent envelope shape:
    { "success": bool, "message": str, "data": any | None }
"""

from typing import Any


def send_response(
    *,
    success: bool,
    message: str,
    data: Any = None,
) -> dict[str, Any]:
    """
    Build a consistent API response envelope.
    Mirrors Forehand's sendResponse() utility exactly.
    """
    response: dict[str, Any] = {"success": success, "message": message}
    if data is not None:
        response["data"] = data
    return response
