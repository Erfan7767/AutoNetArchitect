from pathlib import Path
import tempfile

from database.db_manager import DBManager
from database.db_models import MigrationRecord, ProjectRow


def test_db_manager_optional_and_sqlite_roundtrip():
    disabled = DBManager()
    assert not disabled.enabled
    assert disabled.health().healthy
    with tempfile.TemporaryDirectory() as directory:
        manager = DBManager(Path(directory) / "projects.sqlite3")
        row = ProjectRow("p1", "1.0.0", '{"project_id":"p1"}', "hash", "2026-01-01T00:00:00+00:00")
        manager.save_project(row)
        assert manager.load_project("p1") == row
        manager.record_migration(MigrationRecord("0001_initial", "migration-hash", "now"))
        assert manager.migrations()[0].migration_id == "0001_initial"
        assert manager.list_project_ids() == ("p1",)
        assert manager.health().healthy
        manager.delete_project("p1")
        assert manager.load_project("p1") is None
