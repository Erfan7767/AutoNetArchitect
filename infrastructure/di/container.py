"""Thread-safe inversion-of-control container."""
from __future__ import annotations
from typing import Any
from threading import RLock
from .provider import Provider, ServiceProvider
from .scope import Scope, ScopeManager

class Container:
    """Register and resolve services with cycle detection."""
    def __init__(self) -> None:
        self._providers: dict[tuple[object, str | None], Provider[Any]] = {}
        self._instances: dict[tuple[object, str | None], Any] = {}
        self._lock = RLock(); self.scopes = ScopeManager()
    def register(self, interface: object, implementation: type[Any] | Provider[Any], scope: Scope = Scope.TRANSIENT, name: str | None = None, dependencies: list[object] | None = None, tags: list[str] | None = None) -> Container:
        """Register a class or provider and reject dependency cycles immediately."""
        provider = implementation if isinstance(implementation, Provider) else ServiceProvider(interface, scope, dependencies or [], name, tags or [], implementation)
        key = (interface, name)
        with self._lock:
            self._providers[key] = provider
            self._validate_cycles()
        return self
    def resolve(self, interface: object, name: str | None = None) -> Any:
        """Resolve a registration using its declared lifetime."""
        return self._resolve((interface, name), [])
    def _resolve(self, key: tuple[object, str | None], stack: list[tuple[object, str | None]]) -> Any:
        if key in stack: raise RuntimeError('circular dependency: ' + repr(key))
        provider = self._providers.get(key)
        if provider is None: raise KeyError(f'no provider for {key!r}')
        store = self._instances if provider.scope == Scope.SINGLETON else (self.scopes.current() if provider.scope == Scope.SCOPED else None)
        if store is not None and key in store: return store[key]
        value = provider.get(lambda dep: self._resolve((dep, None), stack + [key]))
        if store is not None: store[key] = value
        return value
    def _validate_cycles(self) -> None:
        """Validate the provider graph with depth-first traversal."""
        def visit(key: tuple[object, str | None], path: set[tuple[object, str | None]]) -> None:
            if key in path: raise ValueError('circular dependency detected')
            provider = self._providers.get(key)
            if provider is None: return
            for dep in provider.dependencies: visit((dep, None), path | {key})
        for key in self._providers: visit(key, set())
    def validate(self) -> dict[str, list[str]]:
        """Return missing dependency and registration diagnostics."""
        missing = [repr(dep) for p in self._providers.values() for dep in p.dependencies if (dep, None) not in self._providers]
        return {'missing_dependencies': missing, 'registrations': [repr(k) for k in self._providers]}
