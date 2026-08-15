from designers.interface.common import InterfaceDesigner
class InterfaceAllocator(InterfaceDesigner):
    """Allocate available ports without assuming coordinates."""
    def design(self,r):
        available=[x for x in r.get("inventory",[]) if x.get("status","available")=="available"];jobs=list(r.get("jobs",[]));reserve=max(0,round(len(available)*r.get("reserve_fraction",.1)));alloc=[]
        for job,port in zip(jobs,available[:max(0,len(available)-reserve)]):alloc.append({"interface":port.get("name"),"role":job.get("role"),"job":job})
        status="capacity_exceeded" if len(jobs)>len(alloc) else "allocated";self.record_decision("interface_allocation",alloc,"management first, high-speed uplink preference, and spare reserve policy");return {"status":status,"allocations":alloc,"reserve_ports":max(0,len(available)-len(alloc)),"decisions":self.decisions}
