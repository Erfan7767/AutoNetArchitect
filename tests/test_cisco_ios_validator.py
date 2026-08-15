from importlib import import_module
from pathlib import Path


Validator = getattr(import_module("config_validators.vendor_validators.cisco_ios_validator"), "CiscoIosValidator")


def test_cisco_ios_valid_fixture_has_no_invalid_lines():
    text = Path("tests/fixtures/valid_configs/cisco_ios_valid.txt").read_text()
    results = Validator().validate(text)
    assert results
    assert all(result.valid for result in results)


def test_cisco_ios_invalid_fixture_is_detected():
    text = Path("tests/fixtures/invalid_configs/cisco_ios_invalid.txt").read_text()
    results = Validator().validate(text)
    assert any(not result.valid for result in results)
