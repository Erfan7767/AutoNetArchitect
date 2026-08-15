"""JSON file cache backend."""
from pathlib import Path
import json
class FileBackend:
    """Persist a mapping in JSON."""
    def __init__(self, path: str) -> None: self.path = Path(path)
    def set(self, key: str, value: object) -> None: """Persist a value."""; data = json.loads(self.path.read_text()) if self.path.exists() else {}; data[key] = value; self.path.write_text(json.dumps(data))
