"""Dependency graph diagnostics."""
from __future__ import annotations
class DependencyGraph:
    """Build a graph from provider metadata."""
    def __init__(self, providers: dict[object, object]) -> None: self.providers = providers
    def validate(self) -> dict[str, list[str]]:
        """Return missing dependency diagnostics."""
        missing = []
        for key, provider in self.providers.items():
            for dep in getattr(provider, 'dependencies', []):
                if dep not in self.providers: missing.append(f'{key!r}->{dep!r}')
        return {'missing': missing, 'cycles': []}
    def to_dot(self) -> str:
        """Export the graph as Graphviz DOT."""
        lines = ['digraph dependencies {']
        for key, provider in self.providers.items():
            for dep in getattr(provider, 'dependencies', []): lines.append(f'  "{key}" -> "{dep}";')
        return '\n'.join(lines + ['}'])
