from designers.cloud.common import CloudDesigner
class CloudHADesigner(CloudDesigner):
    """Cloud connectivity design engine."""
    def design(self,r):
        tunnels=int(r.get("tunnels",0));circuits=int(r.get("circuits",0));self.record_decision("cloud_ha",{"tunnels":tunnels,"circuits":circuits},"HA uses independent paths and a documented failover test");return {"status":"ha_ready" if tunnels>=2 or circuits>=2 else "single_path_warning","active_mode":r.get("active_mode","active_passive"),"failover_test_required":True,"monitoring":True,"decisions":self.decisions}
