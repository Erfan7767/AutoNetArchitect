from benchmarking.scenario_corpus import ScenarioClass, ScenarioCorpus

def test_scenario_corpus_covers_required_dimensions():
    classes = {item_class for item in ScenarioCorpus().all() for item_class in item.classes}
    assert {ScenarioClass.GREENFIELD, ScenarioClass.BROWNFIELD, ScenarioClass.MULTI_SITE, ScenarioClass.VENDOR_SPECIFIC, ScenarioClass.AMBIGUOUS_INPUTS, ScenarioClass.INCOMPLETE_DATA, ScenarioClass.HIGH_RISK_DEPLOYMENT} <= classes

def test_scenario_corpus_fingerprint_is_repeatable():
    assert ScenarioCorpus().fingerprint() == ScenarioCorpus().fingerprint()
