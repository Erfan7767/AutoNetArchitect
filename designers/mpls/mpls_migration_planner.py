from designers.mpls.common import MPLSDesigner
class MPLSMigrationPlanner(MPLSDesigner):
    """MPLS design engine."""
    def design(self,r):
        scenario=r.get("scenario","new_mpls");self.record_decision("mpls_migration",scenario,"migration uses parallel run, ordered traffic move, testing, and rollback");return {"scenario":scenario,"parallel_run":True,"sequence":["pilot","non_critical","critical"],"rollback":"restore previous WAN routing","testing":["reachability","failover","QoS","SLA"],"decisions":self.decisions}
