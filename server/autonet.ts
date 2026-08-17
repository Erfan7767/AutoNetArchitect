import { createHash } from "node:crypto";
import { and, count, desc, eq, or, sql } from "drizzle-orm";
import {
  auditEvents,
  authorizedDiscoveryScopes,
  benchmarkScenarios,
  changePlanBackupReceipts,
  changePlanRollbackPreparations,
  changePlanRollbackReviews,
  changePlans,
  deviceCapabilityAssessments,
  deviceRollbackEligibilityAssessments,
  inventoryInterfaceEvidence,
  inventoryLinkEvidence,
  managedDevices,
  managedSites,
  networkProjects,
  projectBomItems,
  projectConfigArtifacts,
  projectDesignDetails,
  projectEngineeringReviewReports,
  projectRestrictedClaims,
  projectSiteBusinessRequirements,
  postChangeVerificationRuns,
  virtualTestRuns,
  type InsertDiscoveryRun,
  type InsertNetworkProject,
  discoveryRuns,
} from "../drizzle/schema";
import { getDb } from "./db";
import { evaluateApprovalReadiness } from "./automationPolicy";
import { assessBenchmarkCoverage } from "./benchmarkPolicy";
import {
  assessSectorProfileInputs,
  buildSectorReviewSnapshot,
  isSectorReviewCurrent,
  type SectorProfileId,
} from "./sectorProfiles";

export type ProjectDraft = {
  name: string;
  organization?: string;
};

export type QuestionnaireDraft = {
  organization: string;
  organizationType: string;
  siteCount: number;
  classification: "greenfield" | "brownfield" | "undetermined";
  vendorPreferences: string;
  complianceNeeds: string;
};

export type SiteBusinessRequirementDraft = {
  siteReference: string;
  branchRole: string;
  servicePriorities: string;
  availabilityObjective: string;
  jurisdictionConstraints: string;
  humanMandatoryFields: string[];
  reviewState: "draft" | "reviewed";
};

export type DesignDetailDraft = {
  topologySummary: string;
  vlanPlan: string;
  ipAddressingSummary: string;
  decisionRecords: string;
};

export type BomItemDraft = {
  category: "device" | "optic" | "license" | "support" | "labor" | "rack" | "cable" | "spare";
  description: string;
  quantity: number;
  costEstimate: string;
};

export type ConfigArtifactDraft = {
  deviceId: number;
  vendor: string;
  deviceName: string;
  artifactSummary: string;
  artifactPreview: string;
  featureGuard: "pass" | "blocked" | "unknown";
  unsupportedFeatureLog: string;
};

export type RollbackReviewDraft = {
  rollbackScopeReference: string;
  rollbackArtifactHash: string;
  targetFactsHash: string;
  scopeHash: string;
  backupEvidenceReference: string;
  trigger: string;
  reviewState: "review_required" | "reviewed" | "blocked";
};

export type BackupReceiptDraft = {
  backupReference: string;
  backupArtifactHash: string;
  targetFactsHash: string;
  scopeHash: string;
  verificationState: "captured" | "verified" | "rejected";
};

export type ScopedRollbackPreparationDraft = {
  rollbackReviewId: number;
  rollbackArtifactHash: string;
  targetFactsHash: string;
  scopeHash: string;
};

export type DeviceRollbackEligibilityDraft = {
  rollbackArtifactHash: string;
  configurationPathReference: string;
  targetFactsHash: string;
  scopeHash: string;
  decision: "eligible" | "review_required" | "ineligible";
  evidenceReference: string;
  assessedAt: Date;
};

export type AgentTeamAuditDraft = {
  productionExecutionPermitted: false;
  agents: Array<{
    role: string;
    state: "ready" | "waiting" | "blocked" | "abstained" | "completed";
    blockers: string[];
  }>;
};

export type EngineeringReviewReportDraft = {
  reportReference: string;
  findings: Array<{
    specialty: "architecture" | "routing" | "security" | "addressing" | "layer2" | "equipment" | "configuration" | "validation";
    state: "passed" | "failed" | "blocked" | "unresolved";
    decisionReference: string;
    rationale: string;
    evidenceReferences: string[];
  }>;
  assumptions: string;
  risks: string;
  evidenceGaps: string;
  requiredHumanActions: string;
};

export type ManagedSiteDraft = {
  name: string;
  approvedScopeReference: string;
};

export type SiteAgentEnrollmentDraft = {
  agentReference: string;
  approvedScopeReference: string;
};

export type AuthorizedDiscoveryScopeDraft = {
  siteId: number;
  scopeReference: string;
  targetAllowlist: string;
  cidrAllowlist: string;
  protocolAllowlist: string;
  scopeHash: string;
};

const supportedReadOnlyDiscoveryProtocols = new Set(["ssh", "netconf", "https_api", "snmp"]);

export type ManagedDeviceDraft = {
  siteId: number;
  deviceReference: string;
  managementAddress: string;
  protocol: "ssh" | "netconf" | "https_api" | "snmp";
  credentialReference: string;
};

export type DeviceObservationDraft = {
  discoveryRunId: number;
  discoveryScopeId: number;
  observedVendor: string;
  observedPlatform: string;
  observedModel: string;
  observedVersion: string;
  factsHash: string;
  factState: "observed" | "ambiguous" | "unreachable" | "unsupported";
  capabilityVerified: boolean;
  capabilityEvidenceReference?: string;
  licenseEvidenceReference?: string;
  configurationPathEvidenceReference?: string;
};

export type InventoryInterfaceEvidenceDraft = {
  discoveryRunId: number;
  discoveryScopeId: number;
  interfaceReference: string;
  state: "observed" | "inferred" | "unknown";
  evidenceReference: string;
  evidenceHash: string;
  inferenceRationale: string;
  observedAt: Date;
};

export type InventoryLinkEvidenceDraft = {
  discoveryRunId: number;
  discoveryScopeId: number;
  endpointADeviceId: number;
  endpointAInterfaceReference: string;
  endpointBDeviceId: number;
  endpointBInterfaceReference: string;
  topologyState: "observed" | "inferred" | "unknown";
  evidenceReference: string;
  evidenceHash: string;
  inferenceRationale: string;
  observedAt: Date;
};

export type DeviceCapabilityAssessmentDraft = {
  observedVendor: string;
  observedPlatform: string;
  observedModel: string;
  observedVersion: string;
  capabilityEvidenceReference: string;
  licenseEvidenceReference: string;
  configurationPathEvidenceReference: string;
  decision: "configuration_supported" | "review_required" | "unsupported";
  assessedAt: Date;
};

export type ChangePlanDraft = {
  deviceId: number;
  name: string;
  artifactHash: string;
  scopeHash: string;
};

export type VirtualTestDraft = {
  state: "not_tested" | "test_queued" | "test_passed" | "test_failed" | "test_inconclusive" | "not_supported_for_virtual_test";
  adapterKind: string;
  fidelityLabel: string;
  artifactHash: string;
  targetFactsHash: string;
  scopeHash: string;
  detail: string;
};

export type PostChangeVerificationDraft = {
  state: "passed" | "failed" | "warning" | "not_verifiable";
  verificationType: "command_verification" | "connectivity_verification" | "service_verification" | "routing_verification" | "monitoring_verification" | "user_verification";
  expectedOutcome: string;
  observedOutcome: string;
  evidenceReference: string;
  observedAt: Date;
};

export type RestrictedClaimRecordDraft = {
  claimClass: "engineer_equivalence" | "production_safe" | "compatibility" | "compliance";
  scopeDescription: string;
  authorityReference: string;
  measuredEvidenceReference: string;
  reviewedAt: Date | null;
  assessmentStatus: "publishable" | "blocked";
};

export type BenchmarkScenarioDraft = {
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
  reviewedAt: Date;
};

export type ProjectSectorDraft = {
  sectorProfile: "enterprise" | "financial_service_branch" | "retail_transaction_branch" | "industrial";
  suppliedInputs: string[];
};

export function requiresUnsupportedFeatureAudit(draft: Pick<ConfigArtifactDraft, "featureGuard" | "unsupportedFeatureLog">): boolean {
  return draft.featureGuard === "blocked" || draft.unsupportedFeatureLog.trim().length > 0;
}

type AuditActor = {
  id: number;
  name?: string | null;
  email?: string | null;
};

const sensitiveReference = /\b(secret|token|password|api[ _-]?key|private[ _-]?key|credential|authorization)\b/i;

export function redactAuditDetails(details: string): string {
  const normalized = details.replace(/[\u0000-\u001f]+/g, " ").trim();
  if (sensitiveReference.test(normalized)) {
    return "Sensitive details were redacted.";
  }
  return normalized.slice(0, 480) || "No additional detail was recorded.";
}

export function calculateQuestionnaireCompleteness(input: QuestionnaireDraft): number {
  const checks = [
    input.organization.trim().length > 0,
    input.organizationType.trim().length > 0,
    input.siteCount > 0,
    input.classification !== "undetermined",
    input.vendorPreferences.trim().length > 0,
    input.complianceNeeds.trim().length > 0,
  ];
  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
}

function parseSectorInputs(serialized: string): string[] {
  try {
    const parsed: unknown = JSON.parse(serialized);
    return Array.isArray(parsed) && parsed.every(value => typeof value === "string") ? parsed : [];
  } catch {
    return [];
  }
}

export function getSectorPlanBlocker(
  sectorProfile: "unselected" | SectorProfileId,
  sectorInputs: string[],
): string | null {
  if (sectorProfile === "unselected") {
    return "A sector profile must be selected before a change plan can be created.";
  }
  const sectorGaps = assessSectorProfileInputs(sectorProfile, sectorInputs);
  return sectorGaps.length > 0 ? `Sector profile is incomplete: ${sectorGaps.join(" ")}` : null;
}

export function getDeploymentGate(project: {
  requirementsComplete: number;
  approvalState: "not_requested" | "pending" | "approved" | "blocked";
}): "go" | "no_go" | "review_required" {
  if (project.requirementsComplete < 100 || project.approvalState === "blocked") {
    return "no_go";
  }
  if (project.approvalState !== "approved") {
    return "review_required";
  }
  return "go";
}

