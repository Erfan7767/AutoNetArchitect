"""Arabic text normalization helpers."""
import re
def normalize_arabic(value: str) -> str:
    """Normalize whitespace and common Arabic presentation variants."""
    normalized = value.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا"); return re.sub(r"\s+", " ", normalized).strip()
