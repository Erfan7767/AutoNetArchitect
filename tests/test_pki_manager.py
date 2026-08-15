from pathlib import Path
import tempfile

from pki.cert_inventory import CertInventory
from pki.pki_manager import PKIManager
from secrets.secret_manager import SecretManager
from secrets.vault_backend import LocalEncryptedVaultBackend


def build_pki(directory: str) -> tuple[PKIManager, CertInventory, SecretManager]:
    root = Path(directory)
    manager = SecretManager(LocalEncryptedVaultBackend(root / "vault.json"), root / "secret_metadata.json")
    manager.initialize("correct horse battery staple")
    inventory = CertInventory(root / "cert_inventory.json")
    return PKIManager(manager, inventory, root / "certificates"), inventory, manager


def test_pki_manager_generates_inventory_and_revokes_certificate():
    with tempfile.TemporaryDirectory() as directory:
        pki, inventory, manager = build_pki(directory)
        record = pki.generate_self_signed("edge-1", "edge.example", ["edge.example", "192.0.2.1"], validity_days=30)
        assert Path(record.certificate_path).exists()
        assert record.private_key_ref.startswith("secret://")
        assert manager.resolve(record.private_key_ref).startswith("-----BEGIN PRIVATE KEY-----")
        revoked = pki.revoke(record.cert_id, "planned replacement")
        assert revoked.status == "revoked"
        crl_path = pki.generate_crl(Path(directory) / "revocations.crl.pem", record.cert_id)
        assert crl_path.exists()
        assert b"BEGIN X509 CRL" in crl_path.read_bytes()
