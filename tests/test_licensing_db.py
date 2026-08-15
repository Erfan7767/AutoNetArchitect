from equipment.licensing_db import LicenseRecord, LicensingDB


def test_license_entitlement_requires_verified_evidence():
    db = LicensingDB(
        [LicenseRecord("AcmeNet", "advanced", "Advanced", ("routing",), True, "verified", ("ev-license",), confidence=0.91)],
        {"ev-license": {"source_id": "src-license", "verification_state": "verified", "revoked": False, "expired": False}},
        {"src-license": {"verified": True}},
    )
    assert db.has_verified_entitlement("AcmeNet", "advanced", "routing")[:2] == (True, "license_entitlement_verified")


def test_unknown_license_is_rejected():
    db = LicensingDB()
    assert db.has_verified_entitlement("AcmeNet", "advanced", "routing")[0] is False
