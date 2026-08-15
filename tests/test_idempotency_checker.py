from config_validators.idempotency_checker import IdempotencyChecker


def test_idempotency_checker_flags_destructive_and_removal_commands():
    diagnostics = IdempotencyChecker().check("no ip route 0.0.0.0 0.0.0.0\nreload\n", "Cisco", "IOS XE")
    codes = {item.code for item in diagnostics}
    assert "REMOVAL_ON_REAPPLICATION" in codes
    assert "DESTRUCTIVE_REAPPLICATION" in codes
