"""Container diagnostic reporting."""
from .container import Container
class ContainerReporter:
    """Render container diagnostics."""
    def render(self, container: Container) -> str: """Return a human-readable report."""; return repr(container.validate())
