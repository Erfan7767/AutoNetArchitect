# Windows Agent V1 Release Scope

The Windows application is a **single-user local shell** for authorized discovery preparation, evidence review, and supervised validation planning. It is not an unattended network controller and does not claim universal vendor, model, software-version, or license compatibility.

The local workspace may hold non-secret project state and redacted evidence references. Device credentials are consumed through protected secret references and must not be written to the workspace, logs, audit details, or exported artifacts. The workspace is not a replacement for enterprise endpoint management, backup, or access-control systems.

Discovery starts only after the operator records explicit scope consent, including the approved targets or CIDRs and permitted read-only protocols. Read-only discovery is the default. A missing, ambiguous, unsupported, or unauthorized device fact is retained as an unresolved or abstained result; it is never converted into a guessed platform or command.

An unsigned package is installable only as a clearly warned development or laboratory artifact. Unknown package trust is not presented as signed. V1 package status does not constitute code-signing assurance, endpoint-security approval, or production deployment authorization.

The desktop shell remains laboratory- and review-oriented. Production changes require the hosted control-plane gates, exact device capability evidence, current virtual validation, backup verification, maintenance-window validation, human approval, audit recording, and a separate execution path. The Windows release-scope contract therefore reports `production_device_execution = false`.
