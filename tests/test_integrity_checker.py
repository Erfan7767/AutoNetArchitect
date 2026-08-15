from persistence.integrity_checker import IntegrityChecker, IntegrityError


def test_integrity_checker_verifies_and_rejects_envelopes():
    envelope = {"project_id": "p1", "schema_version": "1.0.0", "payload": {"name": "demo"}, "checksum_algorithm": "sha256"}
    envelope["checksum"] = IntegrityChecker.envelope_checksum(envelope)
    assert IntegrityChecker.verify_envelope(envelope)
    envelope["payload"]["name"] = "tampered"
    try:
        IntegrityChecker.verify_envelope(envelope)
    except IntegrityError:
        return
    raise AssertionError("tampered payload must fail checksum verification")