async function requireDatabase() {
  const db = await getDb();
  if (!db) {
    throw new Error("The project data service is temporarily unavailable.");
  }
  return db;
}

function actorLabel(actor: AuditActor): string {
  return (actor.name || actor.email || "Authenticated user").slice(0, 160);
}

async function appendAuditEvent(
  projectId: number,
  actor: AuditActor,
  action: string,
  details: string,
): Promise<void> {
  const db = await requireDatabase();
  await db.insert(auditEvents).values({
    projectId,
    actorId: actor.id,
    actorName: actorLabel(actor),
    action: action.slice(0, 100),
    details: redactAuditDetails(details),
  });
}

export async function listProjectsForUser(ownerId: number) {
  const db = await requireDatabase();
  return db
    .select()
    .from(networkProjects)
    .where(eq(networkProjects.ownerId, ownerId))
    .orderBy(desc(networkProjects.updatedAt));
}

export async function getProjectForUser(projectId: number, ownerId: number) {
  const db = await requireDatabase();
  const result = await db
    .select()
    .from(networkProjects)
    .where(and(eq(networkProjects.id, projectId), eq(networkProjects.ownerId, ownerId)))
    .limit(1);
  return result[0];
}

export async function createProjectForUser(draft: ProjectDraft, actor: AuditActor) {
  const db = await requireDatabase();
  const values: InsertNetworkProject = {
    ownerId: actor.id,
    name: draft.name.trim(),
    organization: (draft.organization || "").trim(),
    status: "intake",
    questionnaireComplete: 0,
    requirementsComplete: 0,
    approvalState: "not_requested",
  };
  const inserted = await db.insert(networkProjects).values(values).$returningId();
  const projectId = inserted[0]?.id;
  if (!projectId) {
    throw new Error("The project could not be created.");
  }
  await appendAuditEvent(projectId, actor, "project.created", "Project record created.");
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) {
    throw new Error("The created project could not be loaded.");
  }
  return project;
}

export async function updateProjectQuestionnaire(
  projectId: number,
  draft: QuestionnaireDraft,
  actor: AuditActor,
) {
  const existing = await getProjectForUser(projectId, actor.id);
  if (!existing) {
    return undefined;
  }
  const db = await requireDatabase();
  const completeness = calculateQuestionnaireCompleteness(draft);
  await db
    .update(networkProjects)
    .set({
      organization: draft.organization.trim(),
      organizationType: draft.organizationType.trim(),
      siteCount: draft.siteCount,
      classification: draft.classification,
      vendorPreferences: draft.vendorPreferences.trim(),
      complianceNeeds: draft.complianceNeeds.trim(),
      questionnaireComplete: completeness,
      requirementsComplete: completeness,
      status: completeness === 100 ? "design" : "intake",
      approvalState: completeness === 100 ? existing.approvalState : "not_requested",
      updatedAt: new Date(),
    })
    .where(eq(networkProjects.id, projectId));
  await appendAuditEvent(
    projectId,
    actor,
    "questionnaire.updated",
    `Questionnaire captured with ${completeness}% completeness.`,
  );
  return getProjectForUser(projectId, actor.id);
}

/** List human-supplied business context records without treating them as discovered site facts. */
export async function listSiteBusinessRequirements(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  const records = await db
    .select()
    .from(projectSiteBusinessRequirements)
    .where(eq(projectSiteBusinessRequirements.projectId, projectId))
    .orderBy(desc(projectSiteBusinessRequirements.updatedAt));
  return records.map(record => ({ ...record, humanMandatoryFields: parseSectorInputs(record.humanMandatoryFields) }));
}

/** Persist one reviewed or draft site-business record after verifying project ownership. */
export async function recordSiteBusinessRequirement(
  projectId: number,
  draft: SiteBusinessRequirementDraft,
  actor: AuditActor,
) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) return undefined;
  const mandatoryFields = Array.from(new Set(draft.humanMandatoryFields.map(value => value.trim()).filter(Boolean)));
  if (draft.reviewState === "reviewed" && mandatoryFields.length === 0) {
    throw new Error("A reviewed multi-site business record requires named human-supplied mandatory fields.");
  }
  const db = await requireDatabase();
  await db.insert(projectSiteBusinessRequirements).values({
    projectId,
    siteReference: draft.siteReference.trim(),
    branchRole: draft.branchRole.trim(),
    servicePriorities: draft.servicePriorities.trim(),
    availabilityObjective: draft.availabilityObjective.trim(),
    jurisdictionConstraints: draft.jurisdictionConstraints.trim(),
    humanMandatoryFields: JSON.stringify(mandatoryFields),
    reviewState: draft.reviewState,
    reviewedAt: draft.reviewState === "reviewed" ? new Date() : null,
  });
  await appendAuditEvent(projectId, actor, "multi_site_business_requirement.recorded", `Multi-site business intake record saved in ${draft.reviewState} state.`);
  return listSiteBusinessRequirements(projectId, actor.id);
}

export async function updateProjectSector(projectId: number, draft: ProjectSectorDraft, actor: AuditActor) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) return undefined;
  const normalizedInputs = Array.from(new Set(draft.suppliedInputs.map(value => value.trim()).filter(Boolean)));
  const db = await requireDatabase();
  const sectorInputsUpdatedAt = new Date();
  await db
    .update(networkProjects)
    .set({ sectorProfile: draft.sectorProfile, sectorInputs: JSON.stringify(normalizedInputs), sectorInputsUpdatedAt, updatedAt: sectorInputsUpdatedAt })
    .where(eq(networkProjects.id, projectId));
  const gaps = assessSectorProfileInputs(draft.sectorProfile, normalizedInputs);
  await appendAuditEvent(
    projectId,
    actor,
    "sector.profile_updated",
    gaps.length === 0 ? "Sector profile inputs are complete." : `Sector profile recorded with ${gaps.length} unresolved required input(s).`,
  );
  return getProjectForUser(projectId, actor.id);
}

export async function getSectorReviewStatus(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const profileId = project.sectorProfile as "unselected" | SectorProfileId;
  if (profileId === "unselected") {
    return {
      profileId,
      completenessPercent: 0,
      missingInputs: ["A sector profile must be selected before review."],
      reviewCurrent: false,
      reviewedAt: project.sectorInputsUpdatedAt,
    };
  }
  const snapshot = buildSectorReviewSnapshot(profileId, parseSectorInputs(project.sectorInputs));
  return {
    profileId,
    completenessPercent: snapshot.completenessPercent,
    missingInputs: snapshot.missingInputs,
    reviewCurrent: isSectorReviewCurrent(project.sectorInputsUpdatedAt),
    reviewedAt: project.sectorInputsUpdatedAt,
  };
}

export async function requestDeploymentApproval(projectId: number, actor: AuditActor) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) {
    return undefined;
  }
  if (project.requirementsComplete < 100) {
    throw new Error("Requirements must be complete before approval can be requested.");
  }
  const db = await requireDatabase();
  await db
    .update(networkProjects)
    .set({ approvalState: "pending", status: "ready_for_review", updatedAt: new Date() })
    .where(eq(networkProjects.id, projectId));
  await appendAuditEvent(projectId, actor, "deployment.approval_requested", "Deployment approval was requested.");
  return getProjectForUser(projectId, actor.id);
}

export async function getDesignDetails(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  const result = await db.select().from(projectDesignDetails).where(eq(projectDesignDetails.projectId, projectId)).limit(1);
  return result[0] || null;
}

export async function saveDesignDetails(projectId: number, draft: DesignDetailDraft, actor: AuditActor) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) return undefined;
  const db = await requireDatabase();
  await db.insert(projectDesignDetails).values({
    projectId,
    topologySummary: draft.topologySummary.trim(),
    vlanPlan: draft.vlanPlan.trim(),
    ipAddressingSummary: draft.ipAddressingSummary.trim(),
    decisionRecords: draft.decisionRecords.trim(),
  }).onDuplicateKeyUpdate({
    set: {
      topologySummary: draft.topologySummary.trim(),
      vlanPlan: draft.vlanPlan.trim(),
      ipAddressingSummary: draft.ipAddressingSummary.trim(),
      decisionRecords: draft.decisionRecords.trim(),
      updatedAt: new Date(),
    },
  });
  await appendAuditEvent(projectId, actor, "design.details_updated", "Design detail fields were updated.");
  return getDesignDetails(projectId, actor.id);
}

export async function listBomItems(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  return db.select().from(projectBomItems).where(eq(projectBomItems.projectId, projectId)).orderBy(desc(projectBomItems.createdAt));
}

export async function addBomItem(projectId: number, draft: BomItemDraft, actor: AuditActor) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) return undefined;
  const db = await requireDatabase();
  await db.insert(projectBomItems).values({
    projectId,
    category: draft.category,
    description: draft.description.trim(),
    quantity: draft.quantity,
    costEstimate: draft.costEstimate.trim(),
  });
  await appendAuditEvent(projectId, actor, "bom.item_added", `BOM item added in category ${draft.category}.`);
  return listBomItems(projectId, actor.id);
}

export async function listConfigArtifacts(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  return db.select().from(projectConfigArtifacts).where(eq(projectConfigArtifacts.projectId, projectId)).orderBy(desc(projectConfigArtifacts.createdAt));
}

export async function listProjectRestrictedClaims(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  return db.select().from(projectRestrictedClaims).where(eq(projectRestrictedClaims.projectId, projectId)).orderBy(desc(projectRestrictedClaims.updatedAt));
}

export async function listBenchmarkScenarios(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  return db.select().from(benchmarkScenarios).where(eq(benchmarkScenarios.projectId, projectId)).orderBy(desc(benchmarkScenarios.updatedAt));
}

