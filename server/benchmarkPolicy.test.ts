import { describe, expect, it } from "vitest";
import { assessBenchmarkCoverage, type BenchmarkScenario } from "./benchmarkPolicy";

const measuredScenario: BenchmarkScenario = {
  scenarioId: "bank-cisco-iosxe-17-9-lab-001",
  vendorFamily: "cisco",
  platform: "ios_xe",
  model: "C9300-48P",
  softwareVersion: "17.9.4",
  licenseEvidenceReference: "license-evidence-001",
  configurationPathReference: "candidate-commit-path-001",
  sectorProfile: "financial_service_branch",
  measuredRuns: 3,
  acceptedRuns: 2,
  rejectedRuns: 1,
  minimumAcceptanceRatePercent: 60,
  acceptanceCriteriaReference: "approved-acceptance-criteria-001",
  evidenceReference: "lab-evidence-001",
  reviewedAt: new Date(),
};

describe("assessBenchmarkCoverage", () => {
  it("marks a fully scoped and reconciled scenario as measured coverage", () => {
    expect(assessBenchmarkCoverage(measuredScenario)).toEqual({ status: "measured_coverage", blockers: [] });
  });

  it("blocks a vendor-family claim when exact version and measured evidence are absent", () => {
    const result = assessBenchmarkCoverage({ ...measuredScenario, softwareVersion: "", measuredRuns: 0, acceptedRuns: 0, rejectedRuns: 0, evidenceReference: "" });
    expect(result.status).toBe("outside_measured_coverage");
    expect(result.blockers).toContain("Exact platform, model, and software version are required.");
    expect(result.blockers).toContain("At least one measured scenario run is required.");
  });

  it("blocks inconsistent measured outcomes rather than calculating a claim", () => {
    const result = assessBenchmarkCoverage({ ...measuredScenario, measuredRuns: 2, acceptedRuns: 2, rejectedRuns: 1 });
    expect(result.status).toBe("outside_measured_coverage");
    expect(result.blockers).toContain("Measured outcome totals must reconcile to the recorded run count.");
  });

  it("blocks a scenario that does not meet its recorded acceptance criterion", () => {
    const result = assessBenchmarkCoverage({ ...measuredScenario, minimumAcceptanceRatePercent: 80 });
    expect(result.status).toBe("outside_measured_coverage");
    expect(result.blockers).toContain("Measured acceptance does not meet the recorded minimum acceptance rate.");
  });

  it("blocks a scenario without a human-supplied acceptance-criteria reference", () => {
    const result = assessBenchmarkCoverage({ ...measuredScenario, acceptanceCriteriaReference: "" });
    expect(result.status).toBe("outside_measured_coverage");
    expect(result.blockers).toContain("An acceptance-criteria reference is required.");
  });
});
