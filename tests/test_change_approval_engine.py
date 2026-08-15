from change_management import Approval, ChangeApprovalEngine, ChangeRequest, RiskAssessment


def test_change_approval_engine_requires_all_roles_and_sector_overrides():
    request = ChangeRequest("CHG-7", "Security", "Detailed", "alice", change_type="normal", risk_assessment=RiskAssessment(9.0, "critical"))
    engine = ChangeApprovalEngine()
    requirements = engine.requirements(request, sector="banking")
    assert "technical_reviewer" in requirements.required_roles
    assert "cto_or_it_director" in requirements.required_roles
    assert "security_reviewer" in requirements.required_roles
    pending = engine.evaluate(request, requirements.required_roles)
    assert pending.state == "pending"
    for role in requirements.required_roles:
        pending = engine.record(request, Approval(role, role, "approved", "approved"),)
    assert pending.state == "approved"


def test_change_approval_engine_rejection_blocks():
    request = ChangeRequest("CHG-8", "Change", "Detailed", "alice")
    engine = ChangeApprovalEngine()
    engine.record(request, Approval("technical_reviewer", "bob", "rejected", "insufficient evidence"))
    assert engine.evaluate(request, ["technical_reviewer"]).state == "rejected"
