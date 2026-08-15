from designers.access_control.common import NACDesigner
class NACMonitoringDesigner(NACDesigner):
 def design(self,r):
  metrics=["auth_success_failure","mab_ratio","radius_response_time","coa_success","quarantine_population","exception_count"];self.record_decision("nac_monitoring",metrics,"monitoring covers authentication, infrastructure, and exception health");return {"metrics":metrics,"alerts":["auth_failure_spike","radius_unreachable","quarantine_spike"],"decisions":self.decisions}
