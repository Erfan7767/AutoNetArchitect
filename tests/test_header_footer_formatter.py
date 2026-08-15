from documentation.formatters.header_footer_formatter import HeaderFooterFormatter

def test_header_footer_formatter_builds_metadata():
    value = HeaderFooterFormatter().build(title="HLD", confidential=True)
    assert value["footer"] == "CONFIDENTIAL"
