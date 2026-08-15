from troubleshooting.show_command_interpreter import JuniperInterpreter


def test_juniper_interpreter_parses_vendor_metadata_and_anomalies():
    interpreter = JuniperInterpreter()
    result = interpreter.interpret("neighbor down crc error", "show interfaces")
    assert result.vendor
    assert result.platform
    assert result.confidence > 0.0
    assert result.anomalies
