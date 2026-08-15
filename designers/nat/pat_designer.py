from designers.nat.common import NATDesigner
class PATDesigner(NATDesigner):
 def design(self,r):
  users=int(r.get("estimated_users",0));sessions=int(r.get("sessions_per_user",20));public_ips=int(r.get("public_ip_count",0));demand=users*sessions;capacity=max(public_ips,1)*64000;util=round(demand/capacity,3) if capacity else 1;status="blocked_missing_human_data" if not r.get("public_ip_count") else "designed";self.record_decision("pat",{"demand":demand,"capacity":capacity},"overload is the default internet access pattern")
  return {"status":status,"estimated_concurrent_sessions":demand,"port_capacity":capacity,"utilization":util,"exhaustion_risk":util>.7,"recommendations":["additional public IPs","connection limiting"] if util>.7 else [],"decisions":self.decisions}
