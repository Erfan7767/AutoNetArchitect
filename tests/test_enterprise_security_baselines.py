from domain_packs.enterprise_corporate.security_baselines import EnterpriseSecurityBaselines

def test_security_segments_exist():
    result = EnterpriseSecurityBaselines().design({"sector": "enterprise_corporate"})
    assert {"guest", "staff", "voice", "iot"}.issubset(set(result["artifact"]["segments"]))
