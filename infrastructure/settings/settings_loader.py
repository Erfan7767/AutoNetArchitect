"""Settings loading."""
from .settings_models import Settings
class SettingsLoader:
    """Load settings from a mapping."""
    def load(self, values: dict[str, object]) -> Settings:
        """Validate mapping as settings."""
        return Settings.model_validate(values)
