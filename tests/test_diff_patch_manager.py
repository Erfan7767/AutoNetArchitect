"""Tests for diff_patch_manager."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))

def test_diff_patch_manager_module_imports() -> None:
    """Ensure the module is importable."""
    __import__('execution_protocol.diff_patch_manager')
