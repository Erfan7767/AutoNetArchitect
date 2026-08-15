"""Requirements layer test."""
from AutoNetArchitect.questionnaire.scoring import ScoringEngine
def test_score():
    assert ScoringEngine().score(["a"], {"a":1}) == 1