/** Records supplied measurement facts and acceptance criteria; it makes no unscoped performance or safety claim. */
export async function recordBenchmarkScenario(projectId: number, draft: BenchmarkScenarioDraft, actor: AuditActor) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) return undefined;
  const db = await requireDatabase();
  await db.insert(benchmarkScenarios).values({
    projectId,
    scenarioId: draft.scenarioId.trim(),
    vendorFamily: draft.vendorFamily,
    platform: draft.platform.trim(),
    model: draft.model.trim(),
    softwareVersion: draft.softwareVersion.trim(),
    licenseEvidenceReference: redactAuditDetails(draft.licenseEvidenceReference),
    configurationPathReference: redactAuditDetails(draft.configurationPathReference),
    sectorProfile: draft.sectorProfile,
    measuredRuns: draft.measuredRuns,
    acceptedRuns: draft.acceptedRuns,
    rejectedRuns: draft.rejectedRuns,
    minimumAcceptanceRatePercent: draft.minimumAcceptanceRatePercent,
    acceptanceCriteriaReference: redactAuditDetails(draft.acceptanceCriteriaReference),
    evidenceReference: redactAuditDetails(draft.evidenceReference),
    reviewedAt: draft.reviewedAt,
  });
  await appendAuditEvent(projectId, actor, "benchmark.scenario_recorded", `Measured scenario ${draft.scenarioId.trim()} recorded for bounded review.`);
  return listBenchmarkScenarios(projectId, actor.id);
}

/** Stores a scoped claim assessment record without publishing a claim or granting execution authority. */
export async function recordProjectRestrictedClaim(projectId: number, draft: RestrictedClaimRecordDraft, actor: AuditActor) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) return undefined;
  const db = await requireDatabase();
  await db.insert(projectRestrictedClaims).values({
    projectId,
    claimClass: draft.claimClass,
    scopeDescription: redactAuditDetails(draft.scopeDescription),
    authorityReference: redactAuditDetails(draft.authorityReference),
    measuredEvidenceReference: redactAuditDetails(draft.measuredEvidenceReference),
    reviewedAt: draft.reviewedAt,
    assessmentStatus: draft.assessmentStatus,
  });
  await appendAuditEvent(projectId, actor, "restricted_claim.assessed", `Scoped ${draft.claimClass.replaceAll("_", " ")} claim assessment recorded with status ${draft.assessmentStatus}.`);
  return listProjectRestrictedClaims(projectId, actor.id);
}

/** List advisory engineering-review reports for a project. */
export async function listEngineeringReviewReports(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  return db.select().from(projectEngineeringReviewReports).where(eq(projectEngineeringReviewReports.projectId, projectId)).orderBy(desc(projectEngineeringReviewReports.createdAt));
}

/** Persist a multi-specialty review summary; it cannot approve, release, or execute a change. */
export async function recordEngineeringReviewReport(projectId: number, draft: EngineeringReviewReportDraft, actor: AuditActor) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) return undefined;
  if (!draft.findings.length) throw new Error("An engineering review report requires at least one specialty finding.");
  const serializedFindings = JSON.stringify(draft.findings.map(finding => ({
    specialty: finding.specialty,
    state: finding.state,
    decisionReference: redactAuditDetails(finding.decisionReference),
    rationale: redactAuditDetails(finding.rationale),
    evidenceReferences: finding.evidenceReferences.map(redactAuditDetails),
  })));
  const db = await requireDatabase();
  await db.insert(projectEngineeringReviewReports).values({
    projectId,
    reportReference: draft.reportReference.trim(),
    findingsJson: serializedFindings,
    passedCount: draft.findings.filter(finding => finding.state === "passed").length,
    failedCount: draft.findings.filter(finding => finding.state === "failed").length,
    blockedCount: draft.findings.filter(finding => finding.state === "blocked").length,
    unresolvedCount: draft.findings.filter(finding => finding.state === "unresolved").length,
    assumptions: redactAuditDetails(draft.assumptions),
    risks: redactAuditDetails(draft.risks),
    evidenceGaps: redactAuditDetails(draft.evidenceGaps),
    requiredHumanActions: redactAuditDetails(draft.requiredHumanActions),
    recordedBy: actorLabel(actor),
  });
  await appendAuditEvent(projectId, actor, "engineering_review.recorded", "Multi-specialty engineering review report recorded; human approval remains separately required.");
  return listEngineeringReviewReports(projectId, actor.id);
}

export async function recordAgentTeamAudit(projectId: number, draft: AgentTeamAuditDraft, actor: AuditActor) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) return undefined;
  if (draft.productionExecutionPermitted) {
    throw new Error("Agent-team audit records cannot assert production execution authority.");
  }
  const details = JSON.stringify({
    productionExecutionPermitted: false,
    agents: draft.agents.map(agent => ({ role: agent.role, state: agent.state, blockers: agent.blockers })),
  });
  await appendAuditEvent(projectId, actor, "multi_agent.workflow_evaluated", details);
  return { recorded: true, productionExecutionPermitted: false } as const;
}

export async function addConfigArtifact(projectId: number, draft: ConfigArtifactDraft, actor: AuditActor) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) return undefined;
  const deviceRecord = await getManagedDeviceForUser(draft.deviceId, actor.id);
  if (!deviceRecord || deviceRecord.project.id !== projectId) return undefined;
  const device = deviceRecord.device;
  if (device.factState !== "observed" || !device.factsHash) {
    throw new Error("Config artifact preparation requires current observed device facts.");
  }
  if (!device.capabilityVerified || !device.capabilityEvidenceReference || !device.licenseEvidenceReference || !device.configurationPathEvidenceReference) {
    throw new Error("Config artifact preparation requires exact capability, license, and configuration-path evidence references.");
  }
  if (draft.featureGuard === "pass") {
    const db = await requireDatabase();
    const assessments = await db.select().from(deviceCapabilityAssessments).where(eq(deviceCapabilityAssessments.deviceId, device.id)).orderBy(desc(deviceCapabilityAssessments.assessedAt)).limit(1);
    const assessment = assessments[0];
    const accepted = assessment?.decision === "configuration_supported"
      && assessment.observedVendor.trim().toLowerCase() === device.observedVendor.trim().toLowerCase()
      && assessment.observedPlatform === device.observedPlatform
      && assessment.observedModel === device.observedModel
      && assessment.observedVersion === device.observedVersion
      && assessment.capabilityEvidenceReference === device.capabilityEvidenceReference
      && assessment.licenseEvidenceReference === device.licenseEvidenceReference
      && assessment.configurationPathEvidenceReference === device.configurationPathEvidenceReference;
    if (!accepted) throw new Error("Config artifact preparation cannot mark a feature guard as pass until an accepted exact capability decision is persisted for the current observed device.");
  }
  if (!device.observedVendor || !draft.vendor.trim().toLowerCase().includes(device.observedVendor.trim().toLowerCase())) {
    throw new Error("Config artifact vendor must match the observed device vendor evidence.");
  }
  const db = await requireDatabase();
  await db.insert(projectConfigArtifacts).values({
    projectId,
    deviceId: draft.deviceId,
    vendor: draft.vendor.trim(),
    deviceName: draft.deviceName.trim(),
    artifactSummary: redactAuditDetails(draft.artifactSummary),
    artifactPreview: redactAuditDetails(draft.artifactPreview),
    featureGuard: draft.featureGuard,
    unsupportedFeatureLog: redactAuditDetails(draft.unsupportedFeatureLog),
  });
  await appendAuditEvent(projectId, actor, "config.artifact_added", `Capability-gated config artifact recorded for ${draft.vendor.trim()}.`);
  if (requiresUnsupportedFeatureAudit(draft)) {
    await appendAuditEvent(
      projectId,
      actor,
      "config.unsupported_feature",
      draft.unsupportedFeatureLog.trim() || "A feature guard blocked the reviewed configuration artifact.",
    );
  }
  return listConfigArtifacts(projectId, actor.id);
}

export async function listManagedSites(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  return db.select().from(managedSites).where(eq(managedSites.projectId, projectId)).orderBy(desc(managedSites.updatedAt));
}

export async function createManagedSite(projectId: number, draft: ManagedSiteDraft, actor: AuditActor) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) return undefined;
  const db = await requireDatabase();
  await db.insert(managedSites).values({
    projectId,
    name: draft.name.trim(),
    approvedScopeReference: draft.approvedScopeReference.trim(),
    mode: "read_only",
    enrollmentState: "not_enrolled",
  });
  await appendAuditEvent(projectId, actor, "site.registered", "A site was registered in read-only mode.");
  return listManagedSites(projectId, actor.id);
}

export async function enrollSiteAgent(projectId: number, siteId: number, draft: SiteAgentEnrollmentDraft, actor: AuditActor) {
  const siteRecord = await getManagedSiteForUser(siteId, actor.id);
  if (!siteRecord || siteRecord.site.projectId !== projectId) return undefined;
  if (siteRecord.site.approvedScopeReference !== draft.approvedScopeReference.trim()) {
    throw new Error("Agent enrollment must confirm the exact approved scope reference recorded for this site.");
  }
  const db = await requireDatabase();
  await db.update(managedSites).set({
    agentReference: redactAuditDetails(draft.agentReference),
    enrollmentState: "active",
    mode: "read_only",
  }).where(eq(managedSites.id, siteId));
  await appendAuditEvent(projectId, actor, "site.agent_enrolled", "A local agent reference was enrolled for read-only discovery within the confirmed site scope.");
  return listManagedSites(projectId, actor.id);
}

