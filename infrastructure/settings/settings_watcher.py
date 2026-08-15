"""Settings change watcher."""
class SettingsWatcher:
    """Notify callbacks on settings replacement."""
    def __init__(self) -> None: self.callbacks = []
    def subscribe(self, callback: object) -> None:
        """Subscribe a callback."""
        self.callbacks.append(callback)
