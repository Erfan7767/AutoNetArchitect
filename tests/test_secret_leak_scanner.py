from config_validators.secret_leak_scanner import SecretLeakScanner


def test_secret_scanner_detects_plaintext_without_returning_value():
    diagnostics = SecretLeakScanner().scan("username admin password cleartext\nsnmp-server community public RO\n", "Cisco", "IOS XE")
    assert diagnostics
    assert all("cleartext" not in (item.command or "") for item in diagnostics)
    assert all(item.code in {"SECRET_LEAK", "HIGH_ENTROPY_SECRET_CANDIDATE"} for item in diagnostics)


def test_secret_scanner_allows_secret_references():
    diagnostics = SecretLeakScanner().scan("username admin secret 9 secret://device/admin\n", "Cisco", "IOS XE")
    assert not diagnostics
