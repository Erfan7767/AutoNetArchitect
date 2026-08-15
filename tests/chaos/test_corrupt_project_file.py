"""Chaos test for corrupt local project files."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from persistence.project_persistence import PersistenceError, ProjectPersistence
from tests.final_test_helpers import fixture_project


def test_corrupt_project_file_is_rejected_and_not_repaired_silently():
    with TemporaryDirectory() as tmp:
        store = ProjectPersistence(Path(tmp) / "projects")
        project = fixture_project("enterprise_greenfield")
        store.save(project["project_id"], project)
        target = store.path_for(project["project_id"])
        envelope = json.loads(target.read_text(encoding="utf-8"))
        envelope["checksum"] = "0" * 64
        target.write_text(json.dumps(envelope), encoding="utf-8")
        rejected = False
        try:
            store.load(project["project_id"])
        except PersistenceError:
            rejected = True
        if not rejected:
            raise AssertionError("checksum corruption must be rejected")
        assert json.loads(target.read_text(encoding="utf-8"))["checksum"] == "0" * 64
