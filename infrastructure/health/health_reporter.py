"""Health report rendering."""
class HealthReporter:
    """Aggregate health results."""
    def report(self, results: list[object]) -> dict[str, bool]: """Return component health states."""; return {getattr(r, "component", "unknown"): bool(getattr(r, "healthy", False)) for r in results}
