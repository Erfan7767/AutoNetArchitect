"""Optional dependency loading with graceful degradation."""
import importlib
from typing import Any
def optional_import(module_name: str) -> Any | None:
    """Import a module or return None when it is unavailable."""
    try: return importlib.import_module(module_name)
    except ImportError: return None
def require_feature(module_name: str, fallback: Any) -> Any:
    """Return an optional module or a safe fallback implementation."""
    return optional_import(module_name) or fallback
