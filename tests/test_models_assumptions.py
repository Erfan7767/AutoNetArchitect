"""Foundation smoke test."""
from AutoNetArchitect.models.assumptions import Assumption, AssumptionRegistry
def test_registry():
    registry = AssumptionRegistry(); registry.add(Assumption(key="topology")); assert len(registry.unresolved()) == 1
