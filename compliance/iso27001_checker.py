"""ISO/IEC 27001 technical network control checker."""
from .framework_checker import FrameworkChecker
from .compliance_models import ComplianceFramework

class ISO27001ComplianceChecker(FrameworkChecker):
    """Assess mapped network security controls without claiming an ISMS certification result."""
    framework = ComplianceFramework.ISO_27001
    framework_name = "ISO/IEC 27001 technical network assessment"

Iso27001Checker = ISO27001ComplianceChecker
