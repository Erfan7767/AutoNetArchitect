"""Resource monitoring facade."""
class ResourceMonitor:
    """Expose process resource measurements."""
    def snapshot(self) -> dict[str, float]: """Return a portable resource snapshot."""; return {"cpu_percent": 0.0, "memory_percent": 0.0}
