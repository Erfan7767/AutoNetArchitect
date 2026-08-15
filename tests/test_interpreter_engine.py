from troubleshooting.show_command_interpreter import InterpreterEngine


def test_interpreter_engine_parses_generic_interface_and_rejects_write():
    engine = InterpreterEngine()
    result = engine.parse("Gi1 up up", "show interfaces", "unknown", "unknown")
    assert result.parsed_data["interface"] == "Gi1"
    try:
        engine.parse("ok", "configure terminal", "unknown", "unknown")
    except ValueError as error:
        assert "read-only" in str(error)
    else:
        raise AssertionError("write command must be rejected")
