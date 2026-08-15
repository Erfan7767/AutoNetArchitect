from pathlib import Path
import tempfile

from secrets.secret_manager import SecretManager
from secrets.vault_backend import LocalEncryptedVaultBackend


def build_manager(directory: str) -> SecretManager:
    backend = LocalEncryptedVaultBackend(Path(directory) / "vault.json")
    manager = SecretManager(backend, Path(directory) / "metadata.json")
    manager.initialize("correct horse battery staple")
    return manager


def test_secret_manager_separates_metadata_and_value():
    with tempfile.TemporaryDirectory() as directory:
        manager = build_manager(directory)
        metadata = manager.put("radius-key", "raw-secret-value", "RADIUS", "network-team", tags=("identity",))
        assert metadata.secret_id == "radius-key"
        assert manager.reference("radius-key") == "secret://radius-key"
        assert manager.resolve("secret://radius-key") == "raw-secret-value"
        raw_metadata = (Path(directory) / "metadata.json").read_text(encoding="utf-8")
        assert "raw-secret-value" not in raw_metadata
        assert "radius-key" in raw_metadata


def test_secret_manager_rotation_increments_version_and_delete_removes_metadata():
    with tempfile.TemporaryDirectory() as directory:
        manager = build_manager(directory)
        first = manager.put("api-token", "first-value", "API", "automation", rotation_interval_days=30)
        second = manager.rotate("api-token", "second-value")
        assert second.version == first.version + 1
        assert manager.resolve("secret://api-token") == "second-value"
        manager.delete("api-token")
        assert manager.list_metadata() == ()
