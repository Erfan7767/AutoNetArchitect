"""IGP strategy selector."""
from designers.base_designer import BaseDesigner
from .common import evidence_status
class RoutingStrategySelector(BaseDesigner):
    """Select OSPF, EIGRP, IS-IS, or static without inventing identifiers."""
    def design(self,requirements):
        vendors=set(requirements.get("vendors",[]));multi=bool(requirements.get("multi_vendor",False));existing=requirements.get("existing_protocol");size=int(requirements.get("device_count",0));topology=requirements.get("topology","campus");
        if existing in {"ospf","eigrp","isis"}: choice=existing;why="brownfield protocol retained pending validation"
        elif multi: choice="ospf";why="multi-vendor requirement"
        elif vendors=={"Cisco"} and requirements.get("allow_eigrp",False): choice="eigrp";why="Cisco-only scope and explicit EIGRP policy"
        elif topology=="data_center" and requirements.get("scalability","normal")=="high": choice="isis";why="data-center scalability policy"
        else: choice="ospf";why="broad enterprise interoperability"
        if not requirements.get("evidence_ids"): self.record_assumption("capability_evidence","required","protocol capability must be verified before production")
        decision=self.record_decision("routing_strategy",choice,why,["ospf","eigrp","isis","static"],{"eigrp":"multi-vendor or missing Cisco-only evidence","isis":"no high-scale data-center policy","static":"not scalable as sole IGP"})
        return {"protocol":choice,"rationale":why,"evidence_status":evidence_status(requirements.get("evidence_ids")),"decision":decision,"assumptions":self.assumptions}
