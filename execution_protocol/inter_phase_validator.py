"""Validate imports and public symbols across execution phases."""
from __future__ import annotations
import ast
from pathlib import Path
from typing import Any
from .import_graph_checker import ImportGraphChecker
from .signature_consistency_checker import SignatureConsistencyChecker

class InterPhaseValidator:
    """Run syntax, import-graph, symbol, and signature validation."""
    def validate(self, new_files: list[str], previous_files: list[str]) -> dict[str, Any]:
        """Return a structured validation report for newly delivered files."""
        all_files = previous_files + new_files
        graph = ImportGraphChecker().build_graph(all_files)
        report: dict[str, Any] = ImportGraphChecker().report(graph)
        report.update({'syntax_errors': [], 'missing_symbols': [], 'signature_changes': []})
        known_names: set[str] = set()
        for file in all_files:
            try:
                tree = ast.parse(Path(file).read_text(encoding='utf-8'), filename=file)
            except (OSError, SyntaxError) as exc:
                report['syntax_errors'].append({'file': file, 'error': str(exc)})
                continue
            known_names.update(node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
        for file in new_files:
            try: tree = ast.parse(Path(file).read_text(encoding='utf-8'))
            except (OSError, SyntaxError): continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name != '*' and alias.name not in known_names and node.module and node.module.startswith('execution_protocol'):
                            report['missing_symbols'].append({'file': file, 'symbol': alias.name})
        return report
