from designers.physical.common import PhysicalInfrastructureDesigner
class PhysicalDesigner(PhysicalInfrastructureDesigner):
    """Orchestrate structured cabling, rack, power, cooling, and optics."""
    def design(self,r):
        missing=self.missing_site(r,["site_dimensions"]);self.record_decision("physical_design",True,"physical design is assembled only from supplied site and equipment facts")
        return {"status":"pending_site_data" if missing else "designed","cabling":CablingDesigner().design(r),"rack":RackDesigner().design(r),"power":PowerDesigner().design(r),"cooling":self.cooling(r),"optics":self.optics(r),"decisions":self.decisions,"assumptions":self.assumptions}
    def cooling(self,r):
        watts=sum(x.get("watts",0) for x in r.get("equipment",[]));self.record_decision("cooling_load",watts,"cooling estimate follows supplied equipment power");return {"heat_load_watts":watts,"btu_per_hour":round(watts*3.412,2),"status":"estimated" if watts else "pending_equipment_data"}
    def optics(self,r):
        supported=r.get("supported_transceivers",[]);requested=r.get("requested_transceivers",[]);unsupported=[x for x in requested if x not in supported];self.record_decision("optics",requested,"transceivers are accepted only when present in capability/BOM evidence");return {"requested":requested,"supported":supported,"unsupported":unsupported,"status":"blocked_capability" if unsupported else "validated"}
class CablingDesigner(PhysicalInfrastructureDesigner):
    def design(self,r):
        runs=r.get("cable_runs",[]);self.record_decision("cabling",len(runs),"structured cabling follows endpoint, pathway, distance, and media inputs");return {"runs":runs,"categories":["horizontal","backbone","patching"],"distance_validation":"pending_site_measurement" if not r.get("pathway_distances") else "provided","decisions":self.decisions}
class RackDesigner(PhysicalInfrastructureDesigner):
    def design(self,r):
        units=sum(x.get("rack_units",0) for x in r.get("equipment",[]));available=r.get("available_rack_units");status="pending_site_data" if available is None else "capacity_exceeded" if units>available else "designed";self.record_decision("rack_layout",units,"rack allocation uses equipment RU and measured available space");return {"equipment_units":units,"available_rack_units":available,"status":status,"layout":r.get("rack_layout",[]),"decisions":self.decisions}
class PowerDesigner(PhysicalInfrastructureDesigner):
    def design(self,r):
        load=sum(x.get("watts",0) for x in r.get("equipment",[]));ups=r.get("ups_capacity_watts");self.record_decision("power_ups",load,"power and UPS are sized from equipment load and supplied UPS capacity");return {"load_watts":load,"ups_capacity_watts":ups,"status":"pending_site_data" if ups is None else "capacity_exceeded" if load>ups else "designed","dual_feed":r.get("dual_power_feeds",False),"decisions":self.decisions}
