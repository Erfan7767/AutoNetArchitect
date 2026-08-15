"""Tests for output_size_predictor."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))

def test_output_size_predictor_module_imports() -> None:
    """Ensure the module is importable."""
    __import__('execution_protocol.output_size_predictor')
