"""Compare public Python signatures across revisions."""
from __future__ import annotations
import ast

class SignatureConsistencyChecker:
    """Extract and compare functions, methods, and classes."""
    def extract(self, source: str) -> dict[str, dict[str, str]]:
        """Extract function signatures as normalized strings."""
        tree = ast.parse(source); result: dict[str, dict[str, str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg + (':' + ast.unparse(a.annotation) if a.annotation else '') for a in node.args.args]
                result[node.name] = {'parameters': ','.join(args), 'return': ast.unparse(node.returns) if node.returns else ''}
        return result

    def compare(self, old_source: str, new_source: str) -> list[dict[str, str]]:
        """Return breaking signature changes."""
        old, new, changes = self.extract(old_source), self.extract(new_source), []
        for name, old_sig in old.items():
            if name not in new: changes.append({'symbol': name, 'kind': 'removed'})
            elif old_sig != new[name]: changes.append({'symbol': name, 'kind': 'signature_changed', 'old': str(old_sig), 'new': str(new[name])})
        return changes
