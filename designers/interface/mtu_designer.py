from designers.interface.common import InterfaceDesigner
class MTUDesigner(InterfaceDesigner):
    """Design MTU by role and flag unknown ISP constraints."""
    DEFAULTS={"access":1500,"trunk":9216,"uplink":9216,"wan":1500,"gre":1476,"storage":9000,"iscsi":9000}
    def design(self,r):
        role=r.get("role","access");mtu=r.get("mtu",self.DEFAULTS.get(role,1500));
        if role=="wan" and "mtu" not in r:self.record_assumption("isp_mtu",None,"HumanSuppliedMandatory: ISP MTU is unknown")
        self.record_decision("mtu",mtu,"role-based MTU with explicit ISP override when supplied");return {"role":role,"mtu":mtu,"status":"pending_isp_constraint" if role=="wan" and "mtu" not in r else "designed","path_consistency_required":True,"decisions":self.decisions,"assumptions":self.assumptions}
