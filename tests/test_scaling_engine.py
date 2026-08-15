"""Requirements layer test."""
from AutoNetArchitect.requirements.scaling_engine import ScalingEngine
def test_brownfield():
    assert ScalingEngine().classify_environment({"existing_inventory_required":True}) == "brownfield"
