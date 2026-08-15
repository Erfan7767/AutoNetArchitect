"""Tests for merge_strategy."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))

def test_merge_strategy_module_imports() -> None:
    """Ensure the module is importable."""
    __import__('execution_protocol.merge_strategy')
