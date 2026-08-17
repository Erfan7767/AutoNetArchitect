import { beforeEach, describe, expect, it, vi } from "vitest";
import type { TrpcContext } from "./_core/context";

const selectResults: unknown[][] = [];
const insertCalls: unknown[] = [];

function queryBuilder() {
  const builder: Record<string, (...args: unknown[]) => unknown> = {};
  builder.from = () => builder;
  builder.innerJoin = () => builder;
  builder.where = () => builder;
  builder.limit = async () => selectResults.shift() || [];
  builder.orderBy = async () => selectResults.shift() || [];
  return builder;
}

const fakeDb = {
  select: vi.fn(() => queryBuilder()),
  insert: vi.fn(() => ({
    values: (value: unknown) => {
      insertCalls.push(value);
      return Promise.resolve();
    },
  })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { appRouter } = await import("./routers");

function context(): TrpcContext {
  return {
    user: { id: 65, openId: "reviewer-user", email: "reviewer@example.test", name: "Engineering reviewer", loginMethod: "manus", role: "user", createdAt: new Date(), updatedAt: new Date(), lastSignedIn: new Date() },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const project = { id: 29, ownerId: 65, name: "Evidence-bound review" };
const input = {
  projectId: 29,
  reportReference: "review-29-001",
  findings: [{ specialty: "security" as const, state: "blocked" as const, decisionReference: "decision-security-29", rationale: "The evidence record is incomplete.", evidenceReferences: ["security-evidence-29"] }],
  assumptions: "No unstated configuration behavior is assumed.",
  risks: "A blocked security finding remains a release risk.",
  evidenceGaps: "Authoritative security-path evidence is missing.",
  requiredHumanActions: "Named security reviewer must resolve the evidence gap.",
};

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("engineering review reports integration", () => {
  it("persists finding counts and required human actions without releasing a change", async () => {
    const caller = appRouter.createCaller(context());
    const stored = { id: 3, projectId: 29, reportReference: input.reportReference, findingsJson: JSON.stringify(input.findings), passedCount: 0, failedCount: 0, blockedCount: 1, unresolvedCount: 0, assumptions: input.assumptions, risks: input.risks, evidenceGaps: input.evidenceGaps, requiredHumanActions: input.requiredHumanActions, recordedBy: "Engineering reviewer", recordedAt: new Date() };
    selectResults.push([project], [project], [stored]);

    const records = await caller.projects.engineeringReviewReports.record(input);

    expect(insertCalls[0]).toMatchObject({ projectId: 29, reportReference: input.reportReference, blockedCount: 1, requiredHumanActions: input.requiredHumanActions });
    expect(records[0]).toMatchObject({ blockedCount: 1, requiredHumanActions: input.requiredHumanActions });
    expect(JSON.parse(records[0].findingsJson)).toEqual(input.findings);
  });

  it("rejects an empty findings collection before persistence", async () => {
    const caller = appRouter.createCaller(context());

    await expect(caller.projects.engineeringReviewReports.record({ ...input, findings: [] })).rejects.toThrow();
    expect(insertCalls).toHaveLength(0);
  });

  it("rejects recording where the requested project is not owned by the reviewer", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([]);

    await expect(caller.projects.engineeringReviewReports.record(input)).rejects.toThrow("Project not found");
    expect(insertCalls).toHaveLength(0);
  });
});
