"""Requirements layer test."""
from AutoNetArchitect.questionnaire.contradiction_detector import ContradictionDetector
def test_detector():
    assert ContradictionDetector().detect({"high_availability":True,"redundancy_level":0}).has_contradictions