export async function createAuthorizedDiscoveryScope(projectId: number, draft: AuthorizedDiscoveryScopeDraft, actor: AuditActor) {
  const siteRecord = await getManagedSiteForUser(draft.siteId, actor.id);
  if (!siteRecord || siteRecord.site.projectId !== projectId) return undefined;
  if (siteRecord.site.enrollmentState !== "active") throw new Error("An active read-only site agent is required before an authorized discovery scope can be recorded.");
  const targetAllowlist = draft.targetAllowlist.trim();
  const cidrAllowlist = draft.cidrAllowlist.trim();
  if (!targetAllowlist && !cidrAllowlist) throw new Error("An authorized discovery scope requires a target or CIDR allowlist.");
  const protocols = draft.protocolAllowlist.split(",").map(protocol => protocol.trim()).filter(Boolean);
  if (protocols.length === 0 || protocols.some(protocol => !supportedReadOnlyDiscoveryProtocols.has(protocol))) {
    throw new Error("An authorized discovery scope may use only supported read-only protocols: ssh, netconf, https_api, snmp.");
  }
  const db = await requireDatabase();
  await db.insert(authorizedDiscoveryScopes).values({
    projectId,
    siteId: draft.siteId,
    scopeReference: draft.scopeReference.trim(),
    targetAllowlist: redactAuditDetails(targetAllowlist),
    cidrAllowlist: redactAuditDetails(cidrAllowlist),
    protocolAllowlist: protocols.join(","),
    scopeHash: draft.scopeHash.trim(),
    status: "active",
  });
  await appendAuditEvent(projectId, actor, "discovery.scope_recorded", "An active read-only discovery scope with bounded targets, CIDRs, and protocols was recorded.");
  return listAuthorizedDiscoveryScopes(projectId, draft.siteId, actor.id);
}

export async function listAuthorizedDiscoveryScopes(projectId: number, siteId: number, ownerId: number) {
  const siteRecord = await getManagedSiteForUser(siteId, ownerId);
  if (!siteRecord || siteRecord.site.projectId !== projectId) return undefined;
  const db = await requireDatabase();
  return db.select().from(authorizedDiscoveryScopes).where(and(eq(authorizedDiscoveryScopes.projectId, projectId), eq(authorizedDiscoveryScopes.siteId, siteId))).orderBy(desc(authorizedDiscoveryScopes.updatedAt));
}

async function getManagedSiteForUser(siteId: number, ownerId: number) {
  const db = await requireDatabase();
  const result = await db
    .select({ site: managedSites, project: networkProjects })
    .from(managedSites)
    .innerJoin(networkProjects, eq(managedSites.projectId, networkProjects.id))
    .where(and(eq(managedSites.id, siteId), eq(networkProjects.ownerId, ownerId)))
    .limit(1);
  return result[0];
}

export async function listManagedDevices(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  return db
    .select({ device: managedDevices, siteName: managedSites.name })
    .from(managedDevices)
    .innerJoin(managedSites, eq(managedDevices.siteId, managedSites.id))
    .where(eq(managedSites.projectId, projectId))
    .orderBy(desc(managedDevices.updatedAt));
}

export async function registerManagedDevice(projectId: number, draft: ManagedDeviceDraft, actor: AuditActor) {
  const siteRecord = await getManagedSiteForUser(draft.siteId, actor.id);
  if (!siteRecord || siteRecord.site.projectId !== projectId) return undefined;
  const db = await requireDatabase();
  await db.insert(managedDevices).values({
    siteId: draft.siteId,
    deviceReference: draft.deviceReference.trim(),
    managementAddress: draft.managementAddress.trim(),
    protocol: draft.protocol,
    credentialReference: draft.credentialReference.trim(),
    factState: "unobserved",
  });
  await appendAuditEvent(projectId, actor, "device.registered", "A managed device reference was registered without credentials.");
  return listManagedDevices(projectId, actor.id);
}

async function getManagedDeviceForUser(deviceId: number, ownerId: number) {
  const db = await requireDatabase();
  const result = await db
    .select({ device: managedDevices, site: managedSites, project: networkProjects })
    .from(managedDevices)
    .innerJoin(managedSites, eq(managedDevices.siteId, managedSites.id))
    .innerJoin(networkProjects, eq(managedSites.projectId, networkProjects.id))
    .where(and(eq(managedDevices.id, deviceId), eq(networkProjects.ownerId, ownerId)))
    .limit(1);
  return result[0];
}

async function validateDiscoveryEvidenceForSite(projectId: number, siteId: number, discoveryRunId: number, discoveryScopeId: number, ownerId: number) {
  const db = await requireDatabase();
  const results = await db
    .select({ run: discoveryRuns, scope: authorizedDiscoveryScopes })
    .from(discoveryRuns)
    .innerJoin(authorizedDiscoveryScopes, eq(discoveryRuns.discoveryScopeId, authorizedDiscoveryScopes.id))
    .innerJoin(managedSites, eq(discoveryRuns.siteId, managedSites.id))
    .innerJoin(networkProjects, eq(managedSites.projectId, networkProjects.id))
    .where(and(
      eq(discoveryRuns.id, discoveryRunId),
      eq(discoveryRuns.discoveryScopeId, discoveryScopeId),
      eq(discoveryRuns.siteId, siteId),
      eq(authorizedDiscoveryScopes.siteId, siteId),
      eq(authorizedDiscoveryScopes.projectId, projectId),
      eq(networkProjects.ownerId, ownerId),
    ))
    .limit(1);
  const source = results[0];
  if (!source) throw new Error("Inventory evidence must reference a discovery run and scope authorized for the same site.");
  if (source.run.state !== "completed" && source.run.state !== "partial") {
    throw new Error("Inventory evidence can be recorded only from a completed or partial read-only discovery run.");
  }
  return source;
}

export async function listInventoryInterfaceEvidence(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  return db
    .select({ evidence: inventoryInterfaceEvidence, device: managedDevices, siteName: managedSites.name })
    .from(inventoryInterfaceEvidence)
    .innerJoin(managedDevices, eq(inventoryInterfaceEvidence.deviceId, managedDevices.id))
    .innerJoin(managedSites, eq(inventoryInterfaceEvidence.siteId, managedSites.id))
    .where(and(eq(managedSites.projectId, projectId), eq(managedDevices.siteId, inventoryInterfaceEvidence.siteId)))
    .orderBy(desc(inventoryInterfaceEvidence.observedAt));
}

export async function recordInventoryInterfaceEvidence(projectId: number, deviceId: number, draft: InventoryInterfaceEvidenceDraft, actor: AuditActor) {
  const deviceRecord = await getManagedDeviceForUser(deviceId, actor.id);
  if (!deviceRecord || deviceRecord.project.id !== projectId) return undefined;
  await validateDiscoveryEvidenceForSite(projectId, deviceRecord.device.siteId, draft.discoveryRunId, draft.discoveryScopeId, actor.id);
  if (draft.state === "observed" && deviceRecord.device.factState !== "observed") {
    throw new Error("Observed interface evidence requires an observed device identity.");
  }
  if (draft.state === "inferred" && !draft.inferenceRationale.trim()) {
    throw new Error("Inferred interface evidence requires an explicit inference rationale.");
  }
  const db = await requireDatabase();
  await db.insert(inventoryInterfaceEvidence).values({
    siteId: deviceRecord.device.siteId,
    deviceId,
    discoveryRunId: draft.discoveryRunId,
    discoveryScopeId: draft.discoveryScopeId,
    interfaceReference: draft.interfaceReference.trim(),
    state: draft.state,
    evidenceReference: redactAuditDetails(draft.evidenceReference),
    evidenceHash: draft.evidenceHash.trim(),
    inferenceRationale: redactAuditDetails(draft.inferenceRationale),
    observedAt: draft.observedAt,
  });
  await appendAuditEvent(projectId, actor, "inventory.interface_evidence_recorded", `Interface inventory evidence recorded with explicit state ${draft.state}.`);
  return listInventoryInterfaceEvidence(projectId, actor.id);
}

export async function listInventoryLinkEvidence(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  return db
    .select({ evidence: inventoryLinkEvidence, siteName: managedSites.name })
    .from(inventoryLinkEvidence)
    .innerJoin(managedSites, eq(inventoryLinkEvidence.siteId, managedSites.id))
    .where(eq(managedSites.projectId, projectId))
    .orderBy(desc(inventoryLinkEvidence.observedAt));
}

export async function recordInventoryLinkEvidence(projectId: number, draft: InventoryLinkEvidenceDraft, actor: AuditActor) {
  const endpointA = await getManagedDeviceForUser(draft.endpointADeviceId, actor.id);
  if (!endpointA || endpointA.project.id !== projectId) return undefined;
  await validateDiscoveryEvidenceForSite(projectId, endpointA.device.siteId, draft.discoveryRunId, draft.discoveryScopeId, actor.id);
  const endpointB = draft.endpointBDeviceId > 0 ? await getManagedDeviceForUser(draft.endpointBDeviceId, actor.id) : undefined;
  if (draft.endpointBDeviceId > 0 && (!endpointB || endpointB.project.id !== projectId || endpointB.device.siteId !== endpointA.device.siteId)) {
    throw new Error("A known link endpoint must be an owned device at the same authorized site.");
  }
  if (draft.topologyState === "observed" && (!endpointB || endpointA.device.factState !== "observed" || endpointB.device.factState !== "observed")) {
    throw new Error("Observed topology evidence requires two observed endpoint devices; record an inferred or unknown state otherwise.");
  }
  if (draft.topologyState === "inferred" && !draft.inferenceRationale.trim()) {
    throw new Error("Inferred topology evidence requires an explicit inference rationale.");
  }
  const db = await requireDatabase();
  await db.insert(inventoryLinkEvidence).values({
    siteId: endpointA.device.siteId,
    discoveryRunId: draft.discoveryRunId,
    discoveryScopeId: draft.discoveryScopeId,
    endpointADeviceId: draft.endpointADeviceId,
    endpointAInterfaceReference: draft.endpointAInterfaceReference.trim(),
    endpointBDeviceId: draft.endpointBDeviceId,
    endpointBInterfaceReference: draft.endpointBInterfaceReference.trim(),
    topologyState: draft.topologyState,
    evidenceReference: redactAuditDetails(draft.evidenceReference),
    evidenceHash: draft.evidenceHash.trim(),
    inferenceRationale: redactAuditDetails(draft.inferenceRationale),
    observedAt: draft.observedAt,
  });
  await appendAuditEvent(projectId, actor, "inventory.link_evidence_recorded", `Topology link evidence recorded with explicit state ${draft.topologyState}.`);
  return listInventoryLinkEvidence(projectId, actor.id);
}

