from designers.cloud.common import CloudDesigner
class CloudScopeBoundary(CloudDesigner):
    """Cloud connectivity design engine."""
    def design(self,r):
        in_scope=["onprem_to_cloud_connectivity","vpn","dedicated_connectivity","hybrid_dns","hybrid_routing","onprem_edge_security"];out_scope=["cloud_vpc_vnet_internal_design","cloud_security_groups","cloud_load_balancers","cloud_internal_dns_zones","cloud_network_automation","cloud_cost_optimization"];self.record_decision("cloud_scope",in_scope,"V1 designs connectivity to cloud, not internal cloud-native networking");return {"in_scope":in_scope,"out_of_scope":out_scope,"status":"bounded","human_supplied_for_out_scope":True,"decisions":self.decisions}
