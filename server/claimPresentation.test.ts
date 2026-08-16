import { describe, expect, it } from "vitest";
import { ACTIVE_PROJECT_STORAGE_KEY, parseActiveProjectId } from "../shared/claimPresentation";

describe("active project report bridge", () => {
  it("uses one stable workspace key and accepts only positive integer project identifiers", () => {
    expect(ACTIVE_PROJECT_STORAGE_KEY).toBe("autonet.activeProjectId");
    expect(parseActiveProjectId("42")).toBe(42);
    expect(parseActiveProjectId(null)).toBe(0);
    expect(parseActiveProjectId("0")).toBe(0);
    expect(parseActiveProjectId("1.5")).toBe(0);
    expect(parseActiveProjectId("not-a-project")).toBe(0);
  });
});
