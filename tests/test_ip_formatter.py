from documentation.formatters.ip_formatter import IPFormatter

def test_ip_formatter_canonicalizes_network():
    assert IPFormatter().format("10.0.0.1/24") == "10.0.0.1/24"
