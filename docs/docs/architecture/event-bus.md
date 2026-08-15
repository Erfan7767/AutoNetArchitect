# Event bus and workflow events

Workflow events communicate state changes between orchestration and reporting boundaries. An event should identify the event type, project and workflow identifiers, stage, actor, timestamp, outcome, SoT domain, evidence references, and a redacted payload. Consumers must treat event payloads as data and must not infer a production approval from an informational event.

## Event rules

Events that represent review, approval, no-go, deployment preparation, execution, rollback, verification, override, or compliance assessment must retain their human and audit references. Event handling should be idempotent by event identifier and should preserve ordering metadata when a consumer needs temporal reconstruction.

Secret values, private keys, bearer tokens, session signing keys, device passwords, and raw credentials are prohibited in event payloads. Use secret references or metadata where traceability requires it. Redaction happens before an event reaches logs, artifacts, reports, or external sinks.

The event bus is not a command bus for uncontrolled network changes. A deployment event records a governed attempt or result; the deployment orchestrator remains the only boundary that can authorize the next legal action.
