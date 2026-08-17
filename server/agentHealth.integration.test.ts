import { createHash, generateKeyPairSync, sign } from "node:crypto";
import { beforeEach, describe, expect, it, vi } from "vitest";

const selectResults: unknown[][] = [];
const insertCalls: unknown[] = [];

function queryBuilder() {
  const builder: Record<string, (...args: unknown[]) => unknown> = {};
  builder.from = () => builder;
  builder.innerJoin = () => builder;
  builder.where = () => builder;
  builder.limit = async () => selectResults.shift() || [];
  return builder;
}

const fakeDb = {
  select: vi.fn(() => queryBuilder()),
  insert: vi.fn(() => ({ values: (value: unknown) => { insertCalls.push(value); return Promise.resolve(); } })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { ingestSignedSiteAgentHealth } = await import("./agentHealth");

function canonicalPayload(input: Record<string, string | boolean | number>) {
  const values: Record<string, string> = {
    agent_id: String(input.agentId),
    detail: String(input.detail),
    enrollment_id: String(input.enrollmentId),
    healthy: String(input.healthy),
    mode: String(input.mode),
    observed_at: String(input.observedAt),
    scope_hash: String(input.scopeHash),
    site_id: String(input.siteId),
  };
  return Buffer.from(Object.keys(values).sort().map(key => `${key}=${values[key]}`).join("\n"), "utf8");
}

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("signed local-agent health integration", () => {
  it("accepts a correctly signed read-only health report and persists only secret-free health fields", async () => {
    const keys = generateKeyPairSync("ed25519");
    const publicKeyPem = keys.publicKey.export({ type: "spki", format: "pem" }).toString();
    const fingerprint = createHash("sha256").update(publicKeyPem, "utf8").digest("hex");
    const input = { enrollmentId: "enrollment-agent-health-0001", agentId: "agent-001", siteId: 7, scopeHash: "authorized-scope-hash-001", healthy: true, mode: "read_only", detail: "Active enrollment matches the acknowledged scope.", observedAt: "2026-08-17T00:00:00+00:00", signature: "" };
    input.signature = sign(null, canonicalPayload(input), keys.privateKey).toString("base64");
    selectResults.push([{ enrollment: { id: 4, enrollmentId: input.enrollmentId, agentId: input.agentId, siteId: input.siteId, scopeHash: input.scopeHash, status: "active", expiresAt: new Date("2099-01-01T00:00:00Z"), agentFingerprint: fingerprint, agentPublicKeyPem: publicKeyPem }, site: { id: 7 } }]);

    const result = await ingestSignedSiteAgentHealth(input);

    expect(result.accepted).toBe(true);
    expect(insertCalls[0]).toMatchObject({ enrollmentId: 4, healthy: true, mode: "read_only", detail: input.detail });
    expect(JSON.stringify(insertCalls[0])).not.toContain("private");
  });

  it("rejects a report with an invalid detached signature without storing a health record", async () => {
    const keys = generateKeyPairSync("ed25519");
    const publicKeyPem = keys.publicKey.export({ type: "spki", format: "pem" }).toString();
    const input = { enrollmentId: "enrollment-agent-health-0002", agentId: "agent-002", siteId: 8, scopeHash: "authorized-scope-hash-002", healthy: false, mode: "read_only", detail: "Enrollment status needs attention.", observedAt: "2026-08-17T00:00:00+00:00", signature: "invalid-signature" };
    selectResults.push([{ enrollment: { id: 5, enrollmentId: input.enrollmentId, agentId: input.agentId, siteId: input.siteId, scopeHash: input.scopeHash, status: "active", expiresAt: new Date("2099-01-01T00:00:00Z"), agentPublicKeyPem: publicKeyPem }, site: { id: 8 } }]);

    const result = await ingestSignedSiteAgentHealth(input);

    expect(result.accepted).toBe(false);
    expect(result.reason).toContain("signature");
    expect(insertCalls).toHaveLength(0);
  });
});
