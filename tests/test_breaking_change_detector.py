"""Tests for breaking_change_detector."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))

def test_breaking_change_detector_module_imports() -> None:
    """Ensure the module is importable."""
    __import__('execution_protocol.breaking_change_detector')
