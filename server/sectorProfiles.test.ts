import { describe, expect, it } from "vitest";
import { assessSectorProfileInputs, sectorProfiles } from "./sectorProfiles";

describe("sector profiles", () => {
  it("requires human-supplied industrial safety and ownership boundaries", () => {
    const gaps = assessSectorProfileInputs("industrial", ["Process, safety, and availability impact boundaries"]);
    expect(gaps).toContain("OT system owner and equipment-vendor support constraints");
    expect(gaps).toContain("Emergency stop, escalation, and rollback authority");
  });

  it("does not treat a sector profile as an automatic compliance claim", () => {
    expect(sectorProfiles.financial_service_branch.automaticClaimsProhibited).toContain("Financial regulatory compliance");
    expect(sectorProfiles.industrial.automaticClaimsProhibited).toContain("Functional safety assurance");
  });
});