export async function recordDeviceObservation(projectId: number, deviceId: number, draft: DeviceObservationDraft, actor: AuditActor) {
  const record = await getManagedDeviceForUser(deviceId, actor.id);
  if (!record || record.project.id !== projectId) return undefined;
  const db = await requireDatabase();
  const discoveryEvidence = await db
    .select({ run: discoveryRuns, scope: authorizedDiscoveryScopes })
    .from(discoveryRuns)
    .innerJoin(authorizedDiscoveryScopes, eq(discoveryRuns.discoveryScopeId, authorizedDiscoveryScopes.id))
    .innerJoin(managedSites, eq(discoveryRuns.siteId, managedSites.id))
    .innerJoin(networkProjects, eq(managedSites.projectId, networkProjects.id))
    .where(and(
      eq(discoveryRuns.id, draft.discoveryRunId),
      eq(discoveryRuns.discoveryScopeId, draft.discoveryScopeId),
      eq(discoveryRuns.siteId, record.device.siteId),
      eq(authorizedDiscoveryScopes.siteId, record.device.siteId),
      eq(authorizedDiscoveryScopes.projectId, projectId),
      eq(networkProjects.ownerId, actor.id),
    ))
    .limit(1);
  const source = discoveryEvidence[0];
  if (!source) throw new Error("Device evidence must reference a discovery run and scope authorized for the device site.");
  if (source.run.state !== "completed" && source.run.state !== "partial") {
    throw new Error("Device evidence can be recorded only from a completed or partial read-only discovery run.");
  }
  const capabilityEvidenceReference = draft.capabilityEvidenceReference?.trim() || "";
  const licenseEvidenceReference = draft.licenseEvidenceReference?.trim() || "";
  const configurationPathEvidenceReference = draft.configurationPathEvidenceReference?.trim() || "";
  if (draft.capabilityVerified && draft.factState !== "observed") {
    throw new Error("Capability verification requires an observed device fact state.");
  }
  if (draft.capabilityVerified && (!capabilityEvidenceReference || !licenseEvidenceReference || !configurationPathEvidenceReference)) {
    throw new Error("Capability verification requires capability, license, and configuration-path evidence references.");
  }
  await db
    .update(managedDevices)
    .set({
      discoveryRunId: draft.discoveryRunId,
      discoveryScopeId: draft.discoveryScopeId,
      observedVendor: draft.observedVendor.trim(),
      observedPlatform: draft.observedPlatform.trim(),
      observedModel: draft.observedModel.trim(),
      observedVersion: draft.observedVersion.trim(),
      factsHash: draft.factsHash.trim(),
      factState: draft.factState,
      capabilityVerified: draft.capabilityVerified,
      capabilityEvidenceReference,
      licenseEvidenceReference,
      configurationPathEvidenceReference,
      lastObservedAt: new Date(),
      updatedAt: new Date(),
    })
    .where(eq(managedDevices.id, deviceId));
  await appendAuditEvent(projectId, actor, "device.observation_recorded", `Device observation recorded with state ${draft.factState}.`);
  return getManagedDeviceForUser(deviceId, actor.id);
}

export async function listDeviceCapabilityAssessments(projectId: number, deviceId: number, ownerId: number) {
  const deviceRecord = await getManagedDeviceForUser(deviceId, ownerId);
  if (!deviceRecord || deviceRecord.project.id !== projectId) return undefined;
  const db = await requireDatabase();
  return db.select().from(deviceCapabilityAssessments).where(eq(deviceCapabilityAssessments.deviceId, deviceId)).orderBy(desc(deviceCapabilityAssessments.assessedAt));
}

/** Persists an exact human-reviewed capability decision; it does not authorize a device action. */
export async function recordDeviceCapabilityAssessment(projectId: number, deviceId: number, draft: DeviceCapabilityAssessmentDraft, actor: AuditActor) {
  const deviceRecord = await getManagedDeviceForUser(deviceId, actor.id);
  if (!deviceRecord || deviceRecord.project.id !== projectId) return undefined;
  const device = deviceRecord.device;
  if (device.factState !== "observed" || !device.factsHash) throw new Error("Exact capability assessment requires current observed device facts.");
  const identityMatches = device.observedVendor.trim().toLowerCase() === draft.observedVendor.trim().toLowerCase()
    && device.observedPlatform.trim() === draft.observedPlatform.trim()
    && device.observedModel.trim() === draft.observedModel.trim()
    && device.observedVersion.trim() === draft.observedVersion.trim();
  if (!identityMatches) throw new Error("Exact capability assessment must match the observed vendor, platform, model, and version.");
  const evidenceMatches = device.capabilityEvidenceReference === draft.capabilityEvidenceReference.trim()
    && device.licenseEvidenceReference === draft.licenseEvidenceReference.trim()
    && device.configurationPathEvidenceReference === draft.configurationPathEvidenceReference.trim();
  if (!evidenceMatches) throw new Error("Exact capability assessment must use the persisted capability, license, and configuration-path evidence references.");
  const db = await requireDatabase();
  await db.insert(deviceCapabilityAssessments).values({
    deviceId,
    observedVendor: draft.observedVendor.trim(),
    observedPlatform: draft.observedPlatform.trim(),
    observedModel: draft.observedModel.trim(),
    observedVersion: draft.observedVersion.trim(),
    capabilityEvidenceReference: redactAuditDetails(draft.capabilityEvidenceReference),
    licenseEvidenceReference: redactAuditDetails(draft.licenseEvidenceReference),
    configurationPathEvidenceReference: redactAuditDetails(draft.configurationPathEvidenceReference),
    decision: draft.decision,
    assessedAt: draft.assessedAt,
  });
  await appendAuditEvent(projectId, actor, "device.capability_assessed", `Exact capability assessment recorded with decision ${draft.decision}.`);
  return listDeviceCapabilityAssessments(projectId, deviceId, actor.id);
}

/** List action-specific rollback eligibility assessments for one observed device. */
export async function listDeviceRollbackEligibilityAssessments(projectId: number, deviceId: number, ownerId: number) {
  const deviceRecord = await getManagedDeviceForUser(deviceId, ownerId);
  if (!deviceRecord || deviceRecord.project.id !== projectId) return undefined;
  const db = await requireDatabase();
  return db.select().from(deviceRollbackEligibilityAssessments).where(eq(deviceRollbackEligibilityAssessments.deviceId, deviceId)).orderBy(desc(deviceRollbackEligibilityAssessments.assessedAt));
}

/** Persist human-reviewed eligibility for exactly one rollback artifact and configuration path. */
export async function recordDeviceRollbackEligibilityAssessment(projectId: number, deviceId: number, draft: DeviceRollbackEligibilityDraft, actor: AuditActor) {
  const deviceRecord = await getManagedDeviceForUser(deviceId, actor.id);
  if (!deviceRecord || deviceRecord.project.id !== projectId) return undefined;
  const device = deviceRecord.device;
  if (device.factState !== "observed" || !device.factsHash) {
    throw new Error("Rollback eligibility requires current observed device facts.");
  }
  if (draft.targetFactsHash !== device.factsHash) {
    throw new Error("Rollback eligibility must exactly match the observed device facts hash.");
  }
  if (draft.configurationPathReference.trim() !== device.configurationPathEvidenceReference.trim()) {
    throw new Error("Rollback eligibility must use the device's persisted configuration-path evidence reference.");
  }
  const evidenceReference = redactAuditDetails(draft.evidenceReference);
  if (evidenceReference === "Sensitive details were redacted.") {
    throw new Error("Rollback eligibility evidence reference cannot contain sensitive values.");
  }
  const db = await requireDatabase();
  await db.insert(deviceRollbackEligibilityAssessments).values({
    deviceId,
    rollbackArtifactHash: draft.rollbackArtifactHash.trim(),
    configurationPathReference: redactAuditDetails(draft.configurationPathReference),
    targetFactsHash: draft.targetFactsHash,
    scopeHash: draft.scopeHash,
    decision: draft.decision,
    evidenceReference,
    humanReviewer: actorLabel(actor),
    assessedAt: draft.assessedAt,
  });
  await appendAuditEvent(projectId, actor, "device.rollback_eligibility_assessed", `Action-specific rollback eligibility recorded with decision ${draft.decision}.`);
  return listDeviceRollbackEligibilityAssessments(projectId, deviceId, actor.id);
}

export async function listChangePlans(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  return db.select().from(changePlans).where(eq(changePlans.projectId, projectId)).orderBy(desc(changePlans.updatedAt));
}

export async function createChangePlan(projectId: number, draft: ChangePlanDraft, actor: AuditActor) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) return undefined;
  const sectorProfile = project.sectorProfile as "unselected" | SectorProfileId;
  const sectorInputs = parseSectorInputs(project.sectorInputs);
  const sectorBlocker = getSectorPlanBlocker(sectorProfile, sectorInputs);
  if (sectorBlocker) throw new Error(sectorBlocker);
  if (sectorProfile === "unselected") throw new Error("A sector profile is required before creating a change plan.");
  if (!project.sectorInputsUpdatedAt || !isSectorReviewCurrent(project.sectorInputsUpdatedAt)) {
    throw new Error("Sector profile review is stale or missing; refresh the human-supplied sector inputs before creating a change plan.");
  }
  const sectorSnapshot = buildSectorReviewSnapshot(sectorProfile, sectorInputs);
  const sectorInputsHash = createHash("sha256").update(JSON.stringify({ profile: sectorProfile, inputs: sectorInputs })).digest("hex");
  const deviceRecord = await getManagedDeviceForUser(draft.deviceId, actor.id);
  if (!deviceRecord || deviceRecord.project.id !== projectId) return undefined;
  if (deviceRecord.device.factState !== "observed" || !deviceRecord.device.factsHash) {
    throw new Error("A change plan requires observed device facts and a facts hash.");
  }
  if (!deviceRecord.device.capabilityVerified) {
    throw new Error("A change plan requires explicit device capability verification for the observed platform and version.");
  }
  if (!deviceRecord.device.capabilityEvidenceReference || !deviceRecord.device.licenseEvidenceReference || !deviceRecord.device.configurationPathEvidenceReference) {
    throw new Error("A change plan requires capability, license, and configuration-path evidence references for the observed device.");
  }
  const db = await requireDatabase();
  await db.insert(changePlans).values({
    projectId,
    deviceId: draft.deviceId,
    name: draft.name.trim(),
    artifactHash: draft.artifactHash.trim(),
    targetFactsHash: deviceRecord.device.factsHash,
    scopeHash: draft.scopeHash.trim(),
    virtualValidationState: "not_tested",
    releaseState: "draft",
    sectorProfileSnapshot: JSON.stringify(sectorSnapshot),
    sectorInputsHash,
    sectorReviewState: "current",
    sectorReviewedAt: project.sectorInputsUpdatedAt,
  });
  await appendAuditEvent(projectId, actor, "change_plan.created", "A change plan was created from observed device facts.");
  return listChangePlans(projectId, actor.id);
}

