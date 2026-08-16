# Engineer-Supervised Multi-Agent Workflow

## Purpose

AutoNetArchitect can coordinate specialized local and control-plane work, but it does not represent a claim of autonomous engineer equivalence or a guarantee that a deployment will be error-free. Every specialist produces bounded, reviewable evidence. Production device execution remains outside the specialist roles and requires the existing human Go/No-Go process.

## Responsibility Boundary

| Specialist role | Permitted outcome | Mandatory input | Explicit boundary |
|---|---|---|---|
| Authorized discovery | Read-only, secret-free device evidence or a no-guess result | Approved site scope, target, protocol, credential reference | Cannot scan beyond scope or modify a device |
| Evidence review | Classified evidence, ambiguity, and blockers | Discovery result and provenance | Cannot infer a missing platform, version, or license |
| Design preparation | Versioned design artifact and rationale | Reviewed facts and approved requirements | Cannot invent attributes or unchecked commands |
| Capability assessment | Evidenced capability decision or safe refusal | Exact platform, software release, license evidence | Cannot assume compatibility or replace a vendor command |
| Virtual validation | Hash-bound validation result and fidelity label | Artifact, target-facts, and scope hashes | Cannot treat a virtual pass as production proof |
| Safety review | Approval-readiness result and blockers | Validation, backup, maintenance, and capability evidence | Cannot waive controls or self-approve |
| Release coordination | Human review pack and approval reference | Readiness result and named authority | Cannot execute a change or override No-Go |

## Exact Capability Evidence

An observed vendor label or a candidate release note is not capability verification. Before the control plane treats a managed device as capability-verified, it requires three redacted reference identifiers: the exact platform/version/feature assessment, license or entitlement evidence, and documented configuration-path evidence. The references contain no device credentials or secret values.

The assessment remains blocked or review-required if a model is absent, the observed release is only a candidate, a requested feature is unobserved, entitlement is unverified, or the configuration path has no evidence. The current policy data contains candidate release references for the four bounded vendor families, not blanket production authorization.

## Valid Handoff Order

The shared workflow is `scope_confirmed → discovery → evidence_review → design_preparation → capability_assessment → virtual_validation → safety_review → human_go_no_go`. Agents may perform independent **read-only or review work** concurrently only where their inputs are complete and bound to the same approved scope. A later stage may not silently replace an unresolved result from an earlier stage.

> A successful virtual test is evidence for review only. It does not authorize a production upload, replace a backup, satisfy a maintenance window, verify a license, or provide human approval.

## Operating Approaches

| Approach | Trade-offs | Cost | Setup complexity |
|---|---|---:|---:|
| Local supervised coordinator on the Windows engineer workstation | Keeps device access on-site and starts only under the engineer’s selected scope; suited to the present laboratory-only agent boundary | Included with the local application | Moderate: install the local application and register approved scopes |
| Dedicated organization-managed on-premises coordinator | Can serve several approved sites with centrally reviewed enrollment, health, and audit controls; requires a formal operational and security rollout | Infrastructure and operations cost determined by the organization | High: certificate enrollment, network segmentation, monitoring, and incident ownership |

The current implementation follows the first approach. It does not start background scanning, store raw device credentials, or issue production configuration commands.
