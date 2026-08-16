# Initial Vendor Support Sources

## Scope

The initial AutoNetArchitect vendor scope is limited to Cisco, Huawei, Fortinet, and HPE Aruba. These references document management-interface concepts only; they do not establish compatibility for every model, release, license, or feature.

## Cisco IOS XE

Cisco documents NETCONF over SSH, YANG models, capability discovery, and model-based operations for IOS XE. The workflow must match observed platform, release, capabilities, and model evidence.

Source: [Cisco IOS XE 17.13 NETCONF documentation](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/1713/b_1713_programmability_cg/m_1713_prog_yang_netconf.html)

## Huawei VRP / CloudEngine

Huawei documents RESTCONF and NETCONF as separate management paths. The workflow must be tied to the exact product family and software release; behavior must not be generalized across all Huawei products.

Source: [Huawei CloudEngine RESTCONF documentation](https://support.huawei.com/enterprise/en/doc/EDOC1100278266/d73bfdce/overview-of-restconf)

## Fortinet FortiGate / FortiOS

Fortinet documents token-based API access, least-privilege API administrators, trusted hosts, and token handling. Tokens remain local secret-manager references and never enter source, artifacts, logs, or audit details.

Source: [Fortinet FortiOS API documentation](https://docs.fortinet.com/document/fortigate/8.0.0/administration-guide/940602/using-apis)

## HPE Aruba AOS-CX

HPE Aruba documents AOS-CX REST API access, read-only versus read-write modes, HTTPS VRF enablement, session handling, and CSRF requirements for supported releases. The exact release and API mode must be verified before selecting a workflow.

Source: [HPE Aruba AOS-CX REST API documentation](https://developer.arubanetworks.com/aoscx/docs/introduction)

## Support policy

These sources are authority references for interface concepts, not blanket compatibility claims. Devices without observed vendor family, model, software version, license, management interface, and required feature evidence are marked unsupported or require review. The system refuses to synthesize commands or declare production readiness from vendor name alone.

Last reviewed: 2026-08-16
