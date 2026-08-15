"""Pre-execution contract test."""
def test_source_policy_mentions_unknowns():
    assert 'HumanSuppliedMandatory' in __import__('pathlib').Path('pre_execution/config/source_of_truth_policy.yaml').read_text()
