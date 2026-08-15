"""E2E-style session tests for the V1 UI shell.

The current UI is framework-neutral; this test exercises the session contract
that a Streamlit adapter would consume without importing a UI framework.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json

from ui.app import create_app


def test_ui_session_selects_project_persists_questionnaire_and_shows_audit():
    with TemporaryDirectory() as tmp:
        shell = create_app(Path(tmp))
        try:
            selected = shell.controller.select_project("EnterpriseGreenfield", "e2e-engineer")
            assert selected.status == "success"
            questionnaire = shell.dispatch("01_questionnaire.py", {"site_type": "hq", "provider_asn": "HumanSuppliedMandatory"})
            assert questionnaire.status == "saved"
            admin = shell.dispatch("10_admin.py", {})
            assert admin.data["project_id"] == "EnterpriseGreenfield"
            audit = shell.dispatch("11_audit.py", {"limit": 20})
            assert audit.status == "success"
            assert audit.data["read_only"] is True
            assert "HumanSuppliedMandatory" not in json.dumps(audit.to_dict(), ensure_ascii=False)
        finally:
            shell.controller.close()
