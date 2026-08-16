/**
 * Measured-coverage release policy. It intentionally does not infer support
 * from a vendor family, a candidate release, or a single successful workflow.
 */
export type BenchmarkScenario = {
  scenarioId: string;
  vendorFamily: "cisco" | "huawei" | "fortinet" | "hpe_aruba";
  platform: string;
  model: string;
  softwareVersion: string;
  licenseEvidenceReference: string;
  configurationPathReference: string;
  sectorProfile: "enterprise" | "financial_service_branch" | "retail_transaction_branch" | "industrial";
  measuredRuns: number;
  acceptedRuns: number;
  rejectedRuns: number;
  minimumAcceptanceRatePercent: number;
  acceptanceCriteriaReference: string;
  evidenceReference: string;
  reviewedAt: Date | null;
};

export type BenchmarkCoverageDecision = {
  status: "measured_coverage" | "outside_measured_coverage";
  blockers: string[];
};

/**
 * Checks whether a scenario has its own measured, reviewed evidence record.
 * It returns no performance claim or universal compatibility conclusion.
 */
export function assessBenchmarkCoverage(scenario: BenchmarkScenario): BenchmarkCoverageDecision {
  const blockers: string[] = [];
  if (!scenario.scenarioId.trim()) blockers.push("A scenario identifier is required.");
  if (!scenario.platform.trim() || !scenario.model?.trim() || !scenario.softwareVersion.trim()) blockers.push("Exact platform, model, and software version are required.");
  if (!scenario.licenseEvidenceReference.trim()) blockers.push("License evidence is required.");
  if (!scenario.configurationPathReference.trim()) blockers.push("A configuration-path reference is required.");
  if (scenario.measuredRuns <= 0) blockers.push("At least one measured scenario run is required.");
  if (scenario.acceptedRuns + scenario.rejectedRuns !== scenario.measuredRuns) blockers.push("Measured outcome totals must reconcile to the recorded run count.");
  if (!Number.isInteger(scenario.minimumAcceptanceRatePercent) || scenario.minimumAcceptanceRatePercent < 0 || scenario.minimumAcceptanceRatePercent > 100) blockers.push("A minimum acceptance rate from 0 to 100 percent is required.");
  if (!scenario.acceptanceCriteriaReference.trim()) blockers.push("An acceptance-criteria reference is required.");
  if (scenario.measuredRuns > 0 && scenario.acceptedRuns * 100 < scenario.measuredRuns * scenario.minimumAcceptanceRatePercent) blockers.push("Measured acceptance does not meet the recorded minimum acceptance rate.");
  if (!scenario.evidenceReference.trim()) blockers.push("A measured-evidence reference is required.");
  if (!scenario.reviewedAt) blockers.push("A review timestamp is required.");
  return blockers.length === 0 ? { status: "measured_coverage", blockers: [] } : { status: "outside_measured_coverage", blockers };
}
