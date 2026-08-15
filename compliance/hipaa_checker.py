"""HIPAA technical network control checker."""
from .framework_checker import FrameworkChecker
from .compliance_models import ComplianceFramework

class HIPAAComplianceChecker(FrameworkChecker):
    """Assess network access, segmentation, logging, change, and resilience mappings only."""
    framework = ComplianceFramework.HIPAA
    framework_name = "HIPAA technical network assessment"

HipaaChecker = HIPAAComplianceChecker
