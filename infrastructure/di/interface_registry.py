"""Interface and implementation registry."""
from __future__ import annotations
class InterfaceRegistry:
    """Track interfaces, named implementations, and defaults."""
    def __init__(self) -> None: self._interfaces: set[object] = set(); self._implementations: dict[object, list[tuple[type[object], str | None, bool]]] = {}
    def register_interface(self, interface: object) -> None: """Register an interface."""; self._interfaces.add(interface); self._implementations.setdefault(interface, [])
    def register_implementation(self, interface: object, implementation: type[object], name: str | None = None, default: bool = False) -> None:
        """Register an implementation against a known interface."""
        if interface not in self._interfaces: raise KeyError('interface is not registered')
        self._implementations[interface].append((implementation, name, default))
    def implementations(self, interface: object) -> list[type[object]]: """Return implementation classes."""; return [i for i, _, _ in self._implementations.get(interface, [])]
