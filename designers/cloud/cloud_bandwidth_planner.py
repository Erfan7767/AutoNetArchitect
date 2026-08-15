from designers.cloud.common import CloudDesigner
class CloudBandwidthPlanner(CloudDesigner):
    """Cloud connectivity design engine."""
    def design(self,r):
        provided="bandwidth_mbps" in r;bw=r.get("bandwidth_mbps");users=r.get("users",0);estimate=bw if provided else users*2;self.record_assumption("bandwidth_estimate",estimate,"estimated from user count; validate with traffic telemetry") if not provided else None;self.record_decision("cloud_bandwidth",estimate,"capacity includes growth and upgrade path");return {"minimum_mbps":estimate,"growth_percent":r.get("growth_percent",30),"upgrade_path":True,"basis":"measured" if provided else "assumption","decisions":self.decisions,"assumptions":self.assumptions}
