from documentation.formatters.watermark_formatter import WatermarkFormatter

def test_watermark_formatter_supports_confidential():
    assert WatermarkFormatter().format("CONFIDENTIAL") == "CONFIDENTIAL"
