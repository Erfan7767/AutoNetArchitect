"""PCI DSS technical network control checker."""
from .framework_checker import FrameworkChecker
from .compliance_models import ComplianceFramework

class PCIComplianceChecker(FrameworkChecker):
    """Assess cardholder-data network boundary and supporting technical controls only."""
    framework = ComplianceFramework.PCI_DSS
    framework_name = "PCI DSS technical network assessment"

PciChecker = PCIComplianceChecker
