"""Typed exceptions raised by governance validation."""
class PreExecutionError(Exception):
    """Base exception for pre-execution failures."""
class ValidationError(PreExecutionError):
    """Raised when a contract is invalid."""
class ApprovalRequiredError(PreExecutionError):
    """Raised when an action requires explicit approval."""
