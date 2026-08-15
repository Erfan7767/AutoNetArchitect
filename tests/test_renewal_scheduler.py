from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

from pki.cert_inventory import CertInventory
from pki.pki_manager import PKIManager
from pki.renewal_scheduler import RenewalScheduler
from secrets.secret_manager import SecretManager
from secrets.vault_backend import LocalEncryptedVaultBackend


def test_scheduler_plans_and_executes_approved_renewal():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        secrets = SecretManager(LocalEncryptedVaultBackend(root / "vault.json"), root / "metadata.json")
        secrets.initialize("correct horse battery staple")
        inventory = CertInventory(root / "inventory.json")
        pki = PKIManager(secrets, inventory, root / "certs")
        record = pki.generate_self_signed("edge", "edge.example", ["edge.example"], validity_days=1)
        scheduler = RenewalScheduler(inventory, pki)
        tasks = scheduler.plan(within_days=30)
        assert tasks and tasks[0].cert_id == record.cert_id
        renewed = scheduler.execute(tasks, lambda task: True, validity_days=30)
        assert len(renewed) == 1
        assert inventory.status(record.cert_id) in {"active", "due_soon"}
