from persistence.schema_migrations import SchemaMigrationError, SchemaMigrator


def test_schema_migrator_upgrades_supported_versions():
    migrator = SchemaMigrator()
    payload, applied = migrator.migrate({"project_id": "p1"}, "0.9.0")
    assert payload["project_id"] == "p1"
    assert "assumptions" in payload
    assert applied == ("0.9.0->1.0.0",)
    current, no_steps = migrator.migrate({"project_id": "p1"}, "1.0.0")
    assert current == {"project_id": "p1"}
    assert no_steps == ()


def test_schema_migrator_refuses_unknown_version():
    try:
        SchemaMigrator().migrate({}, "0.1.0")
    except SchemaMigrationError:
        return
    raise AssertionError("unknown schema must not be guessed")
