"""Platform-agnostic QoS baseline."""
from designers.base_designer import BaseDesigner
class QoSDesigner(BaseDesigner):
    """Map application classes to platform-neutral treatment."""
    def design(self,requirements):
        classes=requirements.get("classes",[{"name":"voice","priority":"high"},{"name":"business","priority":"normal"},{"name":"bulk","priority":"low"}]);self.record_decision("qos_classes",classes,"platform-agnostic service classes")
        return {"classes":classes,"platform":"agnostic","decisions":self.decisions,"assumptions":self.assumptions}
