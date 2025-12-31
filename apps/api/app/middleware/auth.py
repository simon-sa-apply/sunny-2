"""API Key authentication middleware."""

import secrets

from fastapi import Request
from fastapi.security import APIKeyHeader

# API Key header configuration
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(
    request: Request,
    api_key: str | None = None,
) -> str | None:
    """
    Validate API key from request header.

    For MVP, we use a simple validation. In production,
    this would check against the database.
    """
    if api_key is None:
        api_key = request.headers.get("X-API-Key")

    if not api_key:
        # Anonymous requests are allowed but rate-limited more strictly
        return None

    # TODO: In production, check against database
    # For MVP, accept any non-empty key and log it
    return api_key


def get_api_key_or_ip(request: Request) -> str:
    """
    Get identifier for rate limiting.

    Uses API key if present, otherwise falls back to IP address.
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key}"

    # Fallback to IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"

    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


def generate_api_key() -> str:
    """Generate a new secure API key."""
    return secrets.token_urlsafe(32)

