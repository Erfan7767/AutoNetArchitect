# AutoNetArchitect V1 Security Guide

## Security posture

AutoNetArchitect V1 applies defense-in-depth controls around local state, authentication, authorization, secrets, auditability, generated artifacts, and deployment gates. The controls are engineering safeguards and a documented baseline; they are not a claim that any installation is secure against every threat or compliant with a particular regulation.

The security model assumes a trusted local administrator, a protected host, controlled access to the state root, and human ownership of network change decisions. V1 does not provide multi-tenant isolation, a hosted identity provider, a distributed policy plane, or a complete enterprise SOC integration.

## Secret handling

Secrets are managed through the SecretManager and local vault boundary. Components should consume secret references and metadata, not raw secret values. The secure logging and redaction layer is mandatory for logs that may contain device output, exception text, audit details, or generated artifacts.

The following values must never appear in reports, exports, audit details, CLI output, API responses, release archives, or test fixtures:

- passwords and password hashes;
- private keys and certificate private material;
- API tokens, session signing keys, and bearer tokens;
- SNMP communities and device enable secrets;
- vault encryption keys;
- raw secret values embedded in configuration or command output.

A secret reference such as `secret://device/router-01/enable` is metadata and may be retained when needed for traceability. It must not be resolved during export. `.env.example` contains names and non-secret local defaults only; it is not a credential template.

## Local vault and state root

The local vault is the V1 storage boundary for secret material. Protect its filesystem permissions, encryption key lifecycle, backups, and restore process. The API signing key and sessions live under `AUTONET_API_ROOT`; the CLI has its own default root. Do not merge or share roots casually between installations.

State backups must be encrypted, access-controlled, integrity-checked, and restoration-tested. A checksum validates the stored artifact; it does not prove that the host, filesystem, backup operator, or restored environment is trustworthy.

## Authentication and RBAC

V1 authentication is local. Sessions are issued after credential verification and carry explicit expiry and revocation state. RBAC permissions are checked at the service or route boundary. Typical permissions distinguish project read/write, audit read, design, configuration generation, deployment preview, deployment execution, operations, and administration.

Authentication is not approval. A user may be authenticated and authorized to request an action while still lacking the governance approval required for that action. The deployment and review-control layers must enforce both.

## Audit and accountability

Audit records capture actor identity, action type, project/workflow scope, timestamp, outcome, references, and redacted details. Secret values are excluded. Audit events are evidence of the application's recorded activity; they are not proof that an external network accepted or completed a change.

Human accountability is explicit. Review, approval, execution authority, and escalation are separate concepts. Separation-of-duties policies may require distinct actors. Overrides record rationale, scope, impact, decision owner, time, and whether revalidation is required.

## Generated configuration and exports

Configuration generators are capability-gated and vendor-aware. They may produce unsupported-feature records or abstain; they must not substitute a plausible command when exact support is unknown. Generated configurations contain references where secrets are needed. Exports and reports must be redacted and must declare their SoT basis and generation timestamp.

Do not paste generated configuration into an uncontrolled ticket, chat, or public repository. Treat device configuration, topology details, public addresses, authentication metadata, and audit exports as sensitive operational information even when they are not classified as secrets.

## Deployment boundaries

V1 distinguishes dry-run, lab validation, deployment preparation, and real execution. Real execution requires policy gates, resolved human-mandatory inputs, required review and approval, backup evidence, verification planning, and rollback scope. High-risk or remote-destructive operations must be blocked when the policy does not explicitly allow them.

Firmware operations require exact supported model/version paths, integrity evidence, maintenance window, approval, and staged handling. Monitoring and discovery are read-only by default. High-risk drift is not auto-remediated in V1 without approval.

## Compliance boundary

The compliance layer maps technical controls to design, configuration, operational, or other declared evidence. It is an assessment aid. It does not issue certification, legal advice, audit attestation, or organizational readiness. A report must state the framework, scope, evidence basis, limitations, and unresolved items.

## Container baseline

The Docker baseline uses a non-root user, a read-only root filesystem, a dedicated writable data volume, dropped capabilities, and `no-new-privileges`. Compose binds the API port to localhost by default. These settings reduce exposure but do not replace host hardening, image provenance, patch management, TLS, network controls, or monitoring.

## Incident response and reporting

If a secret is exposed, revoke or rotate it through the responsible secret or PKI process, preserve relevant redacted audit evidence, and follow the organization's incident procedure. Do not commit the exposed value to a remediation branch. If a security defect is found in the project, report it privately to the project maintainer with reproduction steps, affected version, impact, and a safe contact path; do not publish exploit details before coordinated handling.

## Multi-stage image boundary

The release image separates native build tooling from the runtime image. `gcc` and `libffi-dev` exist only in the builder stage; the runtime stage installs `graphviz` as the explicitly declared native dependency for supported diagram/report paths. The application process runs as the dedicated non-root `autonet` user with UID/GID 10001, and local mutable state is limited to the declared `/var/lib/autonetarchitect` volume plus application-owned directories.

The default `python -m uvicorn api.server:app` command serves the local API. The liveness healthcheck verifies that the process responds at `/api/v1/health/live`; it does not prove authentication configuration, state integrity beyond the route's contract, host security, TLS, organizational monitoring, or network-device readiness. The image does not contain device credentials and does not authorize production network changes.

## Compose UI service boundary

The optional Compose UI service is built with the `optional` dependency extra so Streamlit and rendering integrations do not enter the default API image dependency set. Its adapter calls only the public API liveness route for a read-only status shell. It does not receive device credentials, resolve secret references, execute orchestrators directly, or create an alternative persistence root.

Both Compose services bind to loopback by default, use read-only root filesystems, drop all Linux capabilities, enable `no-new-privileges`, and use temporary `/tmp` storage where framework runtime writes are needed. These controls reduce local exposure but do not provide TLS, tenant isolation, hosted identity, image signing, host hardening, or a production network-change authorization mechanism.
