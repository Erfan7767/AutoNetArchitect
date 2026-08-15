"""Requirements layer test."""
from AutoNetArchitect.questionnaire.defaults_engine import DefaultsEngine
def test_defaults():
    assert DefaultsEngine().suggest({"wan_required":False})["site_count"]["value"] == 1
