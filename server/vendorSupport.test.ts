import { describe, expect, it } from "vitest";
import { filterVendorSupport, VENDOR_SUPPORT_STATUS } from "../shared/vendorSupport";

describe("vendor support review contract", () => {
  it("exposes four bounded families with configuration blocked", () => {
    expect(VENDOR_SUPPORT_STATUS).toHaveLength(4);
    expect(VENDOR_SUPPORT_STATUS.every(item => item.configurationStatus === "verification_required")).toBe(true);
    expect(VENDOR_SUPPORT_STATUS.every(item => item.versionPolicyStatus === "not_loaded")).toBe(true);
  });

  it("filters the review surface to the selected family", () => {
    const selected = filterVendorSupport(VENDOR_SUPPORT_STATUS, "fortinet");
    expect(selected).toHaveLength(1);
    expect(selected[0]?.displayName).toBe("Fortinet FortiOS");
    expect(selected[0]?.licenseEvidenceRequired).toBe(true);
  });
});
