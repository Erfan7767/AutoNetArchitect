from designers.mpls.common import MPLSDesigner
class MPLSScopeBoundary(MPLSDesigner):
    """MPLS design engine."""
    def design(self,r):
        in_scope=["ce_router_configuration","ce_pe_routing","ce_qos_mapping","ce_redundancy","circuit_tracking"];out_scope=["pe_configuration","p_router_configuration","mpls_core_design","sp_vrf_route_targets","sp_traffic_engineering"];self.record_decision("mpls_scope",in_scope,"V1 is CE-side and service-boundary only");return {"in_scope":in_scope,"out_of_scope":out_scope,"status":"bounded","sp_side_configuration":"out_of_scope","human_supplied_sp_details":True,"decisions":self.decisions}
