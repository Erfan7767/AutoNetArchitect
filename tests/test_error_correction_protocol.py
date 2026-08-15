"""Tests for error_correction_protocol."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))

def test_error_correction_protocol_module_imports() -> None:
    """Ensure the module is importable."""
    __import__('execution_protocol.error_correction_protocol')
