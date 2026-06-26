"""
KOVIRX — Shared utility functions.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


def sanitize_string(value: str, max_length: int = 512) -> str:
    """Sanitize and truncate a user-provided string."""
    return value.strip()[:max_length] if value else ""
