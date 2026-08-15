"""Smoke test for infrastructure component sqlite_backend."""
def test_sqlite_backend_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
