from documentation.formatters.toc_generator import TOCGenerator

def test_toc_generator_lists_sections():
    toc = TOCGenerator().generate({"sections": [{"section_id": "s", "title_en": "Summary", "title_ar": "ملخص", "level": 1}]})
    assert toc[0]["section_id"] == "s"
