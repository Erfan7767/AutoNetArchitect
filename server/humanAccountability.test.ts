import { describe, expect, it } from "vitest";
import { getHumanAccountability } from "../shared/humanAccountability";

describe("human accountability presentation policy", () => {
  it("keeps review, approval, execution, and emergency exception responsibilities distinct", () => {
    const matrix = getHumanAccountability("requested");

    expect(matrix.map(item => item.role)).toEqual(["reviewer", "approver", "executor", "emergency_authorizer"]);
    expect(matrix.find(item => item.role === "reviewer")?.state).toBe("required");
    expect(matrix.find(item => item.role === "approver")?.state).toBe("required");
    expect(matrix.find(item => item.role === "executor")?.state).toBe("external_only");
    expect(matrix.find(item => item.role === "emergency_authorizer")?.state).toBe("external_policy_only");
  });

  it("does not convert an approved project state into automatic execution authority", () => {
    const matrix = getHumanAccountability("approved");

    expect(matrix.find(item => item.role === "approver")?.state).toBe("recorded");
    expect(matrix.find(item => item.role === "executor")?.detail).toContain("cannot upload configuration or execute a production change");
    expect(matrix.find(item => item.role === "emergency_authorizer")?.detail).toContain("cannot waive evidence gates");
  });
});
