"""Shared routing helpers and evidence gating."""
from __future__ import annotations
from typing import Any
def evidence_status(evidence_ids:list[str]|None)->str:
    """Return evidence status without asserting unsupported capability."""
    return "evidence_backed" if evidence_ids else "evidence_required"
def policy_value(values:dict[str,Any],key:str,default:Any)->tuple[Any,bool]:
    """Return policy value and whether it was explicitly supplied."""
    return (values[key],True) if key in values else (default,False)
