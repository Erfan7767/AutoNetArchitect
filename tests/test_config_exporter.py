import tempfile
from pathlib import Path
from zipfile import ZipFile
from export.config_exporter import ConfigExporter

def test_config_exporter_redacts_text_and_preserves_secret_reference():
    configs = {"router-1":"hostname router-1\npassword raw-secret\nusername admin secret://vault/router-1", "firewall-1":{"api_token":"raw-token", "endpoint":"https://fw.local"}}
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        result = ConfigExporter().export_directory(configurations=configs, output_directory=root/"configs", sot_basis={"DEPLOYMENT":"sot:deployment"})
        text = (root/"configs"/"router-1.cfg").read_text(encoding="utf-8")
        assert "raw-secret" not in text and "secret://vault/router-1" in text
        zip_result = ConfigExporter().export_zip(configurations=configs, output_path=root/"configs.zip", sot_basis={"DEPLOYMENT":"sot:deployment"})
        with ZipFile(root/"configs.zip") as archive:
            names = set(archive.namelist())
            firewall = archive.read("firewall-1.json").decode("utf-8")
        assert "firewall-1.json" in names and "raw-token" not in firewall
        assert result.secret_values_included is False and zip_result.redaction_applied is True
