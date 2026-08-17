"""Human-written authorization record required before a local laboratory validation path is usable."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class LaboratoryEnvironmentClass(str, Enum):
    """Allowed non-production laboratory environment classes."""

    ISOLATED_SIMULATION = "isolated_simulation"
    VENDOR_IMAGE_LAB = "vendor_image_lab"
    PHYSICAL_LAB = "physical_lab"


class LaboratoryAuthorization(BaseModel):
    """A secret-free written human authorization for one bounded, non-production lab environment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    authorization_reference: str = Field(min_length=3, max_length=300)
    human_authorizer: str = Field(min_length=2, max_length=160)
    scope_hash: str = Field(min_length=8, max_length=160)
    environment_reference: str = Field(min_length=3, max_length=300)
    environment_class: LaboratoryEnvironmentClass
    approved_at: datetime
    expires_at: datetime

    def active_for(self, scope_hash: str, now: datetime | None = None) -> bool:
        """Return true only while written authorization is current and hash-bound to the local scope."""

        current = now or datetime.now(timezone.utc)
        return self.scope_hash == scope_hash and self.approved_at <= current < self.expires_at
