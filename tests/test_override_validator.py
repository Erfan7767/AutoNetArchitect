from expert_override.override_models import OverrideRequest, OverrideScope, OverrideTargetType, OverrideType
from expert_override.override_validator import OverrideValidator

def _request(**kwargs):
    values = {"override_id": "ov-v", "target_id": "config-1", "target_type": OverrideTargetType.CONFIG_ARTIFACT, "override_type": OverrideType.MODIFY_VALUE, "scope": OverrideScope(project_id="p-1", workflow="config_generation", target_ids=("config-1",), scope_statement="one config"), "actor_id": "eng", "actor_role": "engineer", "reason": "vendor field evidence", "impact": "revalidation required", "proposed_value": "new-config"}
    values.update(kwargs)
    return OverrideRequest(**values)

def test_validator_requires_approval_for_elevated_target():
    assert not OverrideValidator().validate(_request()).allowed

def test_validator_accepts_config_change_with_approval_reference():
    result = OverrideValidator().validate(_request(approval_reference="approval://config/1"))
    assert result.allowed and result.requires_revalidation
