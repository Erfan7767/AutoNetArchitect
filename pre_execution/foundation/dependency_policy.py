"""Dependency and automation policy checks."""
from .exceptions import ApprovalRequiredError, ValidationError
APPROVAL_REQUIRED = frozenset({'save_final_configuration','connect_to_device','state_change','deployment'})
def require_approval(action: str, approved: bool = False) -> None:
    """Require approval for side-effecting actions."""
    if action in APPROVAL_REQUIRED and not approved: raise ApprovalRequiredError(f"approval required for {action}")
def validate_vendor(vendor: str) -> str:
    """Accept only the V1 supported vendor."""
    if vendor != 'Huawei': raise ValidationError(f"unsupported vendor: {vendor}")
    return vendor
