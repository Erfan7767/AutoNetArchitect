"""Schema version validation helpers."""
from .constants import SCHEMA_VERSION
from .exceptions import ValidationError
def validate_schema_version(value: str) -> str:
    """Validate and return the supported schema version."""
    if value != SCHEMA_VERSION: raise ValidationError(f"unsupported schema version: {value}")
    return value
