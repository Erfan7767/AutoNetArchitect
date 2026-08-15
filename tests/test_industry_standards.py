"""Requirements layer test."""
from AutoNetArchitect.requirements.industry_standards import IndustryStandards
def test_standard():
    assert IndustryStandards().baseline("enterprise")["source"]
