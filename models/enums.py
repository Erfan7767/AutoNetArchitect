"""Shared domain enumerations."""
from enum import StrEnum
class ProjectStatus(StrEnum):
    """Official project lifecycle states."""
    DRAFT = "draft"; SPECIFIED = "specified"; DESIGNED = "designed"; VALIDATED = "validated"; APPROVED = "approved"; DEPLOYED = "deployed"; BLOCKED = "blocked"
class ApprovalStatus(StrEnum):
    """Approval states."""
    PENDING = "pending"; APPROVED = "approved"; REJECTED = "rejected"
