"""Foundation smoke test."""
from AutoNetArchitect.models.enums import ProjectStatus
def test_enum():
    assert ProjectStatus.DRAFT.value == "draft"
