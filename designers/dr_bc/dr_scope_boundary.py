from designers.dr_bc.common import DRDesigner
class DRScopeBoundary(DRDesigner):
    """DR network design engine."""
    def design(self,r):
        in_scope=["network_infrastructure_dr","dr_site_topology","dr_connectivity","dr_routing_failover","dr_activation_testing","network_monitoring","network_runbook","network_compliance"];out_scope=["application_dr","database_replication","storage_replication","organizational_bc","crisis_communication","employee_relocation","physical_security","facility_management","full_iso22301_system"];self.record_decision("dr_scope",in_scope,"designer covers network infrastructure DR, not enterprise BC or application recovery");return {"in_scope":in_scope,"out_of_scope":out_scope,"status":"bounded","decisions":self.decisions}
