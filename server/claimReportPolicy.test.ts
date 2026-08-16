import { describe, expect, it } from "vitest";
import { buildRestrictedClaimReport } from "./claimReportPolicy";

describe("buildRestrictedClaimReport", () => {
  it("blocks every restricted class when no scoped evidence is supplied", () => {
    const report = buildRestrictedClaimReport([]);

    expect(report.map(item => item.claimClass)).toEqual(["engineer_equivalence", "production_safe", "compatibility", "compliance"]);
    expect(report.every(item => item.status === "blocked")).toBe(true);
    expect(report.every(item => item.blockers[0] === "No scoped evidence record has been supplied for this restricted claim class.")).toBe(true);
  });

  it("keeps a complete assessment scoped to its own claim class", () => {
    const report = buildRestrictedClaimReport([{
      claimClass: "compatibility",
      scopeDescription: "Exact laboratory scenario only.",
      authorityReference: "Official source reference.",
      measuredEvidenceReference: "Measured scenario evidence.",
      reviewedAt: new Date(),
    }]);

    expect(report.find(item => item.claimClass === "compatibility")).toMatchObject({ status: "publishable", blockers: [] });
    expect(report.find(item => item.claimClass === "production_safe")?.status).toBe("blocked");
  });
});
