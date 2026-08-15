"""Platform capability helpers."""
import platform
def platform_name() -> str: """Return the operating-system name."""; return platform.system().lower()
def python_version() -> str: """Return the Python runtime version."""; return platform.python_version()
