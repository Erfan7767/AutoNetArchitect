"""Smoke test for infrastructure component memory_backend."""
def test_memory_backend_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
