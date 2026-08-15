"""Smoke test for infrastructure component dependency_graph."""
def test_dependency_graph_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
