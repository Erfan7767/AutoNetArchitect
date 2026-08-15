from governance import SignoffEvaluation
from review_console.signoff_panel import SignoffPanel

def test_signoff_panel_renders_governance_pending_state():
    view = SignoffPanel().build(SignoffEvaluation(workflow="deployment", allowed=False, state="blocked_pending_signoff", required_approvals=("deployment_approver",), pending_checkpoints=("approval:deployment_approver",), reasons=("approval missing",)))
    assert view is not None and view.workflow == "deployment" and view.pending_checkpoints == ("approval:deployment_approver",) and not view.allowed
