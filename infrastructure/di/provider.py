"""Provider implementations used by the dependency-injection container."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

from .scope import Scope

T = TypeVar("T")


def _missing_factory() -> Any:
    """Reject construction of a factory provider without an explicit factory."""
    raise TypeError("FactoryProvider.factory must be supplied explicitly")


def _default_condition() -> bool:
    """Provide a deterministic false condition until a caller supplies one."""
    return False


@dataclass
class Provider(Generic[T]):
    """Base provider metadata and explicit concrete-provider contract."""

    provides: type[T] | object
    scope: Scope = Scope.TRANSIENT
    dependencies: list[object] = field(default_factory=list)
    name: str | None = None
    tags: list[str] = field(default_factory=list)

    def get(self, resolver: Callable[[object], Any]) -> T:
        """Produce a value through a concrete provider implementation."""
        provider_name = self.name or self.__class__.__name__
        raise TypeError(f"provider {provider_name} requires a concrete get implementation")


@dataclass
class ValueProvider(Provider[T]):
    """Provider for a constant value."""

    value: T = None  # type: ignore[assignment]

    def get(self, resolver: Callable[[object], Any]) -> T:
        """Return the configured value."""
        return self.value


@dataclass
class FactoryProvider(Provider[T]):
    """Provider backed by an explicitly supplied factory callable."""

    factory: Callable[..., T] = _missing_factory  # type: ignore[assignment]

    def get(self, resolver: Callable[[object], Any]) -> T:
        """Resolve dependencies and call the factory."""
        return self.factory(*(resolver(dep) for dep in self.dependencies))


@dataclass
class ServiceProvider(Provider[T]):
    """Provider that constructs a service class."""

    implementation: type[T] | None = None

    def get(self, resolver: Callable[[object], Any]) -> T:
        """Construct the implementation with resolved dependencies."""
        if self.implementation is None:
            raise ValueError("implementation is required")
        return self.implementation(*(resolver(dep) for dep in self.dependencies))


@dataclass
class AliasProvider(Provider[T]):
    """Provider that aliases another registration key."""

    target: object = None

    def get(self, resolver: Callable[[object], Any]) -> T:
        """Resolve the target registration."""
        return resolver(self.target)


@dataclass
class ConditionalProvider(Provider[T]):
    """Choose one provider according to a supplied predicate."""

    condition: Callable[[], bool] = _default_condition
    when_true: Provider[T] | None = None
    when_false: Provider[T] | None = None

    def get(self, resolver: Callable[[object], Any]) -> T:
        """Resolve the selected branch."""
        selected = self.when_true if self.condition() else self.when_false
        if selected is None:
            raise ValueError("conditional branch is missing")
        return selected.get(resolver)
