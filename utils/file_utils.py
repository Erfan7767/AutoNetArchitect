"""File operations with safe path handling."""
from pathlib import Path
def read_text(path: str | Path) -> str:
    """Read UTF-8 text from a file."""
    return Path(path).read_text(encoding="utf-8")
def write_text(path: str | Path, content: str) -> Path:
    """Create parent directories and write UTF-8 text."""
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True); target.write_text(content, encoding="utf-8"); return target
