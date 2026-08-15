from pathlib import Path
import tempfile

from secrets.vault_backend import LocalEncryptedVaultBackend, VaultIntegrityError, VaultLockedError


def test_local_vault_encrypts_values_and_supports_lock_unlock():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "vault.json"
        vault = LocalEncryptedVaultBackend(path)
        vault.initialize("correct horse battery staple")
        vault.put("device-password", "super-secret-value")
        raw = path.read_text(encoding="utf-8")
        assert "super-secret-value" not in raw
        assert vault.get("device-password") == "super-secret-value"
        vault.lock()
        try:
            vault.get("device-password")
        except VaultLockedError:
            pass
        else:
            raise AssertionError("locked vault must not return values")
        vault.unlock("correct horse battery staple")
        assert vault.get("device-password") == "super-secret-value"


def test_vault_rejects_wrong_master_password():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "vault.json"
        vault = LocalEncryptedVaultBackend(path)
        vault.initialize("correct horse battery staple")
        vault.lock()
        try:
            vault.unlock("wrong password with enough length")
        except VaultIntegrityError:
            return
        raise AssertionError("wrong master password must fail authentication")
