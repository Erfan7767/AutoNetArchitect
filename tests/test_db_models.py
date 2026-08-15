from database.db_models import DatabaseHealth, MigrationRecord, ProjectRow


def test_db_models_are_typed_and_serializable():
    row = ProjectRow("p1", "1.0.0", "{}", "checksum", "2026-01-01T00:00:00+00:00")
    assert row.to_dict()["project_id"] == "p1"
    assert MigrationRecord("0001", "hash", "now").migration_id == "0001"
    assert DatabaseHealth(False, None, None, 0, True, "disabled").healthy
