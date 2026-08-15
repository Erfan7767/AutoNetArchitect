"""Chaos test for missing configuration-rendering dependency."""
from __future__ import annotations

from unittest.mock import patch

from config_generators.cisco.ios_xe_generator import IOSXEGenerator


def test_missing_jinja2_dependency_is_explicitly_reported():
    generator = IOSXEGenerator()
    original_import = __import__

    def missing_jinja2(name, *args, **kwargs):
        if name == "jinja2":
            raise ImportError("simulated missing jinja2")
        return original_import(name, *args, **kwargs)

    rejected = False
    with patch("builtins.__import__", side_effect=missing_jinja2):
        try:
            generator._render({"device_id": "MISSING-DEP", "commands": [], "secret_references": [], "decision_ids": []})
        except RuntimeError as exc:
            rejected = True
            assert "Jinja2" in str(exc)
    if not rejected:
        raise AssertionError("missing Jinja2 must produce an explicit runtime error")
