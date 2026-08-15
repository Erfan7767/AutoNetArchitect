import tempfile
from pathlib import Path
from reports.as_built_generator import AsBuiltGenerator

def test_as_built_generator_creates_snapshots_manifest_and_redacts_secrets():
    with tempfile.TemporaryDirectory() as directory:
        package = AsBuiltGenerator().generate(project_snapshot={"name":"demo", "password":"secret-value"}, design_snapshot={"topology":{"nodes":[{"id":"r1"}], "links":[]}}, deployment_snapshot={"state":"deployed", "token":"secret-value"}, operational_snapshot={"health":"observed"}, evidence_index=[{"evidence_id":"ev-1", "source":"monitoring"}], output_directory=Path(directory)/"as-built", sot_basis={"DESIGN":"sot:design", "DEPLOYMENT":"sot:deployment"}, evidence_basis=["ev-1"])
        assert (Path(directory)/"as-built"/"manifest.json").exists()
        assert (Path(directory)/"as-built"/"topology.mmd").exists()
        assert package.secret_values_included is False
        assert "secret-value" not in (Path(directory)/"as-built"/"project_snapshot.json").read_text(encoding="utf-8")
