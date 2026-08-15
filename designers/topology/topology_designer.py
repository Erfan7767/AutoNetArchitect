"""Logical topology designer."""
from designers.base_designer import BaseDesigner
from .fault_domain import FaultDomain
class TopologyDesigner(BaseDesigner):
    """Design topology and explicit fault domains."""
    def design(self,requirements):
        domains=[FaultDomain(f"fd-{i+1}",members,"site" if i==0 else "rack") for i,members in enumerate(requirements.get("fault_domain_members",[]))]
        if not domains:self.record_assumption("fault_domains","inferred from sites","no explicit domains supplied")
        topology=requirements.get("topology","collapsed_core")
        self.record_decision("topology",topology,"selected from stated topology intent",["collapsed_core","three_tier"],{})
        return {"topology":topology,"fault_domains":domains,"decisions":self.decisions,"assumptions":self.assumptions}
