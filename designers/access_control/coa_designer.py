from designers.access_control.common import NACDesigner
class COADesigner(NACDesigner):
 def design(self,r):
  actions=r.get("actions",["port_bounce","reauthenticate","session_termination","vlan_change","acl_change"]);self.record_decision("coa",actions,"RFC 5176 CoA actions are capability-gated")
  return {"port":3799,"actions":actions,"status":self.evidence(r),"posture_linked":bool(r.get("posture_enabled")),"decisions":self.decisions}
