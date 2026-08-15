import tempfile
from pathlib import Path
from zipfile import ZipFile
from reports.as_built_generator import AsBuiltGenerator
from reports.handover_pack_generator import HandoverPackGenerator

def test_handover_pack_contains_as_built_files_and_guide():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        package = AsBuiltGenerator().generate(project_snapshot={"name":"demo"}, design_snapshot={}, deployment_snapshot={}, operational_snapshot={}, output_directory=root/"as-built", sot_basis={"OPERATIONAL":"sot:operational"})
        output = root / "handover.zip"
        handover = HandoverPackGenerator().generate(as_built=package, output_path=output, additional_notes=["Human acceptance required"])
        with ZipFile(output) as archive:
            names = set(archive.namelist())
            guide = archive.read("HANDOVER.md").decode("utf-8")
        assert "HANDOVER.md" in names and "handover_metadata.json" in names
        assert "Human acceptance required" in guide
        assert handover.secret_values_included is False
