from designers.mpls.common import MPLSDesigner
class MPLSToSDWANTransition(MPLSDesigner):
    """MPLS design engine."""
    def design(self,r):
        self.record_decision("mpls_to_sdwan",True,"SD-WAN overlay is introduced over MPLS and internet before traffic migration");return {"hybrid_period":True,"transports":["mpls","internet"],"sequence":["pilot","non_critical","critical"],"mpls_backup":True,"decisions":self.decisions}
