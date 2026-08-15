import tempfile
from pathlib import Path
from zipfile import ZipFile
from reports.word_generator import WordGenerator

def test_word_generator_creates_valid_docx_with_rtl_content():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "report.docx"
        artifact = WordGenerator().generate(title="Handover / التسليم", sections={"Summary":"حالة الشبكة"}, output_path=path, language="both", sot_basis={"DESIGN":"sot:design"}, evidence_basis=["ev-1"])
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            document = archive.read("word/document.xml").decode("utf-8")
        assert "word/document.xml" in names
        assert "w:rtl" in document
        assert artifact.format == "docx"
