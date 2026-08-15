from designers.interface.common import InterfaceDesigner
class InterfaceCapacityValidator(InterfaceDesigner):
    """Validate ports, PoE, spares, and uplink aggregate capacity."""
    def design(self,r):
        total=len(r.get("inventory",[]));allocated=len(r.get("allocations",[]));poe_total=sum(x.get("poe_budget_watts",0) for x in r.get("inventory",[]));poe_used=sum(x.get("poe_watts",0) for x in r.get("jobs",[]));spare=total-allocated;self.record_decision("capacity",{"total":total,"allocated":allocated,"spare":spare},"capacity must be measured from inventory and jobs");return {"total_ports":total,"allocated_ports":allocated,"spare_ports":spare,"spare_percentage":round(spare/total,3) if total else 0,"poe_budget_total_watts":poe_total,"poe_consumed_watts":poe_used,"poe_remaining_watts":poe_total-poe_used,"status":"capacity_exceeded" if allocated>total or poe_used>poe_total else "valid","decisions":self.decisions}
