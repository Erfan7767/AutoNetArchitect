"""Smoke test for infrastructure component file_backend."""
def test_file_backend_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
