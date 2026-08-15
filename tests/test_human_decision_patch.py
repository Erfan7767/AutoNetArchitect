from expert_override.human_decision_patch import HumanDecisionPatch, HumanDecisionPatchManager

def _patch(base="old"):
    return HumanDecisionPatch(patch_id="patch-1", target_id="config-1", author_id="eng", author_role="engineer", base_value=base, proposed_value="new", reason="human decision", override_id="ov-1")

def test_human_patch_applies_on_exact_base():
    result = HumanDecisionPatchManager().apply(_patch(), "old")
    assert result.applied and result.provenance == ("patch-1", "ov-1") and "+++" in result.diff

def test_human_patch_rejects_conflicting_current_value():
    result = HumanDecisionPatchManager().apply(_patch(), "changed")
    assert not result.applied and result.conflict
