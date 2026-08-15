"""Foundation exception hierarchy."""
class AutoNetError(Exception):
    """Base project exception."""
class ValidationError(AutoNetError):
    """Raised when an input contract is invalid."""
class ConfigurationError(AutoNetError):
    """Raised when configuration is incomplete or inconsistent."""
class DependencyUnavailableError(AutoNetError):
    """Raised when an optional dependency is unavailable and no fallback exists."""
class SecurityError(AutoNetError):
    """Raised when a security operation cannot be completed safely."""
