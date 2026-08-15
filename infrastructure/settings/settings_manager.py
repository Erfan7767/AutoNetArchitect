"""Central settings manager."""
from .settings_models import Settings
class SettingsManager:
    """Load and replace validated settings."""
    def __init__(self, settings: Settings | None = None) -> None: self.settings = settings or Settings()
    def get(self, key: str, default: object = None) -> object: """Read a setting."""; return self.settings.values.get(key, default)
    def update(self, values: dict[str, object]) -> Settings: """Merge settings values."""; self.settings = Settings(environment=self.settings.environment, values={**self.settings.values, **values}); return self.settings
