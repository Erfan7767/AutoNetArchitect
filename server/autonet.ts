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
  virtualTestRuns,
  type InsertNetworkProject,
} from "../drizzle/schema";
import { getDb } from "./db";
import { assessSectorProfileInputs, type SectorProfileId } from "./sectorProfiles";

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
  vendor: string;
  deviceName: string;
  artifactSummary: string;
  artifactPreview: string;
  featureGuard: "pass" | "blocked" | "unknown";
  unsupportedFeatureLog: string;
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
  await db
    .update(networkProjects)
    .set({ sectorProfile: draft.sectorProfile, sectorInputs: JSON.stringify(normalizedInputs), updatedAt: new Date() })
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

export async function addConfigArtifact(projectId: number, draft: ConfigArtifactDraft, actor: AuditActor) {
  const project = await getProjectForUser(projectId, actor.id);
  if (!project) return undefined;
  const db = await requireDatabase();
  await db.insert(projectConfigArtifacts).values({
    projectId,
    vendor: draft.vendor.trim(),
    deviceName: draft.deviceName.trim(),
    artifactSummary: redactAuditDetails(draft.artifactSummary),
    artifactPreview: redactAuditDetails(draft.artifactPreview),
    featureGuard: draft.featureGuard,
    unsupportedFeatureLog: redactAuditDetails(draft.unsupportedFeatureLog),
  });
  await appendAuditEvent(projectId, actor, "config.artifact_added", `Config artifact recorded for ${draft.vendor.trim()}.`);
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
  const db = await requireDatabase();
  await db
    .update(managedDevices)
    .set({
      observedVendor: draft.observedVendor.trim(),
      observedPlatform: draft.observedPlatform.trim(),
      observedVersion: draft.observedVersion.trim(),
      factsHash: draft.factsHash.trim(),
      factState: draft.factState,
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
  const sectorBlocker = getSectorPlanBlocker(project.sectorProfile as "unselected" | SectorProfileId, parseSectorInputs(project.sectorInputs));
  if (sectorBlocker) throw new Error(sectorBlocker);
  const deviceRecord = await getManagedDeviceForUser(draft.deviceId, actor.id);
  if (!deviceRecord || deviceRecord.project.id !== projectId) return undefined;
  if (deviceRecord.device.factState !== "observed" || !deviceRecord.device.factsHash) {
    throw new Error("A change plan requires observed device facts and a facts hash.");
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
