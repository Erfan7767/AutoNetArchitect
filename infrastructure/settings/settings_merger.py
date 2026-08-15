"""Settings merge policy."""
class SettingsMerger:
    """Merge layered mappings."""
    def merge(self, *layers: dict[str, object]) -> dict[str, object]:
        """Merge layers from low to high precedence."""
        result: dict[str, object] = {}
        for layer in layers: result.update(layer)
        return result
