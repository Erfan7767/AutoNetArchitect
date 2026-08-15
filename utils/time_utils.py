"""UTC time utilities."""
from datetime import datetime, timezone
def utc_now() -> datetime:
    """Return timezone-aware UTC time."""
    return datetime.now(timezone.utc)
def iso_now() -> str:
    """Return current UTC time in ISO-8601 format."""
    return utc_now().isoformat()
