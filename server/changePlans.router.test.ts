import { describe, expect, it, vi } from "vitest";
import type { TrpcContext } from "./_core/context";

const createChangePlanMock = vi.fn();

vi.mock("./autonet", async importOriginal => ({
  ...(await importOriginal<typeof import("./autonet")>()),
  createChangePlan: createChangePlanMock,
}));

const { appRouter } = await import("./routers");

function createContext(): TrpcContext {
  return {
    user: {
      id: 11,
      openId: "reviewer-open-id",
      email: "reviewer@example.test",
      name: "Reviewer",
      loginMethod: "test",
      role: "user",
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSignedIn: new Date(),
    },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const input = {
  projectId: 1,
  deviceId: 10,
  name: "Branch edge change",
  artifactHash: "artifact-hash",
  scopeHash: "scope-hash",
};

describe("projects.changePlans.create route", () => {
  it("surfaces unselected sector profile blocking through the protected route", async () => {
    createChangePlanMock.mockRejectedValueOnce(new Error("A sector profile must be selected before a change plan can be created."));

    const caller = appRouter.createCaller(createContext());
    await expect(caller.projects.changePlans.create(input)).rejects.toThrow("sector profile must be selected");
  });

  it("surfaces incomplete sector profile blocking through the protected route", async () => {
    createChangePlanMock.mockRejectedValueOnce(new Error("Sector profile is incomplete: missing human input."));

    const caller = appRouter.createCaller(createContext());
    await expect(caller.projects.changePlans.create(input)).rejects.toThrow("Sector profile is incomplete");
    expect(createChangePlanMock).toHaveBeenCalledWith(1, input, expect.objectContaining({ id: 11, name: "Reviewer" }));
  });

  it("surfaces stale sector review blocking through the protected route", async () => {
    createChangePlanMock.mockRejectedValueOnce(new Error("Sector profile review is stale or missing; refresh the human-supplied sector inputs before creating a change plan."));

    const caller = appRouter.createCaller(createContext());
    await expect(caller.projects.changePlans.create(input)).rejects.toThrow("Sector profile review is stale or missing");
  });

  it("returns persisted sector snapshot fields for a complete scoped path", async () => {
    const persisted = {
      id: 55,
      projectId: 1,
      deviceId: 10,
      name: input.name,
      artifactHash: input.artifactHash,
      targetFactsHash: "facts-hash",
      scopeHash: input.scopeHash,
      virtualValidationState: "not_tested",
      releaseState: "draft",
      backupVerified: false,
      maintenanceWindowValid: false,
      sectorProfileSnapshot: JSON.stringify({ profileId: "enterprise", completenessPercent: 100 }),
      sectorInputsHash: "a".repeat(64),
      sectorReviewState: "current",
      sectorReviewedAt: new Date("2026-08-16T00:00:00.000Z"),
    };
    createChangePlanMock.mockResolvedValueOnce([persisted]);

    const caller = appRouter.createCaller(createContext());
    const result = await caller.projects.changePlans.create(input);

    expect(result[0]).toMatchObject({ sectorReviewState: "current", sectorInputsHash: "a".repeat(64) });
    expect(JSON.parse(result[0]?.sectorProfileSnapshot || "{}")).toMatchObject({ completenessPercent: 100 });
  });
});
