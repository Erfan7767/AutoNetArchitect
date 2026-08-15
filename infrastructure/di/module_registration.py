"""Registration protocol and registry for dependency-injection modules."""

from __future__ import annotations

from typing import Protocol

from .container import Container


class IModule(Protocol):
    """Protocol implemented by registration modules."""

    def register(self, container: Container) -> None:
        """Register module providers into the supplied container."""
        raise TypeError("IModule.register requires a concrete module implementation")


class ModuleRegistry:
    """Register a collection of modules in insertion order."""

    def __init__(self) -> None:
        """Create an empty module registry."""
        self.modules: list[IModule] = []

    def add(self, module: IModule) -> None:
        """Append one module to the registration sequence."""
        self.modules.append(module)

    def register_all(self, container: Container) -> None:
        """Register every module in insertion order."""
        for module in self.modules:
            module.register(container)
