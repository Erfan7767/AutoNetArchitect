"""Environment value resolver."""
import os
class EnvironmentResolver:
    """Resolve values from process environment."""
    def get(self, key: str, default: str | None = None) -> str | None:
        """Get an environment value."""
        return os.getenv(key, default)
