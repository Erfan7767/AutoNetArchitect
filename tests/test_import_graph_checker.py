"""Tests for import_graph_checker."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))

def test_import_graph_checker_module_imports() -> None:
    """Ensure the module is importable."""
    __import__('execution_protocol.import_graph_checker')
