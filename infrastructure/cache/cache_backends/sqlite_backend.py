"""SQLite backend declaration."""
class SQLiteBackend:
    """Represent a SQLite cache target without owning a connection."""
    def __init__(self, database: str) -> None: self.database = database
