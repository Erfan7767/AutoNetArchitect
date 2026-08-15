"""Tests for execution_state."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))

def test_execution_state_module_imports() -> None:
    """Ensure the module is importable."""
    __import__('execution_protocol.execution_state')
