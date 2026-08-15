"""Feature flag access."""
class FeatureFlags:
    """Read boolean feature flags."""
    def __init__(self, flags: dict[str, bool] | None = None) -> None: self.flags = flags or {}
    def enabled(self, name: str) -> bool:
        """Return a flag state."""
        return self.flags.get(name, False)
