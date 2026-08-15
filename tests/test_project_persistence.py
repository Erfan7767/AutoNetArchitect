from pathlib import Path
import json
import tempfile

from database.db_manager import DBManager
from persistence.project_persistence import PersistenceError, ProjectPersistence


def test_project_persistence_local_roundtrip_and_sqlite_mirror():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        persistence = ProjectPersistence(root / "projects", DBManager(root / "projects.sqlite3"))
        payload = {"project_id": "p1", "name": "demo", "decisions": [{"id": "d1"}]}
        saved = persistence.save("p1", payload)
        loaded, result = persistence.load("p1")
        assert loaded["name"] == "demo"
        assert result.checksum == saved.checksum
        assert persistence.exists("p1")
        assert list((root / "projects").glob("*.tmp")) == []


def test_project_persistence_detects_corruption_and_migrates_old_schema():
    with tempfile.TemporaryDirectory() as directory:
        persistence = ProjectPersistence(Path(directory) / "projects")
        persistence.save("p1", {"project_id": "p1", "name": "demo"})
        path = persistence.path_for("p1")
        envelope = json.loads(path.read_text(encoding="utf-8"))
        envelope["payload"]["name"] = "corrupt"
        path.write_text(json.dumps(envelope), encoding="utf-8")
        try:
            persistence.load("p1")
        except PersistenceError:
            pass
        else:
            raise AssertionError("corruption must fail before deserialization")
        old = {"project_id": "p2", "schema_version": "0.9.0", "saved_at": "now", "checksum_algorithm": "sha256", "payload": {"project_id": "p2"}}
        from persistence.integrity_checker import IntegrityChecker
        old["checksum"] = IntegrityChecker.envelope_checksum(old)
        old_path = persistence.path_for("p2")
        old_path.write_text(json.dumps(old), encoding="utf-8")
        migrated, result = persistence.load("p2")
        assert migrated["schema_version"] == "1.0.0"
        assert result.migrated_from == "0.9.0"
        assert result.migrations_applied == ("0.9.0->1.0.0",)
