"""Safe __init__.py export management."""
from __future__ import annotations
import ast

class InitFileMerger:
    """Merge exports without deleting existing imports."""
    def merge(self, existing: str, additions: list[str]) -> str:
        """Append unique export lines while preserving existing content."""
        lines = existing.splitlines() if existing else []
        for addition in additions:
            if addition not in lines: lines.append(addition)
        return '\n'.join(lines) + ('\n' if lines else '')
    def exports(self, source: str) -> list[str]:
        """Extract imported names from an initializer."""
        tree = ast.parse(source); names = []
        for node in tree.body:
            if isinstance(node, ast.ImportFrom): names.extend(a.asname or a.name for a in node.names)
        return names
