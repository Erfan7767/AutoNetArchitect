"""Guarded multi-vendor network configuration generation layer."""

from .base_generator import BaseGenerator, DeviceConfig, GenerationResult
from .feature_guards import FeatureGuards, GuardResult
from .template_registry import TemplateRegistry
from .template_renderer import TemplateRenderer, TemplateRenderError
from .template_validator import TemplateValidator
from .template_variable_resolver import TemplateVariableResolver
from .template_composition_engine import TemplateCompositionEngine
from .models import TemplateMetadata, TemplateVariable, TemplateValidationReport, VariableResolution, CompositionResult
from .cisco import IOSXEGenerator, IOSGenerator, NXOSGenerator, WLCGenerator, ASAGenerator
from .fortinet import FortiGateGenerator
from .paloalto import PANOSGenerator
from .huawei import VRPGenerator
from .aruba import AOSCXGenerator
from .juniper import JunosGenerator
from .mikrotik import RouterOSGenerator

__all__ = [
    "BaseGenerator",
    "DeviceConfig",
    "GenerationResult",
    "FeatureGuards",
    "GuardResult",
    "TemplateRegistry",
    "TemplateRenderer",
    "TemplateRenderError",
    "TemplateValidator",
    "TemplateVariableResolver",
    "TemplateCompositionEngine",
    "TemplateMetadata",
    "TemplateVariable",
    "TemplateValidationReport",
    "VariableResolution",
    "CompositionResult",
    "IOSXEGenerator",
    "IOSGenerator",
    "NXOSGenerator",
    "WLCGenerator",
    "ASAGenerator",
    "FortiGateGenerator",
    "PANOSGenerator",
    "VRPGenerator",
    "AOSCXGenerator",
    "JunosGenerator",
    "RouterOSGenerator",
]
