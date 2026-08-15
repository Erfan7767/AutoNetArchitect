from governance.accountability_matrix import AccountabilityMatrix, DecisionClass, RiskClass
from governance.review_classes import ReviewClass

def test_accountability_matrix_resolves_critical_deployment_checkpoints():
    requirement = AccountabilityMatrix().resolve(workflow="deployment", decision_class=DecisionClass.DEPLOYMENT, risk_class=RiskClass.CRITICAL)
    assert requirement.accountable_owner_role == "deployment_owner"
    assert ReviewClass.SECURITY in requirement.required_review_classes
    assert "deployment_approver" in requirement.required_approver_roles
    assert requirement.execution_authority_roles

def test_accountability_matrix_adds_banking_security_review():
    requirement = AccountabilityMatrix().resolve(workflow="design", decision_class=DecisionClass.DESIGN, risk_class=RiskClass.HIGH, sector="banking")
    assert ReviewClass.SECURITY in requirement.required_review_classes
