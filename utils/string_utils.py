"""Safe string helpers."""
import re
def slugify(value: str) -> str:
    """Create a lowercase hyphenated identifier."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
def redact_text(value: str, secret: str) -> str:
    """Replace a secret in text without logging the secret."""
    return value.replace(secret, "[REDACTED]") if secret else value
