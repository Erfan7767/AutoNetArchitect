"""Requirements layer test."""
from AutoNetArchitect.requirements.requirements_analyzer import RequirementsAnalyzer
def test_document():
    doc = RequirementsAnalyzer().analyze({"org_type":"enterprise","expected_users":100}, "enterprise")
    assert doc.environment_type and doc.formulas
