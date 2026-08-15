from documentation.formatters.table_formatter import TableFormatter

def test_table_formatter_is_deterministic():
    headers, rows = TableFormatter().normalize([{"b": 2, "a": 1}])
    assert headers == ["a", "b"] and rows == [["1", "2"]]
