"""Settings schema migrations."""
class SettingsMigration:
    """Migrate a mapping between schema versions."""
    def migrate(self, values: dict[str, object], target_version: str) -> dict[str, object]:
        """Attach the target schema version."""
        return {**values, "schema_version": target_version}
