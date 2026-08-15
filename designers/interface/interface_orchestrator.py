from designers.interface.common import InterfaceDesigner
from .interface_inventory_builder import InterfaceInventoryBuilder
from .interface_role_classifier import InterfaceRoleClassifier
from .interface_allocator import InterfaceAllocator
from .svi_designer import SVIDesigner
from .loopback_designer import LoopbackDesigner
from .management_interface_designer import ManagementInterfaceDesigner
from .subinterface_designer import SubinterfaceDesigner
from .tunnel_interface_designer import TunnelInterfaceDesigner
from .interface_description_generator import InterfaceDescriptionGenerator
from .interface_capacity_validator import InterfaceCapacityValidator
from .port_mapping_matrix_generator import PortMappingMatrixGenerator
class InterfaceOrchestrator(InterfaceDesigner):
    """Assemble the complete interface assignment artifact in dependency order."""
    def design(self,r):
        inventory=InterfaceInventoryBuilder().design(r);roles=InterfaceRoleClassifier().design(r);allocation=InterfaceAllocator().design({**r,"inventory":inventory["ports"]});mappings=[{"interface_name":a["interface"],"role":a["role"],"status":"allocated"} for a in allocation["allocations"]];descriptions=InterfaceDescriptionGenerator().design({"mappings":mappings});capacity=InterfaceCapacityValidator().design({**r,"inventory":inventory["ports"],"allocations":allocation["allocations"]});matrix=PortMappingMatrixGenerator().design({"mappings":descriptions["mappings"]});self.record_decision("interface_orchestration",["inventory","roles","allocation","svi","loopback","management","subinterface","tunnel","description","capacity","matrix"],"dependency order produces executable interface artifact");return {"inventory":inventory,"roles":roles,"allocation":allocation,"svi":SVIDesigner().design(r),"loopback":LoopbackDesigner().design(r),"management":ManagementInterfaceDesigner().design(r),"subinterfaces":SubinterfaceDesigner().design(r),"tunnels":TunnelInterfaceDesigner().design(r),"descriptions":descriptions,"capacity":capacity,"matrix":matrix,"decisions":self.decisions}
