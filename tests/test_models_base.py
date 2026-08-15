"""Foundation smoke test."""
from AutoNetArchitect.models.base import FoundationModel
def test_base_conversion():
    class Item(FoundationModel):
        value: int
    assert Item.from_dict({"value": 1}).to_dict()["value"] == 1
