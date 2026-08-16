/** Supported business-context profiles. A profile never substitutes for verified site facts. */
export type SectorProfileId = "enterprise" | "financial_service_branch" | "retail_transaction_branch" | "industrial";

/** Profile definition used to drive questionnaire and release completeness controls. */
export type SectorProfile = {
  id: SectorProfileId;
  label: string;
  description: string;
  requiredHumanInputs: string[];
  mandatoryReviewRoles: string[];
  automaticClaimsProhibited: string[];
};

/**
 * Sector requirements intentionally remain qualitative until a responsible human
 * supplies site-specific facts, policy, and evidence. They are not regulatory certifications.
 */
export const sectorProfiles: Record<SectorProfileId, SectorProfile> = {
  enterprise: {
    id: "enterprise",
    label: "Enterprise / corporate network",
    description: "A multi-role business network requiring declared service, identity, resilience, and lifecycle objectives.",
    requiredHumanInputs: [
      "Business-service priorities and outage impact",
      "Site and management-network boundaries",
      "Identity, segmentation, and internet-edge policy",
      "Supported hardware, software, license, and support evidence",
      "Change authority and maintenance policy",
    ],
    mandatoryReviewRoles: ["network owner", "security reviewer", "change approver"],
    automaticClaimsProhibited: ["Universal enterprise architecture suitability", "Production readiness without scoped verification"],
  },
  financial_service_branch: {
    id: "financial_service_branch",
    label: "Financial-service branch",
    description: "A branch profile requiring human-declared transaction-service boundaries, third-party connectivity, resilience needs, and audit responsibilities.",
    requiredHumanInputs: [
      "Transaction-service and customer-impact boundaries",
      "Third-party, WAN, and payment-system ownership boundaries",
      "Approved security and audit control scope",
      "Business continuity, rollback, and incident escalation policy",
      "Authorized device inventory and software evidence",
    ],
    mandatoryReviewRoles: ["network owner", "security reviewer", "business service owner", "change approver"],
    automaticClaimsProhibited: ["Financial regulatory compliance", "Payment-system compliance", "Transaction availability guarantee"],
  },
  retail_transaction_branch: {
    id: "retail_transaction_branch",
    label: "Retail / transaction branch",
    description: "A transaction-focused branch profile requiring explicit ownership of terminal, guest, staff, WAN, and support boundaries.",
    requiredHumanInputs: [
      "Terminal and transaction traffic ownership boundaries",
      "Staff, guest, support, and vendor-access segmentation policy",
      "WAN dependency and outage fallback expectations",
      "Approved equipment and remote-support policy",
      "Maintenance window and local-site access constraints",
    ],
    mandatoryReviewRoles: ["network owner", "business service owner", "security reviewer"],
    automaticClaimsProhibited: ["Transaction-security compliance", "Vendor-support compatibility", "Business continuity guarantee"],
  },
  industrial: {
    id: "industrial",
    label: "Industrial / factory environment",
    description: "An industrial profile requiring OT-owner input, safety and process boundaries, vendor support evidence, and explicitly approved maintenance controls.",
    requiredHumanInputs: [
      "Process, safety, and availability impact boundaries",
      "OT system owner and equipment-vendor support constraints",
      "Approved zone, conduit, remote-access, and monitoring policy",
      "Device lifecycle, patch, backup, and maintenance restrictions",
      "Emergency stop, escalation, and rollback authority",
    ],
    mandatoryReviewRoles: ["OT owner", "safety authority", "network owner", "security reviewer", "change approver"],
    automaticClaimsProhibited: ["Functional safety assurance", "Industrial compliance certification", "Unattended OT configuration safety"],
  },
};

/** Return explicit profile completeness gaps without treating missing data as defaults. */
export type SectorReviewSnapshot = {
  profileId: SectorProfileId;
  suppliedInputs: string[];
  missingInputs: string[];
  completenessPercent: number;
  mandatoryReviewRoles: string[];
};

export const SECTOR_REVIEW_MAX_AGE_MS = 90 * 24 * 60 * 60 * 1000;

export function assessSectorProfileInputs(profileId: SectorProfileId, suppliedLabels: string[]): string[] {
  const supplied = new Set(suppliedLabels.map(value => value.trim().toLowerCase()));
  return sectorProfiles[profileId].requiredHumanInputs.filter(requirement => !supplied.has(requirement.toLowerCase()));
}

export function buildSectorReviewSnapshot(profileId: SectorProfileId, suppliedLabels: string[]): SectorReviewSnapshot {
  const suppliedInputs = Array.from(new Set(suppliedLabels.map(value => value.trim()).filter(Boolean)));
  const missingInputs = assessSectorProfileInputs(profileId, suppliedInputs);
  const requiredCount = sectorProfiles[profileId].requiredHumanInputs.length;
  return {
    profileId,
    suppliedInputs,
    missingInputs,
    completenessPercent: Math.round(((requiredCount - missingInputs.length) / requiredCount) * 100),
    mandatoryReviewRoles: [...sectorProfiles[profileId].mandatoryReviewRoles],
  };
}

export function isSectorReviewCurrent(
  reviewedAt: Date | null | undefined,
  now: Date = new Date(),
  maxAgeMs: number = SECTOR_REVIEW_MAX_AGE_MS,
): boolean {
  if (!reviewedAt || !Number.isFinite(reviewedAt.getTime())) return false;
  const age = now.getTime() - reviewedAt.getTime();
  return age >= 0 && age <= maxAgeMs;
}
