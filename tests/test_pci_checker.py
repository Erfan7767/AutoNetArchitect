from compliance.pci_checker import PCIComplianceChecker
from compliance.compliance_models import ComplianceFramework

def test_pci_checker_exposes_segmentation_control():
    result = PCIComplianceChecker().assess()
    assert result.framework == ComplianceFramework.PCI_DSS
    assert any("SEGMENT" in item.control.control_id for item in result.controls)
    assert result.certification_statement.startswith("No certification")
