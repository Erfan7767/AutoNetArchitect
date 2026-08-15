from governance.accountability_matrix import AccountabilityMatrix, DecisionClass, RiskClass
from governance.governance_reporter import GovernanceReporter

def test_governance_reporter_lists_pending_checkpoints_and_boundaries():
    requirement = AccountabilityMatrix().resolve(workflow="deployment", decision_class=DecisionClass.DEPLOYMENT, risk_class=RiskClass.CRITICAL)
    report = GovernanceReporter().generate(project_id="p-1", requirements=[requirement])
    markdown = GovernanceReporter().to_markdown(report)
    assert report.pending_human_checkpoints and "Human Checkpoints" in markdown and report.legal_boundary_notes == ()
