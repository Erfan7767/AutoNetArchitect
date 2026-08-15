from designers.cloud.common import CloudDesigner
class CloudStrategySelector(CloudDesigner):
    """Cloud connectivity design engine."""
    def design(self,r):
        critical=r.get("workload_criticality","normal");bw=r.get("bandwidth_mbps",0);dual=r.get("dual_provider",False);
        if dual:method="multi_cloud";why="multiple providers require explicit multi-cloud routing"
        elif critical=="critical" and r.get("dedicated_available"):method="hybrid";why="dedicated primary with VPN backup"
        elif r.get("dedicated_available") and bw>=100:method="dedicated";why="predictable bandwidth requirement"
        else:method="vpn";why="cost and rapid deployment for non-critical or unknown requirements"
        self.record_decision("cloud_strategy",method,why,["vpn","dedicated","hybrid","multi_cloud"],{"vpn":"not enough for critical workload" if critical=="critical" else "not selected","dedicated":"availability or bandwidth criteria not met","hybrid":"no dedicated primary","multi_cloud":"single provider"});return {"method":method,"rationale":why,"source_of_truth":self.source(r),"decisions":self.decisions}
