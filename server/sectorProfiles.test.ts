import { describe, expect, it } from "vitest";
import {
  assessSectorProfileInputs,
  buildSectorReviewSnapshot,
  isSectorReviewCurrent,
  SECTOR_REVIEW_MAX_AGE_MS,
  sectorProfiles,
} from "./sectorProfiles";

describe("sector profiles", () => {
  it("requires human-supplied industrial safety and ownership boundaries", () => {
    const gaps = assessSectorProfileInputs("industrial", ["Process, safety, and availability impact boundaries"]);
    expect(gaps).toContain("OT system owner and equipment-vendor support constraints");
    expect(gaps).toContain("Emergency stop, escalation, and rollback authority");
  });

  it("builds a complete sector snapshot from exact human-supplied labels", () => {
    const snapshot = buildSectorReviewSnapshot("enterprise", sectorProfiles.enterprise.requiredHumanInputs);
    expect(snapshot.completenessPercent).toBe(100);
    expect(snapshot.missingInputs).toEqual([]);
    expect(snapshot.mandatoryReviewRoles).toContain("change approver");
  });

  it("marks missing, stale, and future reviews as not current", () => {
    const now = new Date("2026-08-16T00:00:00.000Z");
    expect(isSectorReviewCurrent(undefined, now)).toBe(false);
    expect(isSectorReviewCurrent(new Date(now.getTime() - SECTOR_REVIEW_MAX_AGE_MS - 1), now)).toBe(false);
    expect(isSectorReviewCurrent(new Date(now.getTime() + 1), now)).toBe(false);
    expect(isSectorReviewCurrent(new Date(now.getTime() - 1), now)).toBe(true);
  });

  it("does not treat a sector profile as an automatic compliance claim", () => {
    expect(sectorProfiles.financial_service_branch.automaticClaimsProhibited).toContain("Financial regulatory compliance");
    expect(sectorProfiles.industrial.automaticClaimsProhibited).toContain("Functional safety assurance");
  });
});
