"""Integration tests for project serialization and persistence integrity."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from persistence.project_persistence import PersistenceError, ProjectPersistence
from tests.conftest import assert_secret_safe
from tests.final_test_helpers import fixture_project


def test_golden_project_save_load_roundtrip_preserves_payload_and_checksum():
    with TemporaryDirectory() as tmp:
        store = ProjectPersistence(Path(tmp) / "projects")
        fixture = fixture_project("enterprise_greenfield")
        result = store.save(fixture["project_id"], fixture)
        loaded, loaded_result = store.load(fixture["project_id"])
        assert loaded == fixture | {"schema_version": result.schema_version}
        assert loaded_result.checksum == result.checksum
        assert_secret_safe(loaded)


def test_corrupted_envelope_is_rejected_without_fallback_claims():
    with TemporaryDirectory() as tmp:
        store = ProjectPersistence(Path(tmp) / "projects")
        fixture = fixture_project("branch_brownfield")
        store.save(fixture["project_id"], fixture)
        target = store.path_for(fixture["project_id"])
        envelope = json.loads(target.read_text(encoding="utf-8"))
        envelope["payload"]["scenario"] = "tampered"
        target.write_text(json.dumps(envelope), encoding="utf-8")
        rejected = False
        try:
            store.load(fixture["project_id"])
        except PersistenceError:
            rejected = True
        if not rejected:
            raise AssertionError("tampered project envelope must be rejected")