async function getChangePlanForUser(changePlanId: number, ownerId: number) {
  const db = await requireDatabase();
  const result = await db
    .select({ plan: changePlans, project: networkProjects })
    .from(changePlans)
    .innerJoin(networkProjects, eq(changePlans.projectId, networkProjects.id))
    .where(and(eq(changePlans.id, changePlanId), eq(networkProjects.ownerId, ownerId)))
    .limit(1);
  return result[0];
}

export async function recordVirtualTest(projectId: number, changePlanId: number, draft: VirtualTestDraft, actor: AuditActor) {
  const planRecord = await getChangePlanForUser(changePlanId, actor.id);
  if (!planRecord || planRecord.project.id !== projectId) return undefined;
  const plan = planRecord.plan;
  if (plan.artifactHash !== draft.artifactHash || plan.targetFactsHash !== draft.targetFactsHash || plan.scopeHash !== draft.scopeHash) {
    throw new Error("Virtual-test evidence does not match the change plan artifact, target facts, or scope.");
  }
  const db = await requireDatabase();
  await db.insert(virtualTestRuns).values({
    changePlanId,
    state: draft.state,
    adapterKind: draft.adapterKind.trim(),
    fidelityLabel: draft.fidelityLabel.trim(),
    artifactHash: draft.artifactHash.trim(),
    targetFactsHash: draft.targetFactsHash.trim(),
    scopeHash: draft.scopeHash.trim(),
    detail: redactAuditDetails(draft.detail),
  });
  await db
    .update(changePlans)
    .set({ virtualValidationState: draft.state, releaseState: draft.state === "test_failed" ? "blocked" : "draft", updatedAt: new Date() })
    .where(eq(changePlans.id, changePlanId));
  await appendAuditEvent(projectId, actor, "virtual_test.recorded", `Virtual test recorded with state ${draft.state}.`);
  return getChangePlanForUser(changePlanId, actor.id);
}

const VIRTUAL_TEST_MAX_AGE_MS = 24 * 60 * 60 * 1000;

function isRecentEvidence(value: Date | null | undefined, now = new Date()): boolean {
  if (!value || !Number.isFinite(value.getTime())) return false;
  const age = now.getTime() - value.getTime();
  return age >= 0 && age <= VIRTUAL_TEST_MAX_AGE_MS;
}

export async function getChangePlanApprovalReadiness(changePlanId: number, ownerId: number) {
  const planRecord = await getChangePlanForUser(changePlanId, ownerId);
  if (!planRecord) return undefined;
  const deviceRecord = await getManagedDeviceForUser(planRecord.plan.deviceId, ownerId);
  if (!deviceRecord) return undefined;
  const db = await requireDatabase();
  const latestTests = await db
    .select()
    .from(virtualTestRuns)
    .where(eq(virtualTestRuns.changePlanId, changePlanId))
    .orderBy(desc(virtualTestRuns.observedAt))
    .limit(1);
  const latestTest = latestTests[0];
  const latestBackupReceipts = planRecord.plan.backupVerified
    ? await db
      .select()
      .from(changePlanBackupReceipts)
      .where(eq(changePlanBackupReceipts.changePlanId, changePlanId))
      .orderBy(desc(changePlanBackupReceipts.verifiedAt))
      .limit(1)
    : [];
  const latestBackupReceipt = latestBackupReceipts[0];
  const backupReceiptMatches = Boolean(latestBackupReceipt)
    && latestBackupReceipt.verificationState === "verified"
    && latestBackupReceipt.targetFactsHash === planRecord.plan.targetFactsHash
    && latestBackupReceipt.scopeHash === planRecord.plan.scopeHash
    && latestBackupReceipt.automaticCapturePermitted === false;
  const scenarios = await db
    .select()
    .from(benchmarkScenarios)
    .where(eq(benchmarkScenarios.projectId, planRecord.project.id))
    .orderBy(desc(benchmarkScenarios.updatedAt));
  const benchmarkCoverageCurrent = scenarios.some(scenario => {
    const matchesTarget = scenario.vendorFamily === deviceRecord.device.observedVendor.toLowerCase()
      && scenario.platform === deviceRecord.device.observedPlatform
      && scenario.model === deviceRecord.device.observedModel
      && scenario.softwareVersion === deviceRecord.device.observedVersion
      && scenario.sectorProfile === planRecord.project.sectorProfile;
    return matchesTarget && assessBenchmarkCoverage(scenario).status === "measured_coverage";
  });
  const targetFactsCurrent = deviceRecord.device.factState === "observed"
    && deviceRecord.device.factsHash === planRecord.plan.targetFactsHash
    && isRecentEvidence(deviceRecord.device.lastObservedAt);
  const virtualTestScopeMatches = Boolean(latestTest)
    && latestTest.artifactHash === planRecord.plan.artifactHash
    && latestTest.targetFactsHash === planRecord.plan.targetFactsHash
    && latestTest.scopeHash === planRecord.plan.scopeHash;
  const virtualTestCurrent = isRecentEvidence(latestTest?.observedAt);
  const baseDecision = evaluateApprovalReadiness({
    requirementsComplete: planRecord.project.requirementsComplete === 100,
    targetFactsCurrent,
    deviceCapabilityVerified: deviceRecord.device.capabilityVerified,
    virtualValidation: planRecord.plan.virtualValidationState,
    virtualTestScopeMatches,
    virtualTestCurrent,
    backupVerified: planRecord.plan.backupVerified && backupReceiptMatches,
    maintenanceWindowValid: planRecord.plan.maintenanceWindowValid,
  });
  const decision = benchmarkCoverageCurrent
    ? baseDecision
    : { status: "blocked" as const, blockers: [...baseDecision.blockers, "No matching measured benchmark scenario meets its recorded acceptance criteria for the observed vendor, platform, model, version, and sector scope."] };
  return {
    changePlanId,
    releaseState: planRecord.plan.releaseState,
    decision,
    evidence: {
      targetFactsCurrent,
      deviceCapabilityVerified: deviceRecord.device.capabilityVerified,
      virtualTestScopeMatches,
      virtualTestCurrent,
      backupVerified: planRecord.plan.backupVerified && backupReceiptMatches,
      backupReceiptMatches,
      maintenanceWindowValid: planRecord.plan.maintenanceWindowValid,
      benchmarkCoverageCurrent,
      latestVirtualTestState: latestTest?.state || planRecord.plan.virtualValidationState,
    },
  };
}

/**
 * Evaluates preparation for a human-controlled change without exposing an upload
 * operation. Automated configuration upload is denied in every outcome, including
 * a fully evidenced and human-approved plan.
 */
export async function prepareDeployment(changePlanId: number, actor: AuditActor) {
  const planRecord = await getChangePlanForUser(changePlanId, actor.id);
  if (!planRecord) return undefined;
  const readiness = await getChangePlanApprovalReadiness(changePlanId, actor.id);
  if (!readiness) return undefined;

  const blockers = [...readiness.decision.blockers];
  if (planRecord.plan.releaseState !== "approved") {
    blockers.push("A recorded human change-plan approval is required before any human-controlled execution may be considered.");
  }

  const status = blockers.length === 0 ? "human_execution_required" : "blocked";
  await appendAuditEvent(
    planRecord.project.id,
    actor,
    "change_plan.automatic_upload_blocked",
    status === "blocked"
      ? `Automatic upload remains blocked. ${blockers.join(" ")}`
      : "Automatic upload remains blocked even though evidence gates are complete; an authorized human executor must use an approved external change process.",
  );

  return {
    changePlanId,
    status,
    automaticUploadAllowed: false as const,
    blockers,
    readiness,
    requiredHumanAction: "An authorized human executor must follow the approved external change process; this control plane does not upload configuration or execute production changes.",
  };
}

/** List external backup receipts without exposing backup bytes, device credentials, or a capture action. */
export async function listBackupReceipts(changePlanId: number, ownerId: number) {
  const planRecord = await getChangePlanForUser(changePlanId, ownerId);
  if (!planRecord) return undefined;
  const db = await requireDatabase();
  return db
    .select()
    .from(changePlanBackupReceipts)
    .where(eq(changePlanBackupReceipts.changePlanId, changePlanId))
    .orderBy(desc(changePlanBackupReceipts.verifiedAt));
}

