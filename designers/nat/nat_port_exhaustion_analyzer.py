from designers.nat.common import NATDesigner
class NATPortExhaustionAnalyzer(NATDesigner):
 def design(self,r):
  users=int(r.get("users",0));sessions=int(r.get("sessions_per_user",20));ports=int(r.get("ports_per_session",1));ips=int(r.get("public_ip_count",1));demand=users*sessions*ports;capacity=ips*64000;util=round(demand/capacity,3) if capacity else 1;self.record_decision("port_capacity",{"demand":demand,"capacity":capacity},"port demand is derived only from supplied estimates")
  return {"estimated_users":users,"total_port_demand":demand,"available_ports":capacity,"utilization":util,"risk":util>.7,"recommendations":["additional public IPs","port blocks","connection limiting"] if util>.7 else [],"decisions":self.decisions}
