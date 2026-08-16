export type VendorSupportStatus = {
  vendorFamily: "cisco" | "huawei" | "fortinet" | "hpe_aruba";
  displayName: string;
  discoveryProtocols: string[];
  configurationStatus: "verification_required";
  versionPolicyStatus: "not_loaded";
  licenseEvidenceRequired: true;
  configurationPathEvidenceRequired: true;
  sourceUrl: string;
  boundary: string;
};

export function filterVendorSupport(items: VendorSupportStatus[], selectedFamily: string): VendorSupportStatus[] {
  return selectedFamily === "all" ? items : items.filter(item => item.vendorFamily === selectedFamily);
}

export const VENDOR_SUPPORT_STATUS: VendorSupportStatus[] = [
  {
    vendorFamily: "cisco",
    displayName: "Cisco",
    discoveryProtocols: ["SSH", "NETCONF", "HTTPS API"],
    configurationStatus: "verification_required",
    versionPolicyStatus: "not_loaded",
    licenseEvidenceRequired: true,
    configurationPathEvidenceRequired: true,
    sourceUrl: "https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/1713/b_1713_programmability_cg/m_1713_prog_yang_netconf.html",
    boundary: "Identity and protocol discovery contracts exist; exact platform/version/license evidence is still required.",
  },
  {
    vendorFamily: "huawei",
    displayName: "Huawei",
    discoveryProtocols: ["SSH", "NETCONF", "HTTPS API"],
    configurationStatus: "verification_required",
    versionPolicyStatus: "not_loaded",
    licenseEvidenceRequired: true,
    configurationPathEvidenceRequired: true,
    sourceUrl: "https://support.huawei.com/enterprise/en/doc/EDOC1100278266/d73bfdce/overview-of-restconf",
    boundary: "Identity and protocol discovery contracts exist; exact platform/version/license evidence is still required.",
  },
  {
    vendorFamily: "fortinet",
    displayName: "Fortinet FortiOS",
    discoveryProtocols: ["SSH", "HTTPS API"],
    configurationStatus: "verification_required",
    versionPolicyStatus: "not_loaded",
    licenseEvidenceRequired: true,
    configurationPathEvidenceRequired: true,
    sourceUrl: "https://docs.fortinet.com/document/fortigate/8.0.0/administration-guide/940602/using-apis",
    boundary: "Identity and protocol discovery contracts exist; exact platform/version/license evidence is still required.",
  },
  {
    vendorFamily: "hpe_aruba",
    displayName: "HPE Aruba AOS-CX",
    discoveryProtocols: ["SSH", "HTTPS API"],
    configurationStatus: "verification_required",
    versionPolicyStatus: "not_loaded",
    licenseEvidenceRequired: true,
    configurationPathEvidenceRequired: true,
    sourceUrl: "https://developer.arubanetworks.com/aoscx/docs/introduction",
    boundary: "Identity and protocol discovery contracts exist; exact platform/version/license evidence is still required.",
  },
];
