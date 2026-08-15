import tempfile
from pathlib import Path
from reports.pdf_generator import PDFGenerator
from reports.report_models import ReportLanguage

def test_pdf_generator_supports_arabic_and_declares_basis():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "report.pdf"
        artifact = PDFGenerator().generate(title="Network Report / تقرير الشبكة", sections={"Summary":"password=not-a-secret", "Arabic":"حالة الشبكة"}, output_path=path, language=ReportLanguage.BOTH, sot_basis={"DESIGN":"sot:design"}, evidence_basis=["ev-1"])
        assert path.exists() and path.stat().st_size > 0
        assert artifact.metadata.sot_basis["DESIGN"] == "sot:design"
        assert artifact.metadata.secret_values_included is False
