"""Settings reporting."""
class SettingsReporter:
    """Render safe settings reports."""
    def report(self, values: dict[str, object]) -> dict[str, object]:
        """Return settings for diagnostics."""
        return {"keys": sorted(values)}
