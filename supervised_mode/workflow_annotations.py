"""Annotations for supervised workflow-aware orchestrators."""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .workflow_mode import WorkflowStage


CallableT = TypeVar("CallableT", bound=Callable[..., Any])


class WorkflowAnnotation(BaseModel):
    """Metadata attached to an orchestrator callable."""

    model_config = ConfigDict(extra="forbid")

    workflow_name: str = Field(min_length=1)
    workflow_stage: WorkflowStage
    checkpoint_ids: tuple[str, ...] = ()
    mutating: bool = False
    high_assurance: bool = True
    description: str = ""


def supervised_workflow(annotation: WorkflowAnnotation) -> Callable[[CallableT], CallableT]:
    """Decorate a callable with a discoverable supervised workflow annotation."""
    def decorator(function: CallableT) -> CallableT:
        """Attach the annotation while preserving the wrapped callable."""
        @wraps(function)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            """Invoke the original callable; gates remain an orchestrator responsibility."""
            return function(*args, **kwargs)
        setattr(wrapped, "__supervised_annotation__", annotation)
        return cast(CallableT, wrapped)
    return decorator


class WorkflowAnnotationRegistry(BaseDesigner):
    """Registry for workflow annotations used by discovery and reporting."""

    def __init__(self) -> None:
        """Initialize an empty annotation registry."""
        super().__init__("WorkflowAnnotationRegistry")
        self._annotations: dict[str, WorkflowAnnotation] = {}
        self.record_decision("annotation_policy", "explicit_stage_and_checkpoint_metadata", "workflow annotations do not grant authority; they identify required supervision policy")

    def register(self, annotation: WorkflowAnnotation) -> WorkflowAnnotation:
        """Register an annotation by workflow name."""
        self._annotations[annotation.workflow_name] = annotation
        self.record_decision(f"annotation:{annotation.workflow_name}", annotation.workflow_stage.value, "workflow annotation was explicitly registered")
        return annotation

    def discover(self, function: Callable[..., Any]) -> WorkflowAnnotation | None:
        """Read annotation metadata from a decorated callable."""
        value = getattr(function, "__supervised_annotation__", None)
        return value if isinstance(value, WorkflowAnnotation) else None

    def all(self) -> tuple[WorkflowAnnotation, ...]:
        """Return annotations in stable workflow order."""
        return tuple(self._annotations[key] for key in sorted(self._annotations))
