from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

from pki.cert_inventory import CertInventory, CertificateRecord


def build_record(not_after: datetime) -> CertificateRecord:
    return CertificateRecord("cert-1", "edge.example", ("edge.example",), "123", "edge.example", datetime.now(timezone.utc).isoformat(), not_after.isoformat(), "/tmp/cert.pem", "secret://pki-key-cert-1")


def test_inventory_tracks_expiry_and_revocation():
    with tempfile.TemporaryDirectory() as directory:
        inventory = CertInventory(Path(directory) / "inventory.json")
        record = inventory.register(build_record(datetime.now(timezone.utc) + timedelta(days=5)))
        assert inventory.status(record.cert_id) == "due_soon"
        assert inventory.expiring(30)
        revoked = inventory.revoke(record.cert_id, "key compromise")
        assert revoked.status == "revoked"
        assert inventory.status(record.cert_id) == "revoked"
        raw = (Path(directory) / "inventory.json").read_text(encoding="utf-8")
        assert "private_key_ref" in raw
        assert "PRIVATE KEY" not in raw
