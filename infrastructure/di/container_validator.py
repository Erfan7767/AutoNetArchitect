"""Container validation facade."""
from .container import Container
class ContainerValidator:
    """Validate registrations and return a report."""
    def validate(self, container: Container) -> dict[str, list[str]]: """Validate a container."""; return container.validate()
