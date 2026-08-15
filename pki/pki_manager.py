"""V1 PKI manager for certificate generation, inventory, renewal, and revocation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path
from typing import Iterable

from .cert_inventory import CertInventory, CertificateRecord
from secrets.secret_manager import SecretManager


class PKIManager:
    """Manage certificates while keeping private key material inside SecretManager."""

    def __init__(self, secret_manager: SecretManager, inventory: CertInventory, certificate_root: str | Path) -> None:
        self.secret_manager = secret_manager
        self.inventory = inventory
        self.certificate_root = Path(certificate_root)
        self.certificate_root.mkdir(parents=True, exist_ok=True)

    def generate_self_signed(self, cert_id: str, common_name: str, sans: Iterable[str], validity_days: int = 365, key_size: int = 2048, owner: str = "pki-manager", purpose: str = "network-device-certificate") -> CertificateRecord:
        """Generate a self-signed RSA certificate and store only the key reference."""
        if validity_days <= 0 or validity_days > 3650:
            raise ValueError("validity_days must be between 1 and 3650")
        if key_size < 2048:
            raise ValueError("key_size must be at least 2048")
        if not common_name:
            raise ValueError("common_name is required")
        san_values = tuple(dict.fromkeys(str(value) for value in sans if str(value)))
        if not san_values:
            san_values = (common_name,)
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        now = datetime.now(timezone.utc)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
        builder = x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=5)).not_valid_after(now + timedelta(days=validity_days))
        san_objects = []
        for value in san_values:
            try:
                san_objects.append(x509.IPAddress(ip_address(value)))
            except ValueError:
                san_objects.append(x509.DNSName(value))
        certificate = builder.add_extension(x509.SubjectAlternativeName(san_objects), critical=False).add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True).sign(key, hashes.SHA256())
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
        key_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode("utf-8")
        key_secret_id = f"pki-key-{cert_id}"
        key_ref = SecretManager.reference(key_secret_id)
        self.secret_manager.put(key_secret_id, key_pem, purpose=f"private-key:{purpose}", owner=owner, classification="highly_confidential", rotation_interval_days=validity_days, source_of_truth="pki_manager", expires_at=(now + timedelta(days=validity_days)).isoformat())
        cert_path = self.certificate_root / f"{cert_id}.crt.pem"
        cert_path.write_bytes(cert_pem)
        not_before = getattr(certificate, "not_valid_before_utc", None)
        not_after = getattr(certificate, "not_valid_after_utc", None)
        if not_before is None:
            not_before = certificate.not_valid_before.replace(tzinfo=timezone.utc)
        if not_after is None:
            not_after = certificate.not_valid_after.replace(tzinfo=timezone.utc)
        record = CertificateRecord(cert_id=cert_id, subject=common_name, sans=san_values, serial_number=str(certificate.serial_number), issuer=common_name, not_before=not_before.isoformat(), not_after=not_after.isoformat(), certificate_path=str(cert_path), private_key_ref=key_ref, status="active", key_algorithm=f"RSA-{key_size}")
        return self.inventory.register(record)

    def renew(self, cert_id: str, validity_days: int | None = None) -> CertificateRecord:
        """Generate a replacement certificate with a new serial and same subject/SAN set."""
        current = self.inventory.get(cert_id)
        days = validity_days or max(1, (self._parse(current.not_after) - self._parse(current.not_before)).days)
        self.revoke(cert_id, "renewed") if current.status != "revoked" else None
        return self.generate_self_signed(cert_id, current.subject, current.sans, days, int(current.key_algorithm.split("-")[-1]), owner="pki-renewal", purpose="certificate-renewal")

    def revoke(self, cert_id: str, reason: str) -> CertificateRecord:
        """Mark a certificate revoked and update inventory."""
        if not reason:
            raise ValueError("revocation reason is required")
        return self.inventory.revoke(cert_id, reason)

    def generate_crl(self, crl_path: str | Path, issuer_cert_id: str) -> Path:
        """Generate a CRL from the issuer certificate key and inventory revocations."""
        issuer_record = self.inventory.get(issuer_cert_id)
        key_pem = self.secret_manager.resolve(issuer_record.private_key_ref)
        cert_pem = Path(issuer_record.certificate_path).read_bytes()
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        issuer_key = serialization.load_pem_private_key(key_pem.encode("utf-8"), password=None)
        issuer_cert = x509.load_pem_x509_certificate(cert_pem)
        now = datetime.now(timezone.utc)
        builder = x509.CertificateRevocationListBuilder().issuer_name(issuer_cert.subject).last_update(now).next_update(now + timedelta(days=7))
        for record in self.inventory.list(include_revoked=True):
            if record.status == "revoked" and record.revocation_date:
                revoked = x509.RevokedCertificateBuilder().serial_number(int(record.serial_number)).revocation_date(self._parse(record.revocation_date)).build()
                builder = builder.add_revoked_certificate(revoked)
        crl = builder.sign(private_key=issuer_key, algorithm=hashes.SHA256())
        output = Path(crl_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(crl.public_bytes(serialization.Encoding.PEM))
        return output

    @staticmethod
    def _parse(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
