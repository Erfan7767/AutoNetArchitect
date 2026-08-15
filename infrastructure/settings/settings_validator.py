"""Settings validation."""
from .settings_models import Settings
class SettingsValidator:
    """Validate settings models."""
    def validate(self, settings: Settings) -> bool:
        """Return whether settings are valid."""
        return settings.environment != ""
