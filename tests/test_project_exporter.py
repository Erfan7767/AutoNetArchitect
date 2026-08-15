import json
import tempfile
from pathlib import Path
from zipfile import ZipFile
from export.project_exporter import ProjectExporter

def test_project_exporter_redacts_json_and_zip():
    project = {"name":"demo", "password":"raw-secret", "nested":{"token":"raw-token", "reference":"secret://vault/demo"}}
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        result = ProjectExporter().export_json(project=project, output_path=root/"project.json", sot_basis={"DESIGN":"sot:design"})
        text = (root/"project.json").read_text(encoding="utf-8")
        assert "raw-secret" not in text and "raw-token" not in text and "secret://vault/demo" in text
        zip_result = ProjectExporter().export_zip(project=project, output_path=root/"project.zip", sot_basis={"DESIGN":"sot:design"})
        with ZipFile(root/"project.zip") as archive:
            exported = archive.read("project.json").decode("utf-8")
        assert "raw-secret" not in exported
        assert zip_result.secret_values_included is False and result.redaction_applied is True