/** Record a human-supplied external backup receipt; verified receipts alone may satisfy the plan backup gate. */
export async function recordBackupReceipt(changePlanId: number, draft: BackupReceiptDraft, actor: AuditActor) {
  const planRecord = await getChangePlanForUser(changePlanId, actor.id);
  if (!planRecord) return undefined;
  if (draft.targetFactsHash !== planRecord.plan.targetFactsHash || draft.scopeHash !== planRecord.plan.scopeHash) {
    throw new Error("Backup receipt hashes must exactly match the change-plan target facts and approved scope.");
  }
  const backupReference = redactAuditDetails(draft.backupReference);
  if (backupReference === "Sensitive details were redacted.") {
    throw new Error("Backup receipt reference cannot contain sensitive values.");
  }
  const db = await requireDatabase();
  await db.insert(changePlanBackupReceipts).values({
    changePlanId,
    backupReference,
    backupArtifactHash: draft.backupArtifactHash,
    targetFactsHash: draft.targetFactsHash,
    scopeHash: draft.scopeHash,
    verificationState: draft.verificationState,
    humanVerifier: actorLabel(actor),
    automaticCapturePermitted: false,
  });
  if (draft.verificationState === "verified") {
    await db.update(changePlans).set({ backupVerified: true, updatedAt: new Date() }).where(eq(changePlans.id, changePlanId));
  }
  if (draft.verificationState === "rejected") {
    await db.update(changePlans).set({ backupVerified: false, updatedAt: new Date() }).where(eq(changePlans.id, changePlanId));
  }
  await appendAuditEvent(
    planRecord.project.id,
    actor,
    "change_plan.backup_receipt_recorded",
    draft.verificationState === "verified"
      ? "Human-verified external backup receipt recorded; no backup capture was initiated by the control plane."
      : `External backup receipt recorded with state ${draft.verificationState}; the control plane did not capture a backup.`,
  );
  return listBackupReceipts(changePlanId, actor.id);
}

/** List bounded rollback-review records; these records never assert a rollback was executed. */
export async function listRollbackReviews(changePlanId: number, ownerId: number) {
  const planRecord = await getChangePlanForUser(changePlanId, ownerId);
  if (!planRecord) return undefined;
  const db = await requireDatabase();
  return db
    .select()
    .from(changePlanRollbackReviews)
    .where(eq(changePlanRollbackReviews.changePlanId, changePlanId))
    .orderBy(desc(changePlanRollbackReviews.reviewedAt));
}

/** Record a human rollback-review packet that remains externally executed and permanently non-automatic. */
export async function recordRollbackReview(changePlanId: number, draft: RollbackReviewDraft, actor: AuditActor) {
  const planRecord = await getChangePlanForUser(changePlanId, actor.id);
  if (!planRecord) return undefined;
  if (!planRecord.plan.backupVerified) {
    throw new Error("A rollback review requires a verified backup on the change plan.");
  }
  if (draft.targetFactsHash !== planRecord.plan.targetFactsHash || draft.scopeHash !== planRecord.plan.scopeHash) {
    throw new Error("Rollback review hashes must exactly match the change-plan target facts and approved scope.");
  }
  const db = await requireDatabase();
  await db.insert(changePlanRollbackReviews).values({
    changePlanId,
    rollbackScopeReference: redactAuditDetails(draft.rollbackScopeReference),
    rollbackArtifactHash: draft.rollbackArtifactHash,
    targetFactsHash: draft.targetFactsHash,
    scopeHash: draft.scopeHash,
    backupEvidenceReference: redactAuditDetails(draft.backupEvidenceReference),
    trigger: redactAuditDetails(draft.trigger),
    reviewState: draft.reviewState,
    humanReviewer: actorLabel(actor),
    automaticExecutionPermitted: false,
  });
  await appendAuditEvent(planRecord.project.id, actor, "change_plan.rollback_review_recorded", "Scoped rollback review was recorded; automatic rollback remains prohibited.");
  return listRollbackReviews(changePlanId, actor.id);
}

/** List prepared external rollback packets; no entry represents an executed rollback. */
export async function listRollbackPreparations(changePlanId: number, ownerId: number) {
  const planRecord = await getChangePlanForUser(changePlanId, ownerId);
  if (!planRecord) return undefined;
  const db = await requireDatabase();
  return db
    .select()
    .from(changePlanRollbackPreparations)
    .where(eq(changePlanRollbackPreparations.changePlanId, changePlanId))
    .orderBy(desc(changePlanRollbackPreparations.preparedAt));
}

/** Build an eligibility-bound external rollback packet without connecting to or changing a device. */
export async function prepareScopedRollback(changePlanId: number, draft: ScopedRollbackPreparationDraft, actor: AuditActor) {
  const planRecord = await getChangePlanForUser(changePlanId, actor.id);
  if (!planRecord) return undefined;
  const db = await requireDatabase();
  const reviewRows = await db
    .select()
    .from(changePlanRollbackReviews)
    .where(and(eq(changePlanRollbackReviews.id, draft.rollbackReviewId), eq(changePlanRollbackReviews.changePlanId, changePlanId)))
    .limit(1);
  const review = reviewRows[0];
  if (!review || review.reviewState !== "reviewed") {
    throw new Error("A matching human-reviewed rollback review is required before preparing an external rollback packet.");
  }
  const verificationRows = await db
    .select()
    .from(postChangeVerificationRuns)
    .where(eq(postChangeVerificationRuns.changePlanId, changePlanId))
    .orderBy(desc(postChangeVerificationRuns.observedAt));
  if (!verificationRows.some(record => record.rollbackReviewRequired)) {
    throw new Error("An observed failed or non-verifiable post-change verification must require rollback review before rollback preparation.");
  }
  const backupRows = await db
    .select()
    .from(changePlanBackupReceipts)
    .where(eq(changePlanBackupReceipts.changePlanId, changePlanId))
    .orderBy(desc(changePlanBackupReceipts.verifiedAt));
  const matchingBackup = backupRows.find(receipt => receipt.verificationState === "verified"
    && receipt.targetFactsHash === planRecord.plan.targetFactsHash
    && receipt.scopeHash === planRecord.plan.scopeHash
    && receipt.automaticCapturePermitted === false);
  if (!planRecord.plan.backupVerified || !matchingBackup) {
    throw new Error("A matching human-verified external backup receipt is required before rollback preparation.");
  }
  const eligibilityRows = await db
    .select()
    .from(deviceRollbackEligibilityAssessments)
    .where(eq(deviceRollbackEligibilityAssessments.deviceId, planRecord.plan.deviceId))
    .orderBy(desc(deviceRollbackEligibilityAssessments.assessedAt));
  const matchingEligibility = eligibilityRows.find(assessment => assessment.decision === "eligible"
    && assessment.rollbackArtifactHash === draft.rollbackArtifactHash
    && assessment.targetFactsHash === planRecord.plan.targetFactsHash
    && assessment.scopeHash === planRecord.plan.scopeHash);
  if (!matchingEligibility) {
    throw new Error("A matching action-specific rollback eligibility decision is required before external rollback preparation.");
  }
  const hashesMatch = draft.targetFactsHash === planRecord.plan.targetFactsHash
    && draft.scopeHash === planRecord.plan.scopeHash
    && draft.rollbackArtifactHash === review.rollbackArtifactHash;
  if (!hashesMatch) {
    throw new Error("Rollback preparation must exactly match the reviewed rollback artifact and the change-plan target facts and scope.");
  }
  await db.insert(changePlanRollbackPreparations).values({
    changePlanId,
    rollbackReviewId: review.id,
    rollbackArtifactHash: draft.rollbackArtifactHash,
    targetFactsHash: draft.targetFactsHash,
    scopeHash: draft.scopeHash,
    eligibilityState: "ready_for_human_execution",
    humanExecutionRequired: true,
    automaticExecutionPermitted: false,
    preparedBy: actorLabel(actor),
  });
  await appendAuditEvent(planRecord.project.id, actor, "change_plan.rollback_external_packet_prepared", "Scoped rollback packet is ready for human-controlled external execution; the control plane cannot execute it.");
  return listRollbackPreparations(changePlanId, actor.id);
}

/** Lists observed verification records without inferring that a production action occurred. */
export async function listPostChangeVerifications(changePlanId: number, ownerId: number) {
  const planRecord = await getChangePlanForUser(changePlanId, ownerId);
  if (!planRecord) return undefined;
  const db = await requireDatabase();
  return db
    .select()
    .from(postChangeVerificationRuns)
    .where(eq(postChangeVerificationRuns.changePlanId, changePlanId))
    .orderBy(desc(postChangeVerificationRuns.observedAt));
}

/**
 * Records an externally observed verification result after recorded human approval.
 * It neither initiates a probe nor executes a rollback. A failed or unverifiable
 * observation closes the plan's automated path and flags human rollback review.
 */
export async function recordPostChangeVerification(changePlanId: number, draft: PostChangeVerificationDraft, actor: AuditActor) {
  const planRecord = await getChangePlanForUser(changePlanId, actor.id);
  if (!planRecord) return undefined;
  if (planRecord.plan.releaseState !== "approved" || !planRecord.plan.humanApprover) {
    throw new Error("Post-change verification evidence requires a recorded human change-plan approval.");
  }
  const evidenceReference = redactAuditDetails(draft.evidenceReference);
  if (evidenceReference === "Sensitive details were redacted.") {
    throw new Error("Post-change verification evidence reference cannot contain sensitive values.");
  }
  const observedOutcome = redactAuditDetails(draft.observedOutcome);
  if (observedOutcome === "Sensitive details were redacted.") {
    throw new Error("Observed verification outcome cannot contain sensitive values.");
  }
  const expectedOutcome = redactAuditDetails(draft.expectedOutcome);
  if (expectedOutcome === "Sensitive details were redacted.") {
    throw new Error("Expected verification outcome cannot contain sensitive values.");
  }
  const rollbackReviewRequired = draft.state === "failed" || draft.state === "not_verifiable";
  const db = await requireDatabase();
  await db.insert(postChangeVerificationRuns).values({
    changePlanId,
    state: draft.state,
    verificationType: draft.verificationType,
    expectedOutcome,
    observedOutcome,
    evidenceReference,
    rollbackReviewRequired,
    recordedBy: actorLabel(actor),
    observedAt: draft.observedAt,
  });
  if (rollbackReviewRequired) {
    await db.update(changePlans).set({ releaseState: "blocked", updatedAt: new Date() }).where(eq(changePlans.id, changePlanId));
  }
  await appendAuditEvent(
    planRecord.project.id,
    actor,
    "post_change_verification.recorded",
    rollbackReviewRequired
      ? "Observed post-change verification requires human rollback review; no rollback was executed."
      : `Observed post-change verification recorded with state ${draft.state}.`,
  );
  return listPostChangeVerifications(changePlanId, actor.id);
}

