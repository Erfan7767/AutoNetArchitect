"""Fluent container builder."""
from __future__ import annotations
from .container import Container
class ContainerBuilder:
    """Collect modules and build a validated container."""
    def __init__(self) -> None: self.container = Container(); self.modules = []
    def add_module(self, module: object) -> ContainerBuilder: self.modules.append(module); return self
    def with_settings(self, settings: object) -> ContainerBuilder: self.container.register(type(settings), settings); return self
    def validate(self) -> ContainerBuilder:
        """Validate registrations before build."""
        result = self.container.validate()
        if result['missing_dependencies']: raise ValueError(str(result))
        return self
    def build(self) -> Container: """Register modules and return the container."""; [m.register(self.container) for m in self.modules]; return self.container
