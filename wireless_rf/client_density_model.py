"""Client density model."""
class ClientDensityModel:
    """Classify known client density without fabricating measurements."""
    def classify(self,clients:int|None)->str:
        """Return unknown, low, medium, or high."""
        if clients is None:return "unknown"
        if clients<0:raise ValueError("clients cannot be negative")
        return "low" if clients<25 else "medium" if clients<75 else "high"
