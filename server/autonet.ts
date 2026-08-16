import { createHash } from "node:crypto";
import { and, count, desc, eq, or, sql } from "drizzle-orm";
import {
  auditEvents,
  changePlans,
  managedDevices,
  managedSites,
  networkProjects,
  projectBomItems,
  projectConfigArtifacts,
  projectDesignDetails,
  postChangeVerificationRuns,
  virtualTestRuns,
  type InsertDiscoveryRun,
  type InsertNetworkProject,
  discoveryRuns,
} from "../drizzle/schema";
import { getDb } from "./db";
import { evaluateApprovalReadiness } from "./automationPolicy";
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

export type AgentTeamAuditDraft = {
  productionExecutionPermitted: false;
  agents: Array<{
    role: string;
    state: "ready" | "waiting" | "blocked" | "abstained" | "completed";
    blockers: string[];
  }>;
};

export type ManagedSiteDraft = {
  name: string;
  approvedScopeReference: string;
};

export type ManagedDeviceDraft = {
  siteId: number;
  deviceReference: string;
  managementAddress: string;
  protocol: "ssh" | "netconf" | "https_api" | "snmp";
  credentialReference: string;
};

export type DeviceObservationDraft = {
  observedVendor: string;
  observedPlatform: string;
  observedVersion: string;
  factsHash: string;
  factState: "observed" | "ambiguous" | "unreachable" | "unsupported";
  capabilityVerified: boolean;
  capabilityEvidenceReference?: string;
  licenseEvidenceReference?: string;
  configurationPathEvidenceReference?: string;
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
    throw new Error("Config artifact preparation cannot mark a feature guard as pass until an accepted exact capability decision is persisted for the device.");
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

export async function recordDeviceObservation(projectId: number, deviceId: number, draft: DeviceObservationDraft, actor: AuditActor) {
  const record = await getManagedDeviceForUser(deviceId, actor.id);
  if (!record || record.project.id !== projectId) return undefined;
  const capabilityEvidenceReference = draft.capabilityEvidenceReference?.trim() || "";
  const licenseEvidenceReference = draft.licenseEvidenceReference?.trim() || "";
  const configurationPathEvidenceReference = draft.configurationPathEvidenceReference?.trim() || "";
  if (draft.capabilityVerified && draft.factState !== "observed") {
    throw new Error("Capability verification requires an observed device fact state.");
  }
  if (draft.capabilityVerified && (!capabilityEvidenceReference || !licenseEvidenceReference || !configurationPathEvidenceReference)) {
    throw new Error("Capability verification requires capability, license, and configuration-path evidence references.");
  }
  const db = await requireDatabase();
  await db
    .update(managedDevices)
    .set({
      observedVendor: draft.observedVendor.trim(),
      observedPlatform: draft.observedPlatform.trim(),
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
  const targetFactsCurrent = deviceRecord.device.factState === "observed"
    && deviceRecord.device.factsHash === planRecord.plan.targetFactsHash
    && isRecentEvidence(deviceRecord.device.lastObservedAt);
  const virtualTestScopeMatches = Boolean(latestTest)
    && latestTest.artifactHash === planRecord.plan.artifactHash
    && latestTest.targetFactsHash === planRecord.plan.targetFactsHash
    && latestTest.scopeHash === planRecord.plan.scopeHash;
  const virtualTestCurrent = isRecentEvidence(latestTest?.observedAt);
  const decision = evaluateApprovalReadiness({
    requirementsComplete: planRecord.project.requirementsComplete === 100,
    targetFactsCurrent,
    deviceCapabilityVerified: deviceRecord.device.capabilityVerified,
    virtualValidation: planRecord.plan.virtualValidationState,
    virtualTestScopeMatches,
    virtualTestCurrent,
    backupVerified: planRecord.plan.backupVerified,
    maintenanceWindowValid: planRecord.plan.maintenanceWindowValid,
  });
  return {
    changePlanId,
    releaseState: planRecord.plan.releaseState,
    decision,
    evidence: {
      targetFactsCurrent,
      deviceCapabilityVerified: deviceRecord.device.capabilityVerified,
      virtualTestScopeMatches,
      virtualTestCurrent,
      backupVerified: planRecord.plan.backupVerified,
      maintenanceWindowValid: planRecord.plan.maintenanceWindowValid,
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
  scopeHash: string;
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
  const values: InsertDiscoveryRun = {
    siteId: draft.siteId,
    mode: "read_only",
    state: "queued",
    scopeHash: draft.scopeHash.trim(),
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
