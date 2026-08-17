"""Pinned public-key trust material for concrete local-agent mutual authentication."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field, field_validator


def public_key_fingerprint(public_key_pem: str) -> str:
    """Return the SHA-256 fingerprint of a PEM public key without loading any private material."""

    return hashlib.sha256(public_key_pem.encode("utf-8")).hexdigest()


class TrustedPublicKey(BaseModel):
    """One pinned Ed25519 public key whose declared fingerprint must match its PEM bytes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fingerprint: str = Field(min_length=64, max_length=64)
    public_key_pem: str = Field(min_length=32, max_length=4096)

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_format(cls, value: str) -> str:
        """Require a normalized SHA-256 hexadecimal fingerprint."""

        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("Pinned public-key fingerprint must be a lowercase SHA-256 hexadecimal value.")
        return value

    def verify_fingerprint(self) -> None:
        """Fail closed if public key bytes do not match the pinned fingerprint."""

        if public_key_fingerprint(self.public_key_pem) != self.fingerprint:
            raise ValueError("Pinned public-key fingerprint does not match the supplied PEM public key.")
        try:
            loaded = serialization.load_pem_public_key(self.public_key_pem.encode("utf-8"))
        except (TypeError, ValueError) as error:
            raise ValueError("Pinned public key is not valid PEM.") from error
        if not isinstance(loaded, Ed25519PublicKey):
            raise ValueError("Pinned public key must use Ed25519 for this enrollment flow.")


class TrustedAgentPublicKey(TrustedPublicKey):
    """Pinned public key assigned to exactly one local agent identity."""

    agent_id: str = Field(min_length=3, max_length=160)


class PinnedTrustStore(BaseModel):
    """Secret-free trust store containing one control-plane key and provisioned local agent keys."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    control_plane: TrustedPublicKey
    agents: tuple[TrustedAgentPublicKey, ...] = Field(min_length=1)

    def validate(self) -> None:
        """Verify key formats, fingerprints, and unique provisioned agent identities."""

        self.control_plane.verify_fingerprint()
        agent_ids: set[str] = set()
        fingerprints: set[str] = {self.control_plane.fingerprint}
        for agent in self.agents:
            agent.verify_fingerprint()
            if agent.agent_id in agent_ids or agent.fingerprint in fingerprints:
                raise ValueError("Pinned trust store contains duplicate agent identity or public-key fingerprint.")
            agent_ids.add(agent.agent_id)
            fingerprints.add(agent.fingerprint)

    def key_for(self, fingerprint: str) -> TrustedPublicKey | None:
        """Return a pinned public key only when its fingerprint is provisioned."""

        if self.control_plane.fingerprint == fingerprint:
            return self.control_plane
        return next((agent for agent in self.agents if agent.fingerprint == fingerprint), None)

    def agent_for(self, agent_id: str) -> TrustedAgentPublicKey | None:
        """Return the pre-provisioned key bound to the local agent identifier."""

        return next((agent for agent in self.agents if agent.agent_id == agent_id), None)


class Ed25519PinnedSignatureVerifier:
    """Concrete verifier that accepts only proofs made by a key in the pinned trust store."""

    def __init__(self, trust_store: PinnedTrustStore) -> None:
        """Validate trust material before it can verify any enrollment proof."""

        trust_store.validate()
        self._trust_store = trust_store

    def verify(self, fingerprint: str, payload: bytes, proof: str) -> bool:
        """Verify base64 Ed25519 proof bytes against the exact canonical payload."""

        trusted = self._trust_store.key_for(fingerprint)
        if trusted is None:
            return False
        try:
            public_key = serialization.load_pem_public_key(trusted.public_key_pem.encode("utf-8"))
            signature = base64.b64decode(proof.encode("ascii"), validate=True)
            if not isinstance(public_key, Ed25519PublicKey):
                return False
            public_key.verify(signature, payload)
        except (InvalidSignature, TypeError, ValueError):
            return False
        return True


def load_pinned_trust_store(path: Path) -> PinnedTrustStore:
    """Load and validate a secret-free JSON trust store from an administrator-controlled location."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"Pinned trust store cannot be read: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Pinned trust store is not valid JSON: {error.msg}") from error
    trust_store = PinnedTrustStore.model_validate(payload)
    trust_store.validate()
    return trust_store
