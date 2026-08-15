from designers.access_control.common import NACDesigner
class DeploymentPhasingPlanner(NACDesigner):
 def design(self,r):
  phases=[{"phase":1,"mode":"monitor","success":"profiling coverage","rollback":"disable enforcement"},{"phase":2,"mode":"low_impact","success":"false_positive rate acceptable","rollback":"return to monitor"},{"phase":3,"mode":"closed","success":"auth success and exception process stable","rollback":"return to low_impact"}];self.record_decision("nac_phasing",phases,"staged rollout protects service continuity");return {"phases":phases,"decisions":self.decisions}
