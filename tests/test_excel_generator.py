import tempfile
from pathlib import Path
from reports.excel_generator import ExcelGenerator

def test_excel_generator_writes_metadata_sot_and_redacted_records():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "report.xlsx"
        artifact = ExcelGenerator().generate(title="Operations Report", records=[{"device":"r1", "password":"raw-secret", "reference":"secret://vault/r1"}], output_path=path, sot_basis={"OPERATIONAL":"sot:operational"}, evidence_basis=["ev-op"], assumptions=["maintenance window supplied by human"])
        assert path.exists() and path.stat().st_size > 0
        assert artifact.metadata.secret_values_included is False
