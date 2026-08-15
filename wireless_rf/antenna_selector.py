"""Evidence-linked antenna selection."""
class AntennaSelector:
    """Select only hardware entries with support evidence."""
    def select(self,hardware:list[dict[str,object]],requirement:str)->dict[str,object]:
        """Return a supported hardware item or an explicit unknown result."""
        for item in hardware:
            if requirement in item.get("capabilities",[]) and item.get("evidence_ids"):return {"status":"selected","hardware":item}
        return {"status":"blocked_no_supported_hardware_evidence","hardware":None}
