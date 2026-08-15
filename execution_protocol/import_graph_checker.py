"""Static import graph checks using Python's AST."""
from __future__ import annotations
import ast
from pathlib import Path

class ImportGraphChecker:
    """Build import edges and report structural defects."""
    def build_graph(self, files: list[str]) -> dict[str, set[str]]:
        """Return file-to-file import edges for relative/local imports."""
        names = {Path(f).stem: f for f in files}; graph = {f: set() for f in files}
        for file in files:
            try: tree = ast.parse(Path(file).read_text(encoding='utf-8'))
            except (OSError, SyntaxError): continue
            for node in ast.walk(tree):
                name = node.module.split('.')[-1] if isinstance(node, ast.ImportFrom) and node.module else (node.names[0].name.split('.')[0] if isinstance(node, ast.Import) else '')
                if name in names and names[name] != file: graph[file].add(names[name])
        return graph

    def cycles(self, graph: dict[str, set[str]]) -> list[list[str]]:
        """Return detected directed cycles."""
        result: list[list[str]] = []; visiting: list[str] = []
        def visit(node: str) -> None:
            if node in visiting: result.append(visiting[visiting.index(node):] + [node]); return
            if node in done: return
            visiting.append(node)
            for child in graph.get(node, set()): visit(child)
            visiting.pop(); done.add(node)
        done: set[str] = set()
        for node in graph: visit(node)
        return result

    def report(self, graph: dict[str, set[str]]) -> dict[str, object]:
        """Report cycles, orphaned nodes, and missing edge targets."""
        incoming = {n: 0 for n in graph}
        for edges in graph.values():
            for edge in edges:
                if edge in incoming: incoming[edge] += 1
        return {'cycles': self.cycles(graph), 'orphaned_files': [n for n, count in incoming.items() if count == 0 and not graph[n]], 'missing_dependencies': [e for edges in graph.values() for e in edges if e not in graph]}
