from documentation.formatters.arabic_formatter import ArabicFormatter

def test_arabic_formatter_provides_bilingual_headers():
    value = ArabicFormatter().bilingual_header("Network", "الشبكة")
    assert "Network" in value and value
