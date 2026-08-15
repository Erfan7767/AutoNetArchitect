from datetime import datetime, timedelta, timezone
from governance.authority_model import AuthorityGrant, AuthorityModel, AuthorityType
from governance.accountability_matrix import RiskClass

def test_authority_model_requires_current_explicit_grant():
    model = AuthorityModel()
    grant = AuthorityGrant(grant_id="g-1", principal_id="alice", role="deployment_operator", authority_type=AuthorityType.EXECUTOR, workflows=("deployment",), maximum_risk=RiskClass.CRITICAL, reference="approval://grant", expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    model.grant(grant)
    assert model.check(principal_id="alice", workflow="deployment", risk_class=RiskClass.CRITICAL, authority_type=AuthorityType.EXECUTOR, required_role="deployment_operator").allowed
    assert not model.check(principal_id="bob", workflow="deployment", risk_class=RiskClass.CRITICAL, authority_type=AuthorityType.EXECUTOR, required_role="deployment_operator").allowed

def test_authority_model_revocation_blocks_grant():
    model = AuthorityModel()
    model.grant(AuthorityGrant(grant_id="g-2", principal_id="alice", role="reviewer", authority_type=AuthorityType.REVIEWER, workflows=("design",), maximum_risk=RiskClass.HIGH))
    model.revoke("g-2", "role ended")
    assert not model.check(principal_id="alice", workflow="design", risk_class=RiskClass.HIGH, authority_type=AuthorityType.REVIEWER, required_role="reviewer").allowed
