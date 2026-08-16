export const RESTRICTED_CLAIM_PRESENTATION = [
  { id: "engineer_equivalence", label: "Engineer equivalence", requirement: "Measured comparison scope, authority, and reviewed evidence are required." },
  { id: "production_safe", label: "Production-safe", requirement: "Scoped authoritative and measured evidence are required; no execution authority follows." },
  { id: "compatibility", label: "Compatibility", requirement: "Exact vendor, platform, version, license, configuration-path, and measured evidence are required." },
  { id: "compliance", label: "Compliance", requirement: "Scoped controls, authoritative mapping, measured evidence, and review are required." },
] as const;

export type RestrictedClaimPresentationId = typeof RESTRICTED_CLAIM_PRESENTATION[number]["id"];

/** Shared bridge for the active project selected by the authenticated workspace. */
export const ACTIVE_PROJECT_STORAGE_KEY = "autonet.activeProjectId";

export function parseActiveProjectId(value: string | null): number {
  const candidate = Number(value);
  return Number.isInteger(candidate) && candidate > 0 ? candidate : 0;
}