export async function requestChangePlanApproval(changePlanId: number, actor: AuditActor) {
  const planRecord = await getChangePlanForUser(changePlanId, actor.id);
  if (!planRecord) return undefined;
  const readiness = await getChangePlanApprovalReadiness(changePlanId, actor.id);
  if (!readiness || readiness.decision.status !== "ready_for_human_approval") {
    const blockers = readiness?.decision.blockers.join(" ") || "Change plan was not found.";
    throw new Error(`Change plan approval is blocked: ${blockers}`);
  }
  const db = await requireDatabase();
  await db.update(changePlans).set({ releaseState: "ready_for_approval", updatedAt: new Date() }).where(eq(changePlans.id, changePlanId));
  await appendAuditEvent(planRecord.project.id, actor, "change_plan.approval_requested", "Change-plan approval was requested after all readiness gates passed.");
  return getChangePlanApprovalReadiness(changePlanId, actor.id);
}

export async function approveChangePlan(changePlanId: number, actor: AuditActor) {
  const planRecord = await getChangePlanForUser(changePlanId, actor.id);
  if (!planRecord) return undefined;
  if (planRecord.plan.releaseState !== "ready_for_approval") {
    throw new Error("A change plan must be ready for human approval before it can be approved.");
  }
  const db = await requireDatabase();
  await db.update(changePlans).set({ releaseState: "approved", humanApprover: actorLabel(actor), approvedAt: new Date(), updatedAt: new Date() }).where(eq(changePlans.id, changePlanId));
  await appendAuditEvent(planRecord.project.id, actor, "change_plan.approved", "Human approval was recorded for the change plan.");
  return { changePlanId, approved: true, approver: actorLabel(actor) } as const;
}

export async function approveDeployment(projectId: number, actor: AuditActor) {
  const db = await requireDatabase();
  const result = await db.select().from(networkProjects).where(eq(networkProjects.id, projectId)).limit(1);
  const project = result[0];
  if (!project) {
    return undefined;
  }
  if (project.requirementsComplete < 100) {
    throw new Error("Requirements must be complete before approval can be granted.");
  }
  await db
    .update(networkProjects)
    .set({
      approvalState: "approved",
      status: "approved",
      approvedBy: actorLabel(actor),
      approvedAt: new Date(),
      updatedAt: new Date(),
    })
    .where(eq(networkProjects.id, projectId));
  await appendAuditEvent(projectId, actor, "deployment.approved", "Deployment gate approval was granted.");
  return projectId;
}

export async function deleteProjectForUser(projectId: number, actor: AuditActor): Promise<boolean> {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) {
    return false;
  }
  await appendAuditEvent(projectId, actor, "project.deleted", "Project record was deleted.");
  const db = await requireDatabase();
  await db.delete(networkProjects).where(and(eq(networkProjects.id, projectId), eq(networkProjects.ownerId, actor.id)));
  return true;
}

export type DiscoveryRunDraft = {
  siteId: number;
  discoveryScopeId: number;
  evidenceSummary?: string;
  evidenceHash?: string;
  ambiguousCount?: number;
  unsupportedCount?: number;
};

export type DiscoveryRunState = "queued" | "running" | "completed" | "partial" | "failed" | "blocked";

const discoveryStateTransitions: Record<DiscoveryRunState, readonly DiscoveryRunState[]> = {
  queued: ["running", "blocked"],
  running: ["completed", "partial", "failed", "blocked"],
  completed: [],
  partial: [],
  failed: [],
  blocked: [],
};

export function canTransitionDiscoveryRun(from: DiscoveryRunState, to: DiscoveryRunState): boolean {
  return discoveryStateTransitions[from].includes(to);
}

export function redactDiscoveryEvidence(value: string): string {
  return redactAuditDetails(value);
}

async function getDiscoveryRunForActor(runId: number, actorId: number) {
  const db = await requireDatabase();
  const result = await db
    .select({ run: discoveryRuns, projectId: networkProjects.id })
    .from(discoveryRuns)
    .innerJoin(managedSites, eq(discoveryRuns.siteId, managedSites.id))
    .innerJoin(networkProjects, eq(managedSites.projectId, networkProjects.id))
    .where(and(eq(discoveryRuns.id, runId), eq(networkProjects.ownerId, actorId)))
    .limit(1);
  return result[0];
}

export async function createDiscoveryRun(projectId: number, draft: DiscoveryRunDraft, actor: AuditActor) {
  const db = await requireDatabase();
  const site = await db
    .select({ id: managedSites.id })
    .from(managedSites)
    .innerJoin(networkProjects, eq(managedSites.projectId, networkProjects.id))
    .where(and(eq(managedSites.id, draft.siteId), eq(managedSites.projectId, projectId), eq(networkProjects.ownerId, actor.id)))
    .limit(1);
  if (!site[0]) return undefined;
  const scopes = await db
    .select({ scope: authorizedDiscoveryScopes })
    .from(authorizedDiscoveryScopes)
    .innerJoin(managedSites, eq(authorizedDiscoveryScopes.siteId, managedSites.id))
    .innerJoin(networkProjects, eq(managedSites.projectId, networkProjects.id))
    .where(and(
      eq(authorizedDiscoveryScopes.id, draft.discoveryScopeId),
      eq(authorizedDiscoveryScopes.projectId, projectId),
      eq(authorizedDiscoveryScopes.siteId, draft.siteId),
      eq(authorizedDiscoveryScopes.status, "active"),
      eq(networkProjects.ownerId, actor.id),
    ))
    .limit(1);
  const scope = scopes[0]?.scope;
  if (!scope) throw new Error("Discovery runs require a saved active authorized scope for the selected site.");
  const values: InsertDiscoveryRun = {
    siteId: draft.siteId,
    discoveryScopeId: draft.discoveryScopeId,
    mode: "read_only",
    state: "queued",
    scopeHash: scope.scopeHash,
    evidenceSummary: redactDiscoveryEvidence(draft.evidenceSummary || ""),
    evidenceHash: draft.evidenceHash?.trim() || "",
    ambiguousCount: draft.ambiguousCount || 0,
    unsupportedCount: draft.unsupportedCount || 0,
  };
  const inserted = await db.insert(discoveryRuns).values(values).$returningId();
  const runId = inserted[0]?.id;
  if (!runId) throw new Error("The discovery run could not be created.");
  await appendAuditEvent(projectId, actor, "discovery.run_created", "A read-only discovery run was queued.");
  return getDiscoveryRunForActor(runId, actor.id);
}

export async function listDiscoveryRuns(projectId: number, ownerId: number) {
  const project = await getProjectForUser(projectId, ownerId);
  if (!project) return undefined;
  const db = await requireDatabase();
  return db
    .select({ run: discoveryRuns, siteName: managedSites.name })
    .from(discoveryRuns)
    .innerJoin(managedSites, eq(discoveryRuns.siteId, managedSites.id))
    .where(eq(managedSites.projectId, projectId))
    .orderBy(desc(discoveryRuns.createdAt));
}

export async function transitionDiscoveryRun(
  runId: number,
  nextState: DiscoveryRunState,
  draft: Pick<DiscoveryRunDraft, "evidenceSummary" | "evidenceHash" | "ambiguousCount" | "unsupportedCount">,
  actor: AuditActor,
) {
  const existing = await getDiscoveryRunForActor(runId, actor.id);
  if (!existing) return undefined;
  const currentState = existing.run.state as DiscoveryRunState;
  if (!canTransitionDiscoveryRun(currentState, nextState)) {
    throw new Error(`Invalid discovery-run transition from ${currentState} to ${nextState}.`);
  }
  const db = await requireDatabase();
  const now = new Date();
  await db.update(discoveryRuns).set({
    state: nextState,
    evidenceSummary: draft.evidenceSummary === undefined ? existing.run.evidenceSummary : redactDiscoveryEvidence(draft.evidenceSummary),
    evidenceHash: draft.evidenceHash === undefined ? existing.run.evidenceHash : draft.evidenceHash.trim(),
    ambiguousCount: draft.ambiguousCount ?? existing.run.ambiguousCount,
    unsupportedCount: draft.unsupportedCount ?? existing.run.unsupportedCount,
    startedAt: currentState === "queued" && nextState === "running" ? now : existing.run.startedAt,
    completedAt: ["completed", "partial", "failed", "blocked"].includes(nextState) ? now : existing.run.completedAt,
    updatedAt: now,
  }).where(eq(discoveryRuns.id, runId));
  await appendAuditEvent(existing.projectId, actor, "discovery.run_state_changed", `Discovery run moved from ${currentState} to ${nextState}.`);
  return getDiscoveryRunForActor(runId, actor.id);
}

export async function listAuditEventsForUser(ownerId: number, page: number, pageSize: number) {
  const db = await requireDatabase();
  const filter = or(eq(networkProjects.ownerId, ownerId), eq(auditEvents.actorId, ownerId));
  const items = await db
    .select({
      id: auditEvents.id,
      projectId: auditEvents.projectId,
      projectName: sql<string>`coalesce(${networkProjects.name}, 'Deleted project')`,
      actorName: auditEvents.actorName,
      action: auditEvents.action,
      details: auditEvents.details,
      createdAt: auditEvents.createdAt,
    })
    .from(auditEvents)
    .leftJoin(networkProjects, eq(auditEvents.projectId, networkProjects.id))
    .where(filter)
    .orderBy(desc(auditEvents.createdAt))
    .limit(pageSize)
    .offset((page - 1) * pageSize);
  const totals = await db
    .select({ value: count() })
    .from(auditEvents)
    .leftJoin(networkProjects, eq(auditEvents.projectId, networkProjects.id))
    .where(filter);
  return {
    items: items.map(item => ({ ...item, details: redactAuditDetails(item.details) })),
    page,
    pageSize,
    total: Number(totals[0]?.value || 0),
  };
}
