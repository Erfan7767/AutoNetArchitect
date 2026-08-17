# Laboratory-Only Validation Runbook

## Purpose and boundary

This runbook governs **isolated validation laboratories** used to evaluate a versioned configuration artifact against a selected virtual or physical-lab topology. It does not authorize production discovery, configuration upload, rollback, or any device action. A passed laboratory result is evidence for later human review; it is not a Go decision.

| Control | Required behavior | Prohibited behavior |
|---|---|---|
| Scope | Use a recorded artifact hash, target-facts hash, and authorized scope hash. | Reuse a result after any of these values change. |
| Environment | Use a segregated lab provider, tenant, or physically isolated lab equipment. | Point a lab adapter at a customer production device or management network. |
| Evidence | Preserve adapter kind, fidelity, timestamp, observations, and approved golden comparison. | Claim protocol fidelity that the external lab has not evidenced. |
| Decision | Present result to the named human reviewer with limitations and unresolved items. | Treat a passed result as approval or automatic execution authority. |

## Preconditions

The responsible engineer must verify that the project contains a human-approved discovery scope, an observed or explicitly unresolved device-facts record, a hash-bound configuration artifact, and a lab environment authorization. The configuration material must be scrubbed of inline secrets. References to an approved external secret manager are acceptable, but secret values must not be copied into the lab record or its logs.

## Procedure

1. Select the validation path and record its fidelity. Use `vendor_image_lab` or `physical_lab` only where the actual lab evidence supports that label; retain `logical_intent_only` for a logical model.
2. Verify that the artifact hash, target-facts hash, and scope hash exactly match the proposed change context. Stop if any field is absent or differs.
3. Deploy only the approved topology to the isolated lab provider. The provider operation must remain marked `validation_only=true` and `production_change_control_required=true`.
4. Apply the redacted, versioned configuration artifact to the lab target. Stop if inline secrets, unbound artifacts, or unapproved topology elements are encountered.
5. Run the agreed verification checks and compare observations to an approved golden output. Record mismatches, missing observations, and unexpected observations explicitly.
6. Record the external lab result as a hash-bound virtual-test evidence record. State adapter, fidelity, evidence reference, limitations, and result state.
7. Submit the evidence to human review. A separate change-plan gate still requires current evidence, maintenance policy, backup verification, and named human Go/No-Go approval.

## Failure handling

If the lab result is failed, inconclusive, stale, scope-mismatched, or unsupported, mark the path blocked and retain the evidence. Do not retry against production equipment. The engineer may correct an artifact or supply new evidence, then begin a new lab run with a new hash-bound record.

## Exit criteria

A lab run is complete when its observations, comparison status, hashes, fidelity label, and limitations are recorded. It never changes the production release state directly. Production execution remains unavailable in this control plane and must remain a separate, human-controlled external activity.
