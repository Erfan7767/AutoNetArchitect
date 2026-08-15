"""Dependency health checks."""
class DependencyHealth:
    """Check dependency objects."""
    def check(self, dependency: object) -> bool: """Return whether a dependency is available."""; return dependency is not None
