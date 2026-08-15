import { and, count, desc, eq, or, sql } from "drizzle-orm";
import {
  auditEvents,
  networkProjects,
  projectBomItems,
  projectConfigArtifacts,
  projectDesignDetails,
  type InsertNetworkProject,
} from "../drizzle/schema";
import { getDb } from "./db";

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
