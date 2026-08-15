"""Tests for context_handoff_manager."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))

def test_context_handoff_manager_module_imports() -> None:
    """Ensure the module is importable."""
    __import__('execution_protocol.context_handoff_manager')
