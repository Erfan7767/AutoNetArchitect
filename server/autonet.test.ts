import { describe, expect, it } from "vitest";
import { calculateQuestionnaireCompleteness, getDeploymentGate, getSectorPlanBlocker, redactAuditDetails, requiresUnsupportedFeatureAudit } from "./autonet";

describe("AutoNetArchitect governance helpers", () => {
  it("calculates questionnaire completeness from supplied project requirements", () => {
    expect(
      calculateQuestionnaireCompleteness({
        organization: "Northwind",
        organizationType: "Enterprise",
        siteCount: 2,
        classification: "brownfield",
        vendorPreferences: "Cisco",
        complianceNeeds: "ISO 27001",
      }),
    ).toBe(100);
  });

  it("does not count unspecified fields as complete", () => {
    expect(
      calculateQuestionnaireCompleteness({
        organization: "",
        organizationType: "",
        siteCount: 0,
        classification: "undetermined",
        vendorPreferences: "",
        complianceNeeds: "",
      }),
    ).toBe(0);
  });

  it("redacts sensitive audit detail instead of returning the supplied value", () => {
    expect(redactAuditDetails("api key: value-that-must-not-be-shown")).toBe(
      "Sensitive details were redacted.",
    );
  });

  it("keeps the deployment gate closed until requirements and approval are both present", () => {
    expect(getDeploymentGate({ requirementsComplete: 75, approvalState: "approved" })).toBe("no_go");
    expect(getDeploymentGate({ requirementsComplete: 100, approvalState: "pending" })).toBe("review_required");
    expect(getDeploymentGate({ requirementsComplete: 100, approvalState: "approved" })).toBe("go");
  });

  it("requires a dedicated audit event for blocked or explicitly unsupported config features", () => {
    expect(requiresUnsupportedFeatureAudit({ featureGuard: "blocked", unsupportedFeatureLog: "" })).toBe(true);
    expect(requiresUnsupportedFeatureAudit({ featureGuard: "pass", unsupportedFeatureLog: "Needs vendor capability evidence" })).toBe(true);
    expect(requiresUnsupportedFeatureAudit({ featureGuard: "pass", unsupportedFeatureLog: "" })).toBe(false);
  });

  it("blocks change-plan creation until the selected sector profile has every required human input", () => {
    expect(getSectorPlanBlocker("unselected", [])).toContain("sector profile must be selected");
    expect(getSectorPlanBlocker("industrial", ["Process, safety, and availability impact boundaries"])).toContain("Sector profile is incomplete");
    expect(getSectorPlanBlocker("enterprise", [
      "Business-service priorities and outage impact",
      "Site and management-network boundaries",
      "Identity, segmentation, and internet-edge policy",
      "Supported hardware, software, license, and support evidence",
      "Change authority and maintenance policy",
    ])).toBeNull();
  });
});
