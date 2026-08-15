"""Tests for init_file_merger."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))

def test_init_file_merger_module_imports() -> None:
    """Ensure the module is importable."""
    __import__('execution_protocol.init_file_merger')
