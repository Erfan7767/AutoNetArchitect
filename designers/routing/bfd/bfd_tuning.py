from designers.base_designer import BaseDesigner
class BFDTuning(BaseDesigner):
 def design(self,requirements):
  profile=requirements.get("link_profile","physical");values={"physical":(50,50,3),"logical":(300,300,5)}.get(profile);self.record_decision("bfd_tuning",values,"aggressive physical and conservative logical policy")
  return {"profile":profile,"values":values,"decisions":self.decisions}
