import { createHash, createPublicKey, verify } from "node:crypto";
import { and, desc, eq } from "drizzle-orm";
import { authorizedDiscoveryScopes, managedSites, networkProjects, siteAgentEnrollments, siteAgentHealthReports } from "../drizzle/schema";
import { getDb } from "./db";
import { redactAuditDetails } from "./autonet";

export type SiteAgentProvisionDraft = {
  siteId: number;
  agentId: string;
  enrollmentId: string;
  agentFingerprint: string;
  agentPublicKeyPem: string;
  scopeHash: string;
  expiresAt: Date;
};

export type SignedAgentHealthInput = {
  enrollmentId: string;
  agentId: string;
  siteId: number;
  scopeHash: string;
  healthy: boolean;
  mode: string;
  detail: string;
  observedAt: string;
  signature: string;
};

function fingerprintPublicKey(publicKeyPem: string): string {
  return createHash("sha256").update(publicKeyPem, "utf8").digest("hex");
}

function canonicalHealthPayload(input: SignedAgentHealthInput): Buffer {
  const values: Record<string, string> = {
    agent_id: input.agentId,
    detail: input.detail,
    enrollment_id: input.enrollmentId,
    healthy: String(input.healthy),
    mode: input.mode,
    observed_at: input.observedAt,
    scope_hash: input.scopeHash,
    site_id: String(input.siteId),
  };
  return Buffer.from(Object.keys(values).sort().map(key => `${key}=${values[key]}`).join("\n"), "utf8");
}

function verifyEd25519Proof(publicKeyPem: string, payload: Buffer, signature: string): boolean {
  try {
    const key = createPublicKey(publicKeyPem);
    return key.asymmetricKeyType === "ed25519" && verify(null, payload, key, Buffer.from(signature, "base64"));
  } catch {
    return false;
  }
}

export async function listSiteAgentEnrollments(projectId: number, ownerId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database is not available.");
  return db
    .select({ enrollment: siteAgentEnrollments, siteName: managedSites.name })
    .from(siteAgentEnrollments)
    .innerJoin(managedSites, eq(siteAgentEnrollments.siteId, managedSites.id))
    .innerJoin(networkProjects, eq(siteAgentEnrollments.projectId, networkProjects.id))
    .where(and(eq(siteAgentEnrollments.projectId, projectId), eq(networkProjects.ownerId, ownerId)))
    .orderBy(desc(siteAgentEnrollments.createdAt));
}

export async function provisionSiteAgentEnrollment(projectId: number, draft: SiteAgentProvisionDraft, actor: { id: number; name?: string | null; email?: string | null }) {
  const db = await getDb();
  if (!db) throw new Error("Database is not available.");
  const siteRecord = await db
    .select({ site: managedSites, project: networkProjects })
    .from(managedSites)
    .innerJoin(networkProjects, eq(managedSites.projectId, networkProjects.id))
    .where(and(eq(managedSites.id, draft.siteId), eq(networkProjects.id, projectId), eq(networkProjects.ownerId, actor.id)))
    .limit(1);
  if (!siteRecord[0]) return undefined;
  const scope = await db
    .select()
    .from(authorizedDiscoveryScopes)
    .where(and(eq(authorizedDiscoveryScopes.projectId, projectId), eq(authorizedDiscoveryScopes.siteId, draft.siteId), eq(authorizedDiscoveryScopes.scopeHash, draft.scopeHash), eq(authorizedDiscoveryScopes.status, "active")))
    .limit(1);
  if (!scope[0]) throw new Error("Agent enrollment requires an active authorized discovery scope with the exact scope hash.");
  if (draft.expiresAt <= new Date()) throw new Error("Agent enrollment expiry must be in the future.");
  if (fingerprintPublicKey(draft.agentPublicKeyPem.trim()) !== draft.agentFingerprint) throw new Error("Agent public-key fingerprint does not match the supplied public key.");
  try {
    const key = createPublicKey(draft.agentPublicKeyPem.trim());
    if (key.asymmetricKeyType !== "ed25519") throw new Error("Agent public key must be Ed25519.");
  } catch (error) {
    if (error instanceof Error && error.message === "Agent public key must be Ed25519.") throw error;
    throw new Error("Agent public key is not valid PEM.");
  }
  await db.insert(siteAgentEnrollments).values({
    projectId,
    siteId: draft.siteId,
    agentId: draft.agentId.trim(),
    enrollmentId: draft.enrollmentId.trim(),
    agentFingerprint: draft.agentFingerprint,
    agentPublicKeyPem: draft.agentPublicKeyPem.trim(),
    scopeHash: draft.scopeHash.trim(),
    status: "active",
    expiresAt: draft.expiresAt,
  });
  await db.insert((await import("../drizzle/schema")).auditEvents).values({
    projectId,
    actorId: actor.id,
    actorName: actor.name || actor.email || `user-${actor.id}`,
    action: "site_agent.public_key_provisioned",
    details: `An Ed25519 public key was pinned for agent ${draft.agentId.trim()} against the exact authorized discovery scope. No private key or device credential was stored.`,
  });
  return listSiteAgentEnrollments(projectId, actor.id);
}

export async function listSiteAgentHealthReports(projectId: number, ownerId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database is not available.");
  return db
    .select({ report: siteAgentHealthReports, enrollment: siteAgentEnrollments, siteName: managedSites.name })
    .from(siteAgentHealthReports)
    .innerJoin(siteAgentEnrollments, eq(siteAgentHealthReports.enrollmentId, siteAgentEnrollments.id))
    .innerJoin(managedSites, eq(siteAgentEnrollments.siteId, managedSites.id))
    .innerJoin(networkProjects, eq(siteAgentEnrollments.projectId, networkProjects.id))
    .where(and(eq(siteAgentEnrollments.projectId, projectId), eq(networkProjects.ownerId, ownerId)))
    .orderBy(desc(siteAgentHealthReports.receivedAt));
}

export async function ingestSignedSiteAgentHealth(input: SignedAgentHealthInput): Promise<{ accepted: boolean; reason: string }> {
  const db = await getDb();
  if (!db) throw new Error("Database is not available.");
  const records = await db
    .select({ enrollment: siteAgentEnrollments, site: managedSites })
    .from(siteAgentEnrollments)
    .innerJoin(managedSites, eq(siteAgentEnrollments.siteId, managedSites.id))
    .where(eq(siteAgentEnrollments.enrollmentId, input.enrollmentId))
    .limit(1);
  const record = records[0];
  if (!record || record.enrollment.status !== "active") return { accepted: false, reason: "Enrollment is unknown or inactive." };
  if (record.enrollment.expiresAt <= new Date()) return { accepted: false, reason: "Enrollment has expired." };
  if (record.enrollment.agentId !== input.agentId || record.enrollment.siteId !== input.siteId || record.enrollment.scopeHash !== input.scopeHash) {
    return { accepted: false, reason: "Health identity does not match the enrolled agent and scope." };
  }
  if (input.mode !== "read_only") return { accepted: false, reason: "Only read-only agent health reports are accepted." };
  if (!verifyEd25519Proof(record.enrollment.agentPublicKeyPem, canonicalHealthPayload(input), input.signature)) {
    return { accepted: false, reason: "Health report signature did not verify against the pinned agent public key." };
  }
  await db.insert(siteAgentHealthReports).values({
    enrollmentId: record.enrollment.id,
    healthy: input.healthy,
    mode: "read_only",
    detail: redactAuditDetails(input.detail),
    observedAt: new Date(input.observedAt),
  });
  return { accepted: true, reason: "Signed read-only agent health report was accepted." };
}
