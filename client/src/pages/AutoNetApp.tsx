import { useAuth } from "@/_core/hooks/useAuth";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { trpc } from "@/lib/trpc";
import { filterVendorSupport } from "../../../shared/vendorSupport";
import { cn } from "@/lib/utils";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  BadgeCheck,
  BarChart3,
  Boxes,
  Check,
  ChevronRight,
  ClipboardCheck,
  CloudCog,
  FileCheck2,
  FileKey2,
  FileText,
  Gauge,
  LayoutDashboard,
  Menu,
  Network,
  PackageCheck,
  PanelTopOpen,
  Plus,
  Radar,
  ReceiptText,
  Route,
  Search,
  Settings2,
  ShieldCheck,
  ShieldAlert,
  SlidersHorizontal,
  Sparkles,
  Trash2,
  UsersRound,
  Waypoints,
  type LucideIcon,
} from "lucide-react";
import { type ReactNode, useEffect, useMemo, useState } from "react";
import { useLocation } from "wouter";
import { startLogin } from "../const";

type ProjectRecord = {
  id: number;
  name: string;
  organization: string;
  organizationType: string;
  siteCount: number;
  classification: "greenfield" | "brownfield" | "undetermined";
  vendorPreferences: string;
  complianceNeeds: string;
  status: "intake" | "design" | "ready_for_review" | "approved";
  questionnaireComplete: number;
  requirementsComplete: number;
  approvalState: "not_requested" | "pending" | "approved" | "blocked";
  approvedBy: string | null;
  approvedAt: Date | null;
  createdAt: Date;
  updatedAt: Date;
};

type NavItem = {
  label: string;
  path: string;
  icon: LucideIcon;
  group: "Workflow" | "Governance";
};

const navItems: NavItem[] = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard, group: "Workflow" },
  { label: "Questionnaire", path: "/questionnaire", icon: ClipboardCheck, group: "Workflow" },
  { label: "Requirements", path: "/requirements", icon: FileCheck2, group: "Workflow" },
  { label: "Discovery", path: "/discovery", icon: Radar, group: "Workflow" },
  { label: "Design", path: "/design", icon: Network, group: "Workflow" },
  { label: "Equipment", path: "/equipment", icon: PackageCheck, group: "Workflow" },
  { label: "Configs", path: "/configs", icon: FileKey2, group: "Workflow" },
  { label: "Deployment", path: "/deployment", icon: Route, group: "Workflow" },
  { label: "Operations", path: "/operations", icon: Activity, group: "Workflow" },
  { label: "Compliance", path: "/compliance", icon: ShieldCheck, group: "Governance" },
  { label: "Reports", path: "/reports", icon: ReceiptText, group: "Governance" },
  { label: "Admin", path: "/admin", icon: Settings2, group: "Governance" },
  { label: "Vendor Support", path: "/vendor-support", icon: Boxes, group: "Governance" },
  { label: "Audit", path: "/audit", icon: Search, group: "Governance" },
];

const statusStyle: Record<ProjectRecord["status"], string> = {
  intake: "bg-slate-100 text-slate-700 ring-slate-200",
  design: "bg-blue-50 text-blue-700 ring-blue-100",
  ready_for_review: "bg-amber-50 text-amber-700 ring-amber-100",
  approved: "bg-emerald-50 text-emerald-700 ring-emerald-100",
};

const statusLabel: Record<ProjectRecord["status"], string> = {
  intake: "Intake",
  design: "Design in progress",
  ready_for_review: "Review required",
  approved: "Approved",
};

type QuestionnaireValues = {
  organization: string;
  organizationType: string;
  siteCount: string;
  classification: "greenfield" | "brownfield" | "undetermined";
  vendorPreferences: string;
  complianceNeeds: string;
};

const emptyQuestionnaire: QuestionnaireValues = {
  organization: "",
  organizationType: "",
  siteCount: "",
  classification: "undetermined" as const,
  vendorPreferences: "",
  complianceNeeds: "",
};

function relativeTime(date: Date | string | null | undefined): string {
  if (!date) return "Not recorded";
  const timestamp = new Date(date).getTime();
  const minutes = Math.max(0, Math.round((Date.now() - timestamp) / 60000));
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  return `${Math.round(hours / 24)} days ago`;
}

function TitleBlock({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <div className="max-w-3xl">
      <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.2em] text-cyan-700">{eyebrow}</p>
      <h1 className="font-display text-3xl font-semibold tracking-[-0.04em] text-slate-950 md:text-4xl">{title}</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500 md:text-base">{description}</p>
    </div>
  );
}

function Pill({ children, tone = "slate" }: { children: ReactNode; tone?: "slate" | "blue" | "green" | "amber" | "red" }) {
  const tones = {
    slate: "bg-slate-100 text-slate-600 ring-slate-200",
    blue: "bg-blue-50 text-blue-700 ring-blue-100",
    green: "bg-emerald-50 text-emerald-700 ring-emerald-100",
    amber: "bg-amber-50 text-amber-700 ring-amber-100",
    red: "bg-rose-50 text-rose-700 ring-rose-100",
  };
  return <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1", tones[tone])}>{children}</span>;
}

function PercentRing({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="grid h-11 w-11 place-items-center rounded-full bg-slate-950 text-xs font-bold text-white shadow-sm">
        {value}%
      </div>
      <div>
        <p className="text-sm font-semibold text-slate-800">{label}</p>
        <p className="text-xs text-slate-500">Evidence-backed only</p>
      </div>
    </div>
  );
}

function EmptyProjectState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="panel-grid flex min-h-[460px] flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-white px-6 text-center shadow-sm">
      <div className="mb-5 grid h-16 w-16 place-items-center rounded-2xl bg-cyan-50 text-cyan-700 ring-1 ring-cyan-100">
        <Network className="h-8 w-8" />
      </div>
      <h2 className="font-display text-2xl font-semibold tracking-[-0.03em] text-slate-950">Start with the source of truth.</h2>
      <p className="mt-3 max-w-md text-sm leading-6 text-slate-500">Create a project to capture human-supplied requirements before design recommendations, configurations, or deployment decisions are considered.</p>
      <button className="mt-7 inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-slate-900/15 transition hover:-translate-y-0.5 hover:bg-slate-800" onClick={onCreate}>
        <Plus className="h-4 w-4" /> Create network project
      </button>
    </div>
  );
}

function ProjectPicker({ projects, selectedProjectId, onSelect, onCreate }: { projects: ProjectRecord[]; selectedProjectId: number | null; onSelect: (id: number) => void; onCreate: () => void }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <select
        aria-label="Active network project"
        value={selectedProjectId ?? ""}
        onChange={event => onSelect(Number(event.target.value))}
        className="h-10 min-w-[210px] rounded-xl border border-slate-200 bg-white px-3 text-sm font-medium text-slate-800 shadow-sm outline-none transition focus:border-cyan-500 focus:ring-4 focus:ring-cyan-500/10"
      >
        {projects.map(project => <option key={project.id} value={project.id}>{project.name}</option>)}
      </select>
      <button className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-slate-300 hover:bg-slate-50" onClick={onCreate}>
        <Plus className="h-4 w-4" /> New
      </button>
    </div>
  );
}

function ProjectModal({ onClose, onCreate, isSaving }: { onClose: () => void; onCreate: (name: string, organization: string) => void; isSaving: boolean }) {
  const [name, setName] = useState("");
  const [organization, setOrganization] = useState("");
  const [error, setError] = useState("");
  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (name.trim().length < 2) {
      setError("Use a project name with at least two characters.");
      return;
    }
    onCreate(name, organization);
  };
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/30 p-4 backdrop-blur-sm">
      <form onSubmit={submit} className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl shadow-slate-950/20">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-cyan-700">Project intake</p>
            <h2 className="mt-2 font-display text-2xl font-semibold text-slate-950">Create a network project</h2>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg px-2 py-1 text-sm text-slate-500 hover:bg-slate-100">Close</button>
        </div>
        <div className="mt-6 space-y-4">
          <label className="block text-sm font-semibold text-slate-700">Project name
            <input value={name} onChange={event => setName(event.target.value)} placeholder="e.g. Riyadh campus refresh" className="mt-2 h-11 w-full rounded-xl border border-slate-200 px-3 text-sm outline-none transition focus:border-cyan-500 focus:ring-4 focus:ring-cyan-500/10" autoFocus />
          </label>
          <label className="block text-sm font-semibold text-slate-700">Organization
            <input value={organization} onChange={event => setOrganization(event.target.value)} placeholder="Human-supplied organization name" className="mt-2 h-11 w-full rounded-xl border border-slate-200 px-3 text-sm outline-none transition focus:border-cyan-500 focus:ring-4 focus:ring-cyan-500/10" />
          </label>
          {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-xs font-medium text-rose-700">{error}</p>}
        </div>
        <div className="mt-7 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-100">Cancel</button>
          <button disabled={isSaving} type="submit" className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-slate-900/15 transition hover:bg-slate-800 disabled:opacity-50">{isSaving ? "Creating…" : "Create project"}</button>
        </div>
      </form>
    </div>
  );
}

function DashboardPage({ project, projects, onNavigate, onSelect, onCreate, onDelete }: { project: ProjectRecord; projects: ProjectRecord[]; onNavigate: (path: string) => void; onSelect: (id: number) => void; onCreate: () => void; onDelete: () => void }) {
  const lifecycle = [
    ["Questionnaire", project.questionnaireComplete, "/questionnaire"],
    ["Requirements", project.requirementsComplete, "/requirements"],
    ["Design", project.status === "intake" ? 0 : 60, "/design"],
    ["Deployment", project.approvalState === "approved" ? 100 : 30, "/deployment"],
  ] as const;
  return (
    <div className="space-y-7">
      <section className="grid gap-5 xl:grid-cols-[1.3fr_.7fr]">
        <div className="relative overflow-hidden rounded-3xl bg-slate-950 px-6 py-7 text-white shadow-xl shadow-slate-950/10 sm:px-8">
          <div className="absolute inset-0 opacity-90" style={{ background: "radial-gradient(circle at 85% 10%, rgba(14, 211, 207, .27), transparent 29%), radial-gradient(circle at 58% 110%, rgba(70, 101, 255, .28), transparent 32%)" }} />
          <div className="relative">
            <div className="flex flex-wrap items-center gap-3"><Pill tone="green"><BadgeCheck className="h-3.5 w-3.5" /> Controlled workspace</Pill><span className="text-xs text-slate-400">Updated {relativeTime(project.updatedAt)}</span></div>
            <h1 className="mt-6 max-w-xl font-display text-3xl font-semibold tracking-[-0.045em] sm:text-4xl">{project.name}</h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">A governed workspace for requirements, design evidence, configuration review, and approval-bound deployment preparation.</p>
            <div className="mt-7 flex flex-wrap gap-3">
              <button onClick={() => onNavigate("/questionnaire")} className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-slate-100">Continue intake <ChevronRight className="h-4 w-4" /></button>
              <button onClick={() => onNavigate("/deployment")} className="inline-flex items-center gap-2 rounded-xl border border-white/20 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/10">Review deployment gate <ArrowUpRight className="h-4 w-4" /></button>
            </div>
          </div>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Project posture</p><p className="mt-2 text-sm text-slate-500">Current operational control state.</p></div><Pill tone={project.approvalState === "approved" ? "green" : project.approvalState === "pending" ? "amber" : "slate"}>{project.approvalState.replaceAll("_", " ")}</Pill></div>
          <div className="mt-7 space-y-5">
            <PercentRing value={project.requirementsComplete} label="Requirements completeness" />
            <div className="h-px bg-slate-100" />
            <div className="flex items-center gap-3"><div className="grid h-11 w-11 place-items-center rounded-full bg-blue-50 text-blue-700"><ShieldCheck className="h-5 w-5" /></div><div><p className="text-sm font-semibold text-slate-800">Human approval boundary</p><p className="text-xs text-slate-500">No deployment execution is available here.</p></div></div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.18fr_.82fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center justify-between"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Lifecycle coverage</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Project progression</h2></div><BarChart3 className="h-5 w-5 text-slate-300" /></div><div className="mt-7 grid gap-4 sm:grid-cols-2">{lifecycle.map(([label, value, path], index) => <button key={label} onClick={() => onNavigate(path)} className="group rounded-2xl border border-slate-100 bg-slate-50/65 p-4 text-left transition hover:-translate-y-0.5 hover:border-cyan-200 hover:bg-cyan-50/40"><div className="flex items-center justify-between"><span className="text-sm font-semibold text-slate-800">0{index + 1} · {label}</span><span className="text-sm font-bold text-slate-950">{value}%</span></div><div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-600" style={{ width: `${value}%` }} /></div></button>)}</div></div>
        <div className="network-sketch rounded-3xl border border-slate-200 p-6 shadow-sm"><div className="flex items-center justify-between"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-500">Design signal</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Topology evidence</h2></div><Radar className="h-5 w-5 text-cyan-700" /></div><div className="relative mt-7 h-[176px] overflow-hidden rounded-2xl border border-slate-200 bg-white/70"><div className="absolute left-[12%] top-[45%] h-11 w-20 rounded-xl border border-slate-300 bg-white shadow-sm" /><div className="absolute left-[42%] top-[25%] h-14 w-24 rounded-2xl border border-cyan-200 bg-cyan-50 shadow-sm" /><div className="absolute right-[10%] top-[45%] h-11 w-20 rounded-xl border border-slate-300 bg-white shadow-sm" /><div className="absolute left-[33%] top-[51%] h-px w-[16%] bg-cyan-500" /><div className="absolute left-[58%] top-[51%] h-px w-[22%] bg-cyan-500" /><div className="absolute left-[49%] top-[62%] h-10 w-px bg-dashed-line" /><div className="absolute bottom-[10%] left-[42%] h-10 w-24 rounded-xl border border-slate-300 bg-white shadow-sm" /></div><p className="mt-4 text-xs leading-5 text-slate-500">Topology remains a controlled design artifact. No physical attributes are inferred without human-supplied evidence.</p></div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Project library</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Your network projects</h2></div><button onClick={onCreate} className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-3.5 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"><Plus className="h-4 w-4" /> New project</button></div><div className="mt-5 overflow-x-auto"><table className="w-full min-w-[640px] text-left"><thead><tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-400"><th className="pb-3">Project</th><th className="pb-3">Classification</th><th className="pb-3">Readiness</th><th className="pb-3">Status</th><th className="pb-3 text-right">Action</th></tr></thead><tbody>{projects.map(item => <tr key={item.id} className="border-b border-slate-50 last:border-0"><td className="py-4"><p className="text-sm font-semibold text-slate-800">{item.name}</p><p className="mt-0.5 text-xs text-slate-500">{item.organization || "Organization not specified"}</p></td><td className="py-4 text-sm capitalize text-slate-600">{item.classification}</td><td className="py-4"><span className="text-sm font-semibold text-slate-700">{item.requirementsComplete}%</span></td><td className="py-4"><span className={cn("inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1", statusStyle[item.status])}>{statusLabel[item.status]}</span></td><td className="py-4 text-right">{item.id === project.id ? <button onClick={onDelete} className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold text-rose-600 transition hover:bg-rose-50"><Trash2 className="h-3.5 w-3.5" /> Delete</button> : <button onClick={() => onSelect(item.id)} className="text-xs font-semibold text-cyan-700">Open</button>}</td></tr>)}</tbody></table></div></section>
    </div>
  );
}

function QuestionnairePage({ project, onSave, isSaving }: { project: ProjectRecord; onSave: (values: QuestionnaireValues) => void; isSaving: boolean }) {
  const [values, setValues] = useState(emptyQuestionnaire);
  useEffect(() => setValues({ organization: project.organization || "", organizationType: project.organizationType || "", siteCount: project.siteCount ? String(project.siteCount) : "", classification: project.classification, vendorPreferences: project.vendorPreferences || "", complianceNeeds: project.complianceNeeds || "" }), [project]);
  const update = (key: Exclude<keyof QuestionnaireValues, "classification">, value: string) => setValues(current => ({ ...current, [key]: value }));
  const updateClassification = (classification: QuestionnaireValues["classification"]) => setValues(current => ({ ...current, classification }));
  const submit = (event: React.FormEvent<HTMLFormElement>) => { event.preventDefault(); onSave(values); };
  return <div className="space-y-7"><TitleBlock eyebrow="01 · Discovery" title="Questionnaire" description="Capture only confirmed, human-supplied inputs. The workspace calculates completeness without inventing topology, addressing, facility, or licensing facts." /><form onSubmit={submit} className="grid gap-5 lg:grid-cols-[1.15fr_.85fr]"><div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="grid gap-5 sm:grid-cols-2"><Field label="Organization" value={values.organization} onChange={value => update("organization", value)} placeholder="Human-supplied organization name" /><Field label="Organization type" value={values.organizationType} onChange={value => update("organizationType", value)} placeholder="e.g. Enterprise, university" /><Field label="Site count" value={values.siteCount} onChange={value => update("siteCount", value.replace(/\D/g, ""))} placeholder="Confirmed site count" /><label className="text-sm font-semibold text-slate-700">Network classification<select value={values.classification} onChange={event => updateClassification(event.target.value as QuestionnaireValues["classification"])} className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-normal outline-none focus:border-cyan-500 focus:ring-4 focus:ring-cyan-500/10"><option value="undetermined">Undetermined</option><option value="greenfield">Greenfield</option><option value="brownfield">Brownfield</option></select></label><Field label="Vendor preferences" value={values.vendorPreferences} onChange={value => update("vendorPreferences", value)} placeholder="Confirmed preference or selection constraint" full /><Field label="Compliance needs" value={values.complianceNeeds} onChange={value => update("complianceNeeds", value)} placeholder="Scope-specific technical assessment needs" full /></div><div className="mt-7 flex justify-end"><button disabled={isSaving} type="submit" className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-slate-900/15 transition hover:bg-slate-800 disabled:opacity-50">{isSaving ? "Saving…" : "Save questionnaire"}</button></div></div><aside className="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-xl shadow-slate-950/10"><Pill tone="green"><BadgeCheck className="h-3.5 w-3.5" /> Evidence-aware intake</Pill><h2 className="mt-5 font-display text-2xl font-semibold tracking-[-0.03em]">Completeness, not confidence theatre.</h2><p className="mt-3 text-sm leading-6 text-slate-300">Fields remain visibly incomplete when no answer has been supplied. Completion does not certify the design or deployment path.</p><div className="mt-7 rounded-2xl border border-white/10 bg-white/5 p-4"><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Current completeness</p><p className="mt-2 text-4xl font-semibold">{project.questionnaireComplete}%</p><div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-cyan-400" style={{ width: `${project.questionnaireComplete}%` }} /></div></div></aside></form></div>;
}

function Field({ label, value, onChange, placeholder, full = false }: { label: string; value: string; onChange: (value: string) => void; placeholder: string; full?: boolean }) {
  return <label className={cn("text-sm font-semibold text-slate-700", full && "sm:col-span-2")}>{label}<input value={value} onChange={event => onChange(event.target.value)} placeholder={placeholder} className="mt-2 h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none transition focus:border-cyan-500 focus:ring-4 focus:ring-cyan-500/10" /></label>;
}

function RequirementsPage({ project, onNavigate }: { project: ProjectRecord; onNavigate: (path: string) => void }) {
  const sectorReviewQuery = trpc.projects.sectorReview.useQuery({ projectId: project.id });
  const fields = [["Organization profile", Boolean(project.organization && project.organizationType)], ["Site scope", project.siteCount > 0], ["Project classification", project.classification !== "undetermined"], ["Vendor preferences", Boolean(project.vendorPreferences)], ["Compliance needs", Boolean(project.complianceNeeds)]];
  return <div className="space-y-7"><TitleBlock eyebrow="02 · Requirements" title="Review structured requirements" description="The requirements register reflects questionnaire evidence only. Any field without source input is retained as unresolved rather than silently defaulted." /><div className="grid gap-5 lg:grid-cols-[1.1fr_.9fr]"><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center justify-between"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Completeness register</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Evidence by requirement area</h2></div><PercentRing value={project.requirementsComplete} label="Structured" /></div><div className="mt-6 divide-y divide-slate-100">{fields.map(([label, complete]) => <div key={label as string} className="flex items-center justify-between py-4"><span className="text-sm font-medium text-slate-700">{label}</span>{complete ? <Pill tone="green"><Check className="h-3.5 w-3.5" /> Addressed</Pill> : <Pill tone="amber"><AlertTriangle className="h-3.5 w-3.5" /> Needs input</Pill>}</div>)}</div></section><aside className="rounded-3xl border border-amber-200 bg-amber-50 p-6 shadow-sm"><div className="grid h-11 w-11 place-items-center rounded-xl bg-white text-amber-700 shadow-sm"><ShieldAlert className="h-5 w-5" /></div><h2 className="mt-5 font-display text-2xl font-semibold tracking-[-0.03em] text-slate-950">Unresolved items block certainty.</h2><p className="mt-3 text-sm leading-6 text-slate-600">Design recommendations must retain human-review boundaries whenever requirements are incomplete or unsupported.</p><button onClick={() => onNavigate("/questionnaire")} className="mt-7 inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800">Complete questionnaire <ChevronRight className="h-4 w-4" /></button></aside><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Sector evidence</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Human review currentness</h2></div>{sectorReviewQuery.data ? <Pill tone={sectorReviewQuery.data.reviewCurrent && sectorReviewQuery.data.completenessPercent === 100 ? "green" : "amber"}>{sectorReviewQuery.data.reviewCurrent ? "Current review" : "Review required"}</Pill> : null}</div>{sectorReviewQuery.isLoading ? <p className="mt-4 text-sm text-slate-500">Loading sector evidence status…</p> : sectorReviewQuery.data ? <div className="mt-5 grid gap-4 md:grid-cols-[0.7fr_1.3fr]"><div className="rounded-2xl bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Profile</p><p className="mt-2 text-sm font-semibold capitalize text-slate-800">{sectorReviewQuery.data.profileId.replaceAll("_", " ")}</p><p className="mt-3 text-2xl font-bold text-slate-950">{sectorReviewQuery.data.completenessPercent}%</p><p className="text-xs text-slate-500">Human-supplied evidence completeness</p></div><div><p className="text-sm font-semibold text-slate-700">Missing or unresolved inputs</p>{sectorReviewQuery.data.missingInputs.length ? <ul className="mt-2 space-y-2 text-sm text-slate-600">{sectorReviewQuery.data.missingInputs.map(item => <li key={item} className="rounded-xl bg-amber-50 px-3 py-2 ring-1 ring-amber-100">{item}</li>)}</ul> : <p className="mt-2 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800 ring-1 ring-emerald-100">All required sector inputs are recorded. Review age remains policy-controlled.</p>}</div></div> : null}</section></div></div>;
}

function DesignPage({ project }: { project: ProjectRecord }) {
  const utils = trpc.useUtils();
  const detailsQuery = trpc.projects.design.get.useQuery({ projectId: project.id });
  const saveMutation = trpc.projects.design.save.useMutation({ onSuccess: () => utils.projects.design.get.invalidate({ projectId: project.id }) });
  const [draft, setDraft] = useState({ topologySummary: "", vlanPlan: "", ipAddressingSummary: "", decisionRecords: "" });
  useEffect(() => {
    const details = detailsQuery.data;
    if (details) setDraft({ topologySummary: details.topologySummary, vlanPlan: details.vlanPlan, ipAddressingSummary: details.ipAddressingSummary, decisionRecords: details.decisionRecords });
  }, [detailsQuery.data]);
  const ready = project.requirementsComplete === 100;
  const submit = (event: React.FormEvent<HTMLFormElement>) => { event.preventDefault(); saveMutation.mutate({ projectId: project.id, ...draft }); };
  return <div className="space-y-7"><TitleBlock eyebrow="03 · Architecture" title="Design overview" description="Record supervised topology, segmentation, and addressing decisions. No VLAN IDs, IP ranges, floor dimensions, or public network attributes are invented by this hosted workspace." /><form onSubmit={submit} className="grid gap-5 xl:grid-cols-[1.15fr_.85fr]"><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Decision records</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Topology & addressing review</h2></div><Pill tone={ready ? "blue" : "amber"}>{ready ? "Ready for engineering review" : "Requirements incomplete"}</Pill></div><div className="mt-6 grid gap-4"><TextArea label="Topology decision" value={draft.topologySummary} onChange={value => setDraft(current => ({ ...current, topologySummary: value }))} placeholder="Human-reviewed topology decision, assumptions, and evidence basis" /><TextArea label="VLAN plan" value={draft.vlanPlan} onChange={value => setDraft(current => ({ ...current, vlanPlan: value }))} placeholder="Human-approved segmentation plan; do not infer identifiers or scope" /><TextArea label="IP addressing summary" value={draft.ipAddressingSummary} onChange={value => setDraft(current => ({ ...current, ipAddressingSummary: value }))} placeholder="Allocation source and human-approved addressing summary" /><TextArea label="Decision records" value={draft.decisionRecords} onChange={value => setDraft(current => ({ ...current, decisionRecords: value }))} placeholder="Rationale, confidence, evidence, reviewer, and affected artifacts" /></div><div className="mt-6 flex justify-end"><button disabled={saveMutation.isPending} type="submit" className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-slate-900/15 disabled:opacity-50">{saveMutation.isPending ? "Saving…" : "Save design details"}</button></div></section><aside className="rounded-3xl border border-slate-200 bg-cyan-50/60 p-6 shadow-sm"><p className="text-xs font-bold uppercase tracking-[0.15em] text-cyan-700">Design posture</p><h2 className="mt-2 font-display text-2xl font-semibold tracking-[-0.03em] text-slate-950">Explicit decisions, preserved rationale.</h2><p className="mt-3 text-sm leading-6 text-slate-600">Each field is a project record, not an automated recommendation. Save only confirmed human engineering data.</p><div className="mt-7 space-y-3">{[[Waypoints, "Topology"], [Boxes, "Segmentation"], [Network, "Addressing"]].map(([Icon, label]) => <div key={label as string} className="flex items-center gap-3 rounded-2xl bg-white/80 p-3 ring-1 ring-cyan-100"><Icon className="h-4 w-4 text-cyan-700" /><span className="text-sm font-semibold text-slate-700">{draft[(label === "Topology" ? "topologySummary" : label === "Segmentation" ? "vlanPlan" : "ipAddressingSummary")] ? `${label} recorded` : `${label} unresolved`}</span></div>)}</div></aside></form></div>;
}

function DecisionRow({ icon: Icon, title, detail }: { icon: LucideIcon; title: string; detail: string }) {
  return <div className="flex gap-4 rounded-2xl border border-slate-100 bg-slate-50/70 p-4"><div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white text-blue-700 shadow-sm"><Icon className="h-5 w-5" /></div><div><p className="text-sm font-semibold text-slate-800">{title}</p><p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p></div></div>;
}

function TextArea({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (value: string) => void; placeholder: string }) {
  return <label className="block text-sm font-semibold text-slate-700">{label}<textarea value={value} onChange={event => onChange(event.target.value)} placeholder={placeholder} rows={3} className="mt-2 w-full resize-y rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-normal leading-6 outline-none transition focus:border-cyan-500 focus:ring-4 focus:ring-cyan-500/10" /></label>;
}

function EquipmentPage({ project }: { project: ProjectRecord }) {
  const utils = trpc.useUtils();
  const itemsQuery = trpc.projects.bom.list.useQuery({ projectId: project.id });
  const addMutation = trpc.projects.bom.add.useMutation({ onSuccess: () => utils.projects.bom.list.invalidate({ projectId: project.id }) });
  const [draft, setDraft] = useState({ category: "device" as const, description: "", quantity: "1", costEstimate: "" });
  const submit = (event: React.FormEvent<HTMLFormElement>) => { event.preventDefault(); addMutation.mutate({ projectId: project.id, category: draft.category, description: draft.description, quantity: Number(draft.quantity), costEstimate: draft.costEstimate }, { onSuccess: () => setDraft({ category: "device", description: "", quantity: "1", costEstimate: "" }) }); };
  const items = itemsQuery.data || [];
  return <div className="space-y-7"><TitleBlock eyebrow="04 · Selection" title="Equipment & bill of materials" description="Record human-reviewed devices, optics, licensing, support, labor, and cost estimates. No unsupported platform is automatically selected." /><div className="grid gap-5 lg:grid-cols-[1.1fr_.9fr]"><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center justify-between"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">BOM workspace</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Selection evidence</h2></div><Pill tone={items.length ? "blue" : "amber"}>{items.length ? `${items.length} recorded` : "No BOM issued"}</Pill></div><div className="mt-6 overflow-x-auto rounded-2xl border border-slate-100"><table className="w-full min-w-[560px] text-left text-sm"><thead className="bg-slate-50 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-400"><tr><th className="px-4 py-3">Category</th><th className="px-4 py-3">Description</th><th className="px-4 py-3 text-right">Qty</th><th className="px-4 py-3 text-right">Estimate</th></tr></thead><tbody>{items.length ? items.map(item => <tr key={item.id} className="border-t border-slate-100"><td className="px-4 py-3.5 capitalize text-slate-600">{item.category}</td><td className="px-4 py-3.5 font-medium text-slate-700">{item.description}</td><td className="px-4 py-3.5 text-right text-slate-600">{item.quantity}</td><td className="px-4 py-3.5 text-right text-slate-500">{item.costEstimate || "Not supplied"}</td></tr>) : <tr><td colSpan={4} className="px-4 py-8 text-center text-sm text-slate-500">No human-reviewed BOM items have been recorded.</td></tr>}</tbody></table></div></section><aside className="rounded-3xl bg-slate-950 p-6 text-white shadow-xl shadow-slate-950/10"><PackageCheck className="h-6 w-6 text-cyan-300" /><h2 className="mt-5 font-display text-2xl font-semibold tracking-[-0.03em]">Record a reviewed BOM item.</h2><p className="mt-3 text-sm leading-6 text-slate-300">Vendor preference: {project.vendorPreferences || "not supplied"}.</p><form onSubmit={submit} className="mt-5 space-y-3"><select value={draft.category} onChange={event => setDraft(current => ({ ...current, category: event.target.value as typeof draft.category }))} className="h-10 w-full rounded-xl border border-white/15 bg-white/10 px-3 text-sm text-white outline-none"><option className="text-slate-900" value="device">Device</option><option className="text-slate-900" value="optic">Optic</option><option className="text-slate-900" value="license">License</option><option className="text-slate-900" value="support">Support</option><option className="text-slate-900" value="labor">Labor</option><option className="text-slate-900" value="rack">Rack</option><option className="text-slate-900" value="cable">Cable</option><option className="text-slate-900" value="spare">Spare</option></select><input required value={draft.description} onChange={event => setDraft(current => ({ ...current, description: event.target.value }))} placeholder="Human-reviewed item description" className="h-10 w-full rounded-xl border border-white/15 bg-white/10 px-3 text-sm text-white placeholder:text-slate-500 outline-none" /><div className="grid grid-cols-2 gap-3"><input required min="1" type="number" value={draft.quantity} onChange={event => setDraft(current => ({ ...current, quantity: event.target.value }))} placeholder="Qty" className="h-10 rounded-xl border border-white/15 bg-white/10 px-3 text-sm text-white placeholder:text-slate-500 outline-none" /><input value={draft.costEstimate} onChange={event => setDraft(current => ({ ...current, costEstimate: event.target.value }))} placeholder="Cost estimate" className="h-10 rounded-xl border border-white/15 bg-white/10 px-3 text-sm text-white placeholder:text-slate-500 outline-none" /></div><button disabled={addMutation.isPending} className="w-full rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-950 disabled:opacity-50">{addMutation.isPending ? "Adding…" : "Add BOM item"}</button></form></aside></div></div>;
}

function ConfigsPage({ project }: { project: ProjectRecord }) {
  const utils = trpc.useUtils();
  const artifactsQuery = trpc.projects.configs.list.useQuery({ projectId: project.id });
  const devicesQuery = trpc.projects.devices.list.useQuery({ projectId: project.id });
  const addMutation = trpc.projects.configs.add.useMutation({ onSuccess: () => utils.projects.configs.list.invalidate({ projectId: project.id }) });
  const [draft, setDraft] = useState({ deviceId: 0, vendor: "", deviceName: "", artifactSummary: "", artifactPreview: "", featureGuard: "unknown" as const, unsupportedFeatureLog: "" });
  const submit = (event: React.FormEvent<HTMLFormElement>) => { event.preventDefault(); if (!draft.deviceId) return; addMutation.mutate({ projectId: project.id, ...draft }, { onSuccess: () => setDraft({ deviceId: 0, vendor: "", deviceName: "", artifactSummary: "", artifactPreview: "", featureGuard: "unknown", unsupportedFeatureLog: "" }) }); };
  const artifacts = artifactsQuery.data || [];
  const unsupported = artifacts.filter(artifact => artifact.featureGuard === "blocked" || artifact.unsupportedFeatureLog);
  return <div className="space-y-7"><TitleBlock eyebrow="05 · Configuration" title="Config generation controls" description="Record reviewed generator artifacts per vendor and device. Feature-guard outcomes and unsupported-feature logs remain visible; secrets are never retained in this view." /><div className="grid gap-5 xl:grid-cols-[1.15fr_.85fr]"><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center justify-between"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Generated configuration artifacts</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Vendor review register</h2></div><SlidersHorizontal className="h-5 w-5 text-slate-300" /></div><div className="mt-6 space-y-3">{artifacts.length ? artifacts.map(artifact => <div key={artifact.id} className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-sm font-semibold text-slate-800">{artifact.vendor} · {artifact.deviceName}</p><p className="mt-1 text-xs text-slate-500">{artifact.artifactSummary || "No artifact summary supplied."}</p></div><Pill tone={artifact.featureGuard === "pass" ? "green" : artifact.featureGuard === "blocked" ? "red" : "amber"}>{artifact.featureGuard === "pass" ? <Check className="h-3.5 w-3.5" /> : <AlertTriangle className="h-3.5 w-3.5" />}{artifact.featureGuard}</Pill></div>{artifact.artifactPreview && <pre className="mt-4 overflow-x-auto rounded-xl bg-slate-950 p-3 font-mono text-xs leading-5 text-cyan-100">{artifact.artifactPreview}</pre>}</div>) : <div className="rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">No reviewed configuration artifacts are recorded for this project.</div>}</div></section><aside className="space-y-5"><section className="rounded-3xl border border-rose-200 bg-rose-50 p-6 shadow-sm"><p className="text-xs font-bold uppercase tracking-[0.15em] text-rose-500">Unsupported-feature log</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Clearly surfaced</h2><div className="mt-4 space-y-2">{unsupported.length ? unsupported.map(artifact => <div key={artifact.id} className="rounded-xl bg-white p-3 text-xs leading-5 text-slate-600 ring-1 ring-rose-100"><strong className="text-slate-800">{artifact.vendor} · {artifact.deviceName}</strong><br />{artifact.unsupportedFeatureLog || "Feature guard blocked the artifact; no unsupported command was generated."}</div>) : <p className="text-sm leading-6 text-slate-600">No unsupported features have been logged. Entries will appear here when a guard blocks a reviewed artifact.</p>}</div></section><form onSubmit={submit} className="rounded-3xl bg-slate-950 p-6 text-white shadow-xl shadow-slate-950/10"><p className="text-xs font-bold uppercase tracking-[0.15em] text-cyan-200">Record reviewed artifact</p><div className="mt-4 space-y-3"><input required value={draft.vendor} onChange={event => setDraft(current => ({ ...current, vendor: event.target.value }))} placeholder="Vendor" className="h-10 w-full rounded-xl border border-white/15 bg-white/10 px-3 text-sm placeholder:text-slate-500 outline-none" /><input required value={draft.deviceName} onChange={event => setDraft(current => ({ ...current, deviceName: event.target.value }))} placeholder="Device name" className="h-10 w-full rounded-xl border border-white/15 bg-white/10 px-3 text-sm placeholder:text-slate-500 outline-none" /><select value={draft.featureGuard} onChange={event => setDraft(current => ({ ...current, featureGuard: event.target.value as typeof draft.featureGuard }))} className="h-10 w-full rounded-xl border border-white/15 bg-white/10 px-3 text-sm outline-none"><option className="text-slate-900" value="unknown">Guard status: unknown</option><option className="text-slate-900" value="pass">Guard status: pass</option><option className="text-slate-900" value="blocked">Guard status: blocked</option></select><textarea value={draft.artifactSummary} onChange={event => setDraft(current => ({ ...current, artifactSummary: event.target.value }))} placeholder="Artifact summary; references only, no secret values" rows={2} className="w-full rounded-xl border border-white/15 bg-white/10 px-3 py-2.5 text-sm placeholder:text-slate-500 outline-none" /><textarea value={draft.artifactPreview} onChange={event => setDraft(current => ({ ...current, artifactPreview: event.target.value }))} placeholder="Redacted configuration preview; never enter passwords, keys, tokens, or raw secrets" rows={5} className="w-full rounded-xl border border-white/15 bg-white/10 px-3 py-2.5 font-mono text-xs placeholder:text-slate-500 outline-none" /><textarea value={draft.unsupportedFeatureLog} onChange={event => setDraft(current => ({ ...current, unsupportedFeatureLog: event.target.value }))} placeholder="Unsupported feature or evidence gap, if any" rows={2} className="w-full rounded-xl border border-white/15 bg-white/10 px-3 py-2.5 text-sm placeholder:text-slate-500 outline-none" /><button disabled={addMutation.isPending} className="w-full rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-950 disabled:opacity-50">{addMutation.isPending ? "Recording…" : "Record artifact"}</button></div></form></aside></div></div>;
}

function DeploymentPage({ project, isAdmin, onRequest, onApprove, requestPending, approvePending }: { project: ProjectRecord; isAdmin: boolean; onRequest: () => void; onApprove: () => void; requestPending: boolean; approvePending: boolean }) {
  const complete = project.requirementsComplete === 100;
  const approved = project.approvalState === "approved";
  const gate = approved ? { label: "GO — approved", tone: "green" as const, detail: `Approval recorded${project.approvedBy ? ` by ${project.approvedBy}` : ""}.` } : project.approvalState === "pending" ? { label: "PENDING — review required", tone: "amber" as const, detail: "The request awaits an authorized human approver." } : { label: "NO-GO — approval required", tone: "red" as const, detail: complete ? "Human deployment approval has not been granted." : "Requirements are incomplete, so the gate remains closed." };
  const readinessCards: Array<{ label: string; value: string; icon: LucideIcon }> = [
    { label: "Dry-run plan", value: "Not run", icon: Gauge },
    { label: "Backup verification", value: "Not recorded", icon: FileCheck2 },
    { label: "Rollback readiness", value: "Review required", icon: Route },
  ];
  return <div className="space-y-7"><TitleBlock eyebrow="06 · Deployment" title="Preparation & go/no-go" description="A distinct change-control boundary. This website supports dry-run preparation and approval visibility; it does not execute production changes." /><section className={cn("rounded-3xl border p-6 shadow-sm", gate.tone === "green" ? "border-emerald-200 bg-emerald-50" : gate.tone === "amber" ? "border-amber-200 bg-amber-50" : "border-rose-200 bg-rose-50")}><div className="flex flex-col justify-between gap-6 md:flex-row md:items-center"><div className="flex items-start gap-4"><div className={cn("grid h-14 w-14 place-items-center rounded-2xl bg-white shadow-sm", gate.tone === "green" ? "text-emerald-700" : gate.tone === "amber" ? "text-amber-700" : "text-rose-700")}>{gate.tone === "green" ? <BadgeCheck className="h-7 w-7" /> : <ShieldAlert className="h-7 w-7" />}</div><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-500">Pre-deployment control gate</p><h2 className="mt-1 font-display text-2xl font-semibold tracking-[-0.03em] text-slate-950">{gate.label}</h2><p className="mt-2 text-sm text-slate-600">{gate.detail}</p></div></div><div className="flex flex-wrap gap-2">{!complete ? <Pill tone="red">Requirements incomplete</Pill> : <Pill tone="green"><Check className="h-3.5 w-3.5" /> Requirements complete</Pill>}<Pill tone={approved ? "green" : "amber"}>Approval {project.approvalState.replaceAll("_", " ")}</Pill></div></div><div className="mt-6 flex flex-wrap gap-3 border-t border-slate-900/10 pt-5">{!approved && project.approvalState !== "pending" && <button disabled={!complete || requestPending} onClick={onRequest} className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40">{requestPending ? "Requesting…" : "Request approval"}</button>}{isAdmin && project.approvalState === "pending" && <button disabled={approvePending} onClick={onApprove} className="rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{approvePending ? "Approving…" : "Grant human approval"}</button>}<span className="self-center text-xs font-medium text-slate-500">Deployment execution remains unavailable in this hosted interface.</span></div></section><div className="grid gap-5 md:grid-cols-3">{readinessCards.map(card => { const Icon = card.icon; return <div key={card.label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><Icon className="h-5 w-5 text-blue-700" /><p className="mt-4 text-sm font-semibold text-slate-700">{card.label}</p><p className="mt-1 text-xs text-slate-500">{card.value}</p></div>; })}</div></div>;
}

type ChangePlanListItem = {
  id: number;
  name: string;
  virtualValidationState: string;
  releaseState: string;
};

function ChangePlanReadinessRow({ plan }: { plan: ChangePlanListItem }) {
  const readinessQuery = trpc.projects.changePlans.approvalReadiness.useQuery({ changePlanId: plan.id });
  const readiness = readinessQuery.data;
  const blocked = readiness?.decision.status === "blocked";
  return <div className="flex flex-col gap-3 p-4"><div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-sm font-semibold text-slate-800">{plan.name}</p><p className="mt-1 text-xs text-slate-500">Validation: {plan.virtualValidationState.replaceAll("_", " ")} · Release: {plan.releaseState.replaceAll("_", " ")}</p></div><Pill tone={blocked ? "red" : plan.virtualValidationState === "test_passed" ? "green" : "amber"}>{readinessQuery.isLoading ? "Checking gates" : blocked ? "Approval blocked" : "Review readiness"}</Pill></div>{blocked && <div className="rounded-xl border border-rose-100 bg-rose-50 px-3 py-2 text-xs leading-5 text-rose-800"><strong>Required before human approval:</strong><ul className="mt-1 list-disc space-y-0.5 pl-4">{readiness.decision.blockers.map(blocker => <li key={blocker}>{blocker}</li>)}</ul></div>}{!readinessQuery.isLoading && !readiness && <p className="text-xs text-slate-500">Readiness evidence is unavailable for this plan.</p>}</div>;
}

function OperationsPage() {
  const [projectId, setProjectId] = useState(() => Number(window.localStorage.getItem("autonet.activeProjectId") || 0));
  useEffect(() => {
    const synchronizeProject = () => setProjectId(Number(window.localStorage.getItem("autonet.activeProjectId") || 0));
    synchronizeProject();
    window.addEventListener("autonet-project-changed", synchronizeProject);
    return () => window.removeEventListener("autonet-project-changed", synchronizeProject);
  }, []);
  const sitesQuery = trpc.projects.sites.list.useQuery({ projectId }, { enabled: projectId > 0 });
  const devicesQuery = trpc.projects.devices.list.useQuery({ projectId }, { enabled: projectId > 0 });
  const plansQuery = trpc.projects.changePlans.list.useQuery({ projectId }, { enabled: projectId > 0 });
  const sites = sitesQuery.data || [];
  const devices = devicesQuery.data || [];
  const plans = plansQuery.data || [];
  const observedCount = devices.filter(item => item.device.factState === "observed").length;
  const passedTestCount = plans.filter(plan => plan.virtualValidationState === "test_passed").length;
  const signals: Array<{ title: string; detail: string; icon: LucideIcon; tone: "amber" | "green" | "slate" }> = [
    { title: "Authorized sites", detail: projectId ? `${sites.length} site record${sites.length === 1 ? "" : "s"}; no agent session is implied by registration.` : "Select a project before reviewing site controls.", icon: Network, tone: sites.length ? "green" : "amber" },
    { title: "Observed devices", detail: `${observedCount} device fact record${observedCount === 1 ? "" : "s"} received from an authorized agent.`, icon: Radar, tone: observedCount ? "green" : "slate" },
    { title: "Virtual validation", detail: `${passedTestCount} plan${passedTestCount === 1 ? "" : "s"} with a recorded matching test pass. A pass never bypasses human approval.`, icon: CloudCog, tone: passedTestCount ? "green" : "amber" },
  ];
  return <div className="space-y-7"><TitleBlock eyebrow="07 · Operations" title="Agent-controlled operational reality" description="This control plane shows evidence from authorized local agents. It never scans a network, exposes credentials, or pushes configuration from the browser." /><div className="grid gap-5 md:grid-cols-3">{signals.map(signal => { const Icon = signal.icon; return <section key={signal.title} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center justify-between"><div className="grid h-11 w-11 place-items-center rounded-xl bg-slate-50 text-slate-700"><Icon className="h-5 w-5" /></div><Pill tone={signal.tone}>Evidence state</Pill></div><h2 className="mt-6 font-display text-xl font-semibold text-slate-950">{signal.title}</h2><p className="mt-2 text-sm leading-6 text-slate-500">{signal.detail}</p></section>; })}</div><div className="grid gap-5 lg:grid-cols-2"><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Authorized site registry</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Local agent boundary</h2>{sites.length ? <div className="mt-5 space-y-3">{sites.map(site => <div key={site.id} className="rounded-2xl bg-slate-50 p-4"><div className="flex justify-between gap-3"><p className="font-semibold text-slate-800">{site.name}</p><Pill tone={site.enrollmentState === "active" ? "green" : "amber"}>{site.enrollmentState.replaceAll("_", " ")}</Pill></div><p className="mt-2 text-xs text-slate-500">Scope reference: {site.approvedScopeReference} · Mode: {site.mode.replaceAll("_", " ")}</p></div>)}</div> : <p className="mt-5 text-sm leading-6 text-slate-500">No site is registered. Register a site and approved scope through the API or the next onboarding workflow; this page cannot infer a network boundary.</p>}</section><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Managed-device inventory</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Evidence before automation</h2>{devices.length ? <div className="mt-5 space-y-3">{devices.map(item => <div key={item.device.id} className="rounded-2xl bg-slate-50 p-4"><div className="flex justify-between gap-3"><p className="font-semibold text-slate-800">{item.device.deviceReference}</p><Pill tone={item.device.factState === "observed" ? "green" : "amber"}>{item.device.factState}</Pill></div><p className="mt-2 text-xs text-slate-500">{item.siteName} · {item.device.protocol} · {item.device.observedVendor || "Vendor not observed"} {item.device.observedPlatform || ""}</p></div>)}</div> : <p className="mt-5 text-sm leading-6 text-slate-500">No device facts are available. The platform will abstain from generating a deployable configuration until an agent reports observed facts and capabilities.</p>}</section></div><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Change plans and virtual validation</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">No automatic upload from a virtual pass</h2>{plans.length ? <div className="mt-5 divide-y divide-slate-100 overflow-hidden rounded-2xl border border-slate-100">{plans.map(plan => <ChangePlanReadinessRow key={plan.id} plan={plan} />)}</div> : <p className="mt-5 text-sm leading-6 text-slate-500">No change plan exists. A plan requires observed and capability-verified target facts, a versioned artifact hash, a scope hash, and matching virtual-test evidence before human release can be requested.</p>}</section></div>;
}

function CompliancePage({ project }: { project: ProjectRecord }) { return <div className="space-y-7"><TitleBlock eyebrow="08 · Assurance" title="Compliance assessment" description="Technical assessment summaries are scoped to available design and operational evidence. This workspace does not issue certifications or claims of readiness without authoritative scope and evidence." /><div className="grid gap-5 lg:grid-cols-[1.15fr_.85fr]"><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Assessment basis</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">No compliance outcome yet</h2><div className="mt-6 grid gap-3">{["Scope definition", "Design and configuration evidence", "Operational evidence", "Authoritative control mapping"].map(item => <div key={item} className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3"><span className="text-sm font-medium text-slate-700">{item}</span><Pill tone="amber">Not supplied</Pill></div>)}</div></section><aside className="rounded-3xl border border-blue-100 bg-blue-50 p-6 shadow-sm"><ShieldCheck className="h-6 w-6 text-blue-700" /><h2 className="mt-5 font-display text-2xl font-semibold tracking-[-0.03em] text-slate-950">Scope first.</h2><p className="mt-3 text-sm leading-6 text-slate-600">{project.complianceNeeds ? `Declared needs: ${project.complianceNeeds}.` : "No compliance needs have been declared."} The system will keep this as a review boundary until scoped evidence is supplied.</p></aside></div></div>; }

function ReportsPage() { return <div className="space-y-7"><TitleBlock eyebrow="09 · Handover" title="Reports & deliverables" description="Generated records declare their source-of-truth basis and time of generation. Exports are designed to redact secret values and credentials." /><div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Report registry</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">No reports have been generated</h2><p className="mt-2 text-sm text-slate-500">Build reports after the relevant project evidence is present and reviewed.</p></div><ReceiptText className="h-9 w-9 text-slate-200" /></div></div></div>; }

function VendorSupportPage() {
  const supportQuery = trpc.vendorSupport.list.useQuery();
  const [selectedFamily, setSelectedFamily] = useState("all");
  return <div className="space-y-7"><TitleBlock eyebrow="10 · Vendor evidence" title="Vendor support review" description="Review the four-family support boundary before selecting a discovery path. This surface reports evidence requirements; it does not certify compatibility or authorize production change." /><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-col gap-4 border-b border-slate-100 pb-5 sm:flex-row sm:items-start sm:justify-between"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Review surface</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Evidence chain before configuration</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">A family match is only an initial discovery boundary. Exact platform, software version, entitlement, requested capabilities, and configuration-path evidence must be reviewed before any configuration artifact can be considered.</p></div><div className="flex flex-col items-stretch gap-2 sm:items-end"><label htmlFor="vendor-family-filter" className="text-[11px] font-bold uppercase tracking-[0.12em] text-slate-400">Filter family</label><select id="vendor-family-filter" value={selectedFamily} onChange={event => setSelectedFamily(event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700"><option value="all">All vendor families</option>{(supportQuery.data || []).map(vendor => <option key={vendor.vendorFamily} value={vendor.vendorFamily}>{vendor.displayName}</option>)}</select><Pill tone="amber">Engineer review required</Pill></div></div>{supportQuery.isLoading ? <p className="mt-6 text-sm text-slate-500">Loading vendor evidence boundaries…</p> : <div className="mt-6 grid gap-4 lg:grid-cols-2">{filterVendorSupport(supportQuery.data || [], selectedFamily).map(vendor => <article key={vendor.vendorFamily} className="rounded-2xl border border-slate-100 bg-slate-50 p-5"><div className="flex items-start justify-between gap-3"><div><h3 className="font-display text-lg font-semibold text-slate-950">{vendor.displayName}</h3><p className="mt-1 text-xs text-slate-500">Read-only discovery: {vendor.discoveryProtocols.join(" · ")}</p></div><Pill tone="amber">{vendor.configurationStatus.replaceAll("_", " ")}</Pill></div><div className="mt-4 grid gap-2 text-xs text-slate-600"><div className="flex justify-between gap-3"><span>Version policy</span><strong className="uppercase tracking-[0.08em] text-slate-500">{vendor.versionPolicyStatus.replaceAll("_", " ")}</strong></div><div className="flex justify-between gap-3"><span>License evidence</span><strong className="text-slate-700">Required</strong></div><div className="flex justify-between gap-3"><span>Config path evidence</span><strong className="text-slate-700">Required</strong></div></div><p className="mt-4 text-xs leading-5 text-slate-500">{vendor.boundary}</p><a href={vendor.sourceUrl} target="_blank" rel="noreferrer" className="mt-4 inline-flex text-xs font-semibold text-blue-700 hover:text-blue-900">Open official source <ArrowUpRight className="ml-1 h-3.5 w-3.5" /></a></article>)}</div>}</section></div>;
}

function DiscoveryPage({ project }: { project: ProjectRecord }) {
  const utils = trpc.useUtils();
  const sitesQuery = trpc.projects.sites.list.useQuery({ projectId: project.id });
  const runsQuery = trpc.projects.discoveryRuns.list.useQuery({ projectId: project.id });
  const multiAgentQuery = trpc.projects.multiAgentStatus.useQuery({ projectId: project.id });
  const createSite = trpc.projects.sites.create.useMutation({ onSuccess: () => { utils.projects.sites.list.invalidate({ projectId: project.id }); utils.projects.multiAgentStatus.invalidate({ projectId: project.id }); } });
  const createRun = trpc.projects.discoveryRuns.create.useMutation({ onSuccess: () => { utils.projects.discoveryRuns.list.invalidate({ projectId: project.id }); utils.projects.multiAgentStatus.invalidate({ projectId: project.id }); } });
  const [siteName, setSiteName] = useState("");
  const [scopeReference, setScopeReference] = useState("");
  const [selectedSite, setSelectedSite] = useState<number | null>(null);
  const [scopeHash, setScopeHash] = useState("");
  const sites = sitesQuery.data || [];
  const submitSite = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (siteName.trim().length < 2 || scopeReference.trim().length < 2) return;
    createSite.mutate({ projectId: project.id, name: siteName.trim(), approvedScopeReference: scopeReference.trim() });
    setSiteName("");
    setScopeReference("");
  };
  const submitRun = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedSite || scopeHash.trim().length < 8) return;
    createRun.mutate({ projectId: project.id, siteId: selectedSite, scopeHash: scopeHash.trim(), evidenceSummary: "Queued for authorized read-only collection." });
  };
  return <div className="space-y-7"><TitleBlock eyebrow="02 · Discovery" title="Authorized discovery workspace" description="Register a site and queue read-only evidence collection. This console never opens a device session or changes production state." /><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Specialist coordination</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Evidence team and human Go/No-Go</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">Specialists can coordinate authorized discovery, evidence review, design preparation, capability assessment, virtual validation, and safety review. They cannot approve, waive a blocker, upload a production configuration, or execute a change.</p></div><Pill tone="red">Production execution blocked</Pill></div>{multiAgentQuery.isLoading ? <p className="mt-5 text-sm text-slate-500">Assessing bounded workflow status…</p> : multiAgentQuery.data ? <><div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{multiAgentQuery.data.stages.map(stage => <article key={stage.role} className="rounded-2xl border border-slate-100 bg-slate-50 p-4"><div className="flex items-start justify-between gap-3"><p className="text-sm font-semibold capitalize text-slate-800">{stage.role.replaceAll("_", " ")}</p><Pill tone={stage.state === "completed" || stage.state === "ready" ? "green" : stage.state === "blocked" ? "red" : "amber"}>{stage.state.replaceAll("_", " ")}</Pill></div><p className="mt-2 text-xs leading-5 text-slate-500">{stage.detail}</p></article>)}</div><div className="mt-4 grid gap-3 md:grid-cols-2"><div className="rounded-2xl border border-amber-100 bg-amber-50 p-4"><p className="text-xs font-bold uppercase tracking-[0.12em] text-amber-700">Human Go/No-Go required</p><p className="mt-2 text-sm leading-6 text-amber-900">{multiAgentQuery.data.humanGoNoGo.detail}</p></div><div className="rounded-2xl border border-rose-100 bg-rose-50 p-4"><p className="text-xs font-bold uppercase tracking-[0.12em] text-rose-700">Automatic production execution</p><p className="mt-2 text-sm leading-6 text-rose-900">{multiAgentQuery.data.productionExecution.detail}</p></div></div></> : <p className="mt-5 text-sm text-slate-500">No coordination status is available for this project.</p>}</section><div className="grid gap-5 xl:grid-cols-2"><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Scope registration</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Human-approved site boundary</h2></div><Pill tone="amber">Read-only by default</Pill></div><form onSubmit={submitSite} className="mt-5 space-y-3"><input aria-label="Site name" value={siteName} onChange={event => setSiteName(event.target.value)} placeholder="Site name" className="h-10 w-full rounded-xl border border-slate-200 px-3 text-sm" /><input aria-label="Approved scope reference" value={scopeReference} onChange={event => setScopeReference(event.target.value)} placeholder="Approved CIDR / target-list reference" className="h-10 w-full rounded-xl border border-slate-200 px-3 text-sm" /><button disabled={createSite.isPending} className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{createSite.isPending ? "Saving…" : "Register site boundary"}</button></form><div className="mt-6 space-y-2">{sitesQuery.isLoading ? <p className="text-sm text-slate-500">Loading sites…</p> : sites.length === 0 ? <p className="text-sm text-slate-500">No site scope registered for this project.</p> : sites.map(site => <button key={site.id} onClick={() => setSelectedSite(site.id)} className={cn("flex w-full items-center justify-between rounded-xl border px-3 py-3 text-left text-sm", selectedSite === site.id ? "border-cyan-400 bg-cyan-50" : "border-slate-100 bg-slate-50")}><span><strong className="block text-slate-800">{site.name}</strong><span className="text-xs text-slate-500">Scope ref: {site.approvedScopeReference}</span></span><Pill tone={site.enrollmentState === "active" ? "green" : "amber"}>{site.enrollmentState.replaceAll("_", " ")}</Pill></button>)}</div></section><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Evidence collection</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Queue a read-only run</h2></div><Pill tone="blue">No device execution</Pill></div><form onSubmit={submitRun} className="mt-5 space-y-3"><select aria-label="Discovery site" value={selectedSite ?? ""} onChange={event => setSelectedSite(Number(event.target.value) || null)} className="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"><option value="">Select a registered site</option>{sites.map(site => <option key={site.id} value={site.id}>{site.name}</option>)}</select><input aria-label="Scope hash" value={scopeHash} onChange={event => setScopeHash(event.target.value)} placeholder="Scope hash from approved scope record" className="h-10 w-full rounded-xl border border-slate-200 px-3 text-sm" /><button disabled={createRun.isPending} className="rounded-xl bg-cyan-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{createRun.isPending ? "Queueing…" : "Queue read-only discovery"}</button></form><div className="mt-6 space-y-2">{runsQuery.isLoading ? <p className="text-sm text-slate-500">Loading discovery runs…</p> : (runsQuery.data || []).length === 0 ? <p className="text-sm text-slate-500">No discovery run has been queued.</p> : (runsQuery.data || []).map(item => <div key={item.run.id} className="rounded-xl border border-slate-100 bg-slate-50 p-3"><div className="flex items-center justify-between gap-3"><span className="text-sm font-semibold text-slate-800">{item.siteName}</span><Pill tone={item.run.state === "completed" ? "green" : item.run.state === "blocked" ? "red" : "amber"}>{item.run.state.replaceAll("_", " ")}</Pill></div><p className="mt-2 text-xs leading-5 text-slate-500">{item.run.evidenceSummary || "Evidence summary not yet recorded."}</p><p className="mt-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-400">Ambiguous: {item.run.ambiguousCount} · Unsupported: {item.run.unsupportedCount}</p></div>)}</div></section></div></div>;
}

function AdminPage({ project }: { project: ProjectRecord }) {
  const supportQuery = trpc.vendorSupport.list.useQuery();
  return <div className="space-y-7"><TitleBlock eyebrow="10 · Administration" title="Control plane settings" description="This area summarizes the hosted workspace boundary. It does not expose credentials, tokens, raw secret material, or unmanaged production device access." /><div className="grid gap-5 md:grid-cols-2"><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><UsersRound className="h-6 w-6 text-blue-700" /><h2 className="mt-5 font-display text-xl font-semibold text-slate-950">Workspace access</h2><p className="mt-2 text-sm leading-6 text-slate-500">Authenticated users see only their own project records. Administrative approval is restricted to authorized accounts.</p></section><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><ShieldCheck className="h-6 w-6 text-emerald-700" /><h2 className="mt-5 font-display text-xl font-semibold text-slate-950">Current project safety</h2><p className="mt-2 text-sm leading-6 text-slate-500">Approval state: <span className="font-semibold text-slate-700">{project.approvalState.replaceAll("_", " ")}</span>. Secret material is not stored in the audit surface.</p></section></div><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Vendor support boundary</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Evidence before configuration</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">The registry exposes read-only discovery contracts for the four initial vendor families. Configuration remains blocked until exact platform, version, license, and configuration-path evidence is verified.</p></div><Pill tone="amber">No universal support claim</Pill></div>{supportQuery.isLoading ? <p className="mt-6 text-sm text-slate-500">Loading vendor boundaries…</p> : <div className="mt-6 grid gap-3 lg:grid-cols-2">{(supportQuery.data || []).map(vendor => <div key={vendor.vendorFamily} className="rounded-2xl border border-slate-100 bg-slate-50 p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-slate-800">{vendor.displayName}</p><p className="mt-1 text-xs text-slate-500">Discovery: {vendor.discoveryProtocols.join(" · ")}</p></div><Pill tone="amber">{vendor.configurationStatus.replaceAll("_", " ")}</Pill></div><p className="mt-3 text-xs leading-5 text-slate-500">{vendor.boundary}</p><p className="mt-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-400">Version policy: {vendor.versionPolicyStatus.replaceAll("_", " ")}</p><a href={vendor.sourceUrl} target="_blank" rel="noreferrer" className="mt-3 inline-flex text-xs font-semibold text-blue-700 hover:text-blue-900">View official evidence source <ArrowUpRight className="ml-1 h-3.5 w-3.5" /></a></div>)}</div>}</section></div>;
}

function AuditPage() {
  const [page, setPage] = useState(1);
  const auditQuery = trpc.audit.list.useQuery({ page, pageSize: 8 });
  const totalPages = Math.max(1, Math.ceil((auditQuery.data?.total || 0) / 8));
  return <div className="space-y-7"><TitleBlock eyebrow="11 · Accountability" title="Audit trail" description="A paginated record of project actions with actor, time, and redacted event details. Sensitive values and secret-like references are removed before the data reaches this view." /><section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 px-6 py-5"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Redacted activity log</p><h2 className="mt-2 font-display text-xl font-semibold text-slate-950">Project accountability</h2></div><Pill tone="green"><ShieldCheck className="h-3.5 w-3.5" /> Secret-safe view</Pill></div>{auditQuery.isLoading ? <div className="p-8 text-sm text-slate-500">Loading audit events…</div> : auditQuery.data?.items.length ? <><div className="divide-y divide-slate-100">{auditQuery.data.items.map(event => <div key={event.id} className="grid gap-2 px-6 py-4 md:grid-cols-[1.1fr_.9fr_.8fr]"><div><p className="text-sm font-semibold text-slate-700">{event.action.replaceAll(".", " · ")}</p><p className="mt-1 text-xs text-slate-500">{event.details}</p></div><div className="text-sm text-slate-600">{event.projectName}<p className="mt-1 text-xs text-slate-400">{event.actorName}</p></div><div className="text-sm text-slate-500 md:text-right">{relativeTime(event.createdAt)}</div></div>)}</div><div className="flex items-center justify-between px-6 py-4"><p className="text-xs text-slate-500">Page {page} of {totalPages}</p><div className="flex gap-2"><button disabled={page === 1} onClick={() => setPage(value => value - 1)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold disabled:opacity-40">Previous</button><button disabled={page === totalPages} onClick={() => setPage(value => value + 1)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold disabled:opacity-40">Next</button></div></div></> : <div className="p-10 text-center"><Search className="mx-auto h-7 w-7 text-slate-300" /><p className="mt-3 text-sm font-semibold text-slate-700">No project actions yet</p><p className="mt-1 text-xs text-slate-500">Create or update a project to establish an auditable record.</p></div>}</section></div>;
}

function Workspace({ user, projects, selectedProject, selectedProjectId, location, navigate, onSelectProject, onCreate, onDelete }: { user: { name?: string | null; email?: string | null; role: "admin" | "user" }; projects: ProjectRecord[]; selectedProject: ProjectRecord | null; selectedProjectId: number | null; location: string; navigate: (path: string) => void; onSelectProject: (id: number) => void; onCreate: () => void; onDelete: () => void }) {
  const utils = trpc.useUtils();
  const active = navItems.find(item => item.path === location) || navItems[0];
  const requestApproval = trpc.projects.requestApproval.useMutation({ onSuccess: () => { utils.projects.get.invalidate(); utils.projects.list.invalidate(); } });
  const approve = trpc.projects.approve.useMutation({ onSuccess: () => { utils.projects.get.invalidate(); utils.projects.list.invalidate(); } });
  const saveQuestionnaire = trpc.projects.updateQuestionnaire.useMutation({ onSuccess: () => { utils.projects.get.invalidate(); utils.projects.list.invalidate(); } });
  const openProject = (id: number) => { onSelectProject(id); navigate("/"); };
  const project = selectedProject;
  const activeGroups = ["Workflow", "Governance"] as const;
  return <SidebarProvider defaultOpen><Sidebar collapsible="icon" className="border-r border-slate-800 bg-slate-950 text-slate-300"><SidebarHeader className="border-b border-white/10 px-3 py-4"><button onClick={() => navigate("/")} className="flex items-center gap-3 px-2 text-left"><span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-cyan-300 to-blue-600 text-slate-950 shadow-lg shadow-cyan-500/20"><Network className="h-5 w-5" /></span><span className="group-data-[collapsible=icon]:hidden"><strong className="font-display text-base font-semibold tracking-[-0.03em] text-white">AutoNet</strong><span className="block text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-500">Architect</span></span></button></SidebarHeader><SidebarContent className="px-2 py-3">{activeGroups.map(group => <SidebarGroup key={group} className="px-0 py-2"><SidebarGroupLabel className="px-3 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">{group}</SidebarGroupLabel><SidebarGroupContent><SidebarMenu>{navItems.filter(item => item.group === group).map(item => { const Icon = item.icon; const isActive = item.path === active.path; return <SidebarMenuItem key={item.label}><SidebarMenuButton isActive={isActive} tooltip={item.label} onClick={() => navigate(item.path)} className={cn("h-9 rounded-lg text-slate-400 hover:bg-white/8 hover:text-white data-[active=true]:bg-white/10 data-[active=true]:text-white", isActive && "text-white")}><Icon className="h-4 w-4" /><span>{item.label}</span></SidebarMenuButton></SidebarMenuItem>; })}</SidebarMenu></SidebarGroupContent></SidebarGroup>)}</SidebarContent><SidebarFooter className="border-t border-white/10 p-3"><div className="group-data-[collapsible=icon]:hidden rounded-xl bg-white/5 px-3 py-3"><p className="truncate text-xs font-semibold text-white">{user.name || user.email || "Authenticated user"}</p><p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">{user.role} workspace</p></div></SidebarFooter></Sidebar><SidebarInset className="min-w-0 bg-[#f7f9fc]"><header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200/80 bg-[#f7f9fc]/90 px-4 backdrop-blur-xl sm:px-6"><div className="flex min-w-0 items-center gap-3"><SidebarTrigger className="rounded-lg border border-slate-200 bg-white text-slate-600 shadow-sm"><Menu className="h-4 w-4" /></SidebarTrigger><div className="hidden h-6 w-px bg-slate-200 sm:block"/><p className="truncate text-sm font-semibold text-slate-700">{active.label}</p></div><div className="flex items-center gap-2"><span className="hidden text-xs text-slate-500 lg:block">Engineer-supervised workflow</span><div className="h-7 w-7 rounded-full bg-gradient-to-br from-slate-200 to-cyan-200 ring-2 ring-white" /></div></header><main className="mx-auto w-full max-w-[1440px] px-4 py-7 sm:px-6 lg:px-8">{projects.length ? <div className="mb-7 flex flex-col justify-between gap-4 border-b border-slate-200 pb-6 xl:flex-row xl:items-center"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">Active project</p><p className="mt-1 text-sm font-semibold text-slate-800">{project?.name || "Select a project"}</p></div><ProjectPicker projects={projects} selectedProjectId={selectedProjectId} onSelect={openProject} onCreate={onCreate} /></div> : null}{!project ? <EmptyProjectState onCreate={onCreate} /> : active.path === "/" ? <DashboardPage project={project} projects={projects} onNavigate={navigate} onSelect={openProject} onCreate={onCreate} onDelete={onDelete} /> : active.path === "/questionnaire" ? <QuestionnairePage project={project} isSaving={saveQuestionnaire.isPending} onSave={values => saveQuestionnaire.mutate({ projectId: project.id, organization: values.organization, organizationType: values.organizationType, siteCount: Number(values.siteCount || 0), classification: values.classification, vendorPreferences: values.vendorPreferences, complianceNeeds: values.complianceNeeds })} /> : active.path === "/requirements" ? <RequirementsPage project={project} onNavigate={navigate} /> : active.path === "/discovery" ? <DiscoveryPage project={project} /> : active.path === "/design" ? <DesignPage project={project} /> : active.path === "/equipment" ? <EquipmentPage project={project} /> : active.path === "/configs" ? <ConfigsPage project={project} /> : active.path === "/deployment" ? <DeploymentPage project={project} isAdmin={user.role === "admin"} onRequest={() => requestApproval.mutate({ projectId: project.id })} onApprove={() => approve.mutate({ projectId: project.id })} requestPending={requestApproval.isPending} approvePending={approve.isPending} /> : active.path === "/operations" ? <OperationsPage /> : active.path === "/compliance" ? <CompliancePage project={project} /> : active.path === "/reports" ? <ReportsPage /> : active.path === "/admin" ? <AdminPage project={project} /> : active.path === "/vendor-support" ? <VendorSupportPage /> : <AuditPage />}</main></SidebarInset></SidebarProvider>;
}

export default function AutoNetApp() {
  const [location, navigate] = useLocation();
  const [showCreate, setShowCreate] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const { user, loading, isAuthenticated, logout } = useAuth();
  const utils = trpc.useUtils();
  const projectsQuery = trpc.projects.list.useQuery(undefined, { enabled: isAuthenticated });
  const projects = (projectsQuery.data || []) as ProjectRecord[];
  useEffect(() => { if (projects.length && !selectedProjectId) setSelectedProjectId(projects[0].id); }, [projects, selectedProjectId]);
  useEffect(() => { if (selectedProjectId) { window.localStorage.setItem("autonet.activeProjectId", String(selectedProjectId)); window.dispatchEvent(new Event("autonet-project-changed")); } }, [selectedProjectId]);
  const projectQuery = trpc.projects.get.useQuery({ projectId: selectedProjectId || 0 }, { enabled: isAuthenticated && Boolean(selectedProjectId) });
  const createProject = trpc.projects.create.useMutation({ onSuccess: async project => { await utils.projects.list.invalidate(); setSelectedProjectId(project.id); setShowCreate(false); navigate("/"); } });
  const removeProject = trpc.projects.remove.useMutation({ onSuccess: async () => { await utils.projects.list.invalidate(); setSelectedProjectId(null); navigate("/"); } });
  const selectedProject = (projectQuery.data || projects.find(project => project.id === selectedProjectId) || null) as ProjectRecord | null;
  const handleDelete = () => { if (selectedProject && window.confirm(`Delete ${selectedProject.name}? This only removes the hosted project record.`)) removeProject.mutate({ projectId: selectedProject.id }); };
  if (loading) return <div className="grid min-h-screen place-items-center bg-[#f7f9fc]"><div className="text-center"><div className="mx-auto h-10 w-10 animate-pulse rounded-2xl bg-gradient-to-br from-cyan-300 to-blue-600"/><p className="mt-4 text-sm font-medium text-slate-500">Opening controlled workspace…</p></div></div>;
  if (!isAuthenticated || !user) return <div className="login-grid grid min-h-screen place-items-center bg-slate-950 p-6"><section className="relative max-w-xl overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.06] p-8 text-center text-white shadow-2xl shadow-black/30 backdrop-blur-xl sm:p-12"><div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-cyan-400/15 to-transparent"/><div className="relative"><div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-cyan-300 to-blue-600 text-slate-950 shadow-lg shadow-cyan-400/20"><Network className="h-7 w-7" /></div><p className="mt-7 text-[11px] font-bold uppercase tracking-[0.2em] text-cyan-200">AutoNetArchitect</p><h1 className="mt-3 font-display text-4xl font-semibold tracking-[-0.05em]">Network lifecycle, under human control.</h1><p className="mx-auto mt-5 max-w-md text-sm leading-6 text-slate-300">Enter an authenticated workspace for structured requirements, accountable decisions, capability-bound configs, and explicit deployment gates.</p><button onClick={startLogin} className="mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-950 shadow-lg transition hover:-translate-y-0.5 hover:bg-slate-100">Sign in to workspace <ArrowUpRight className="h-4 w-4" /></button><p className="mt-5 text-xs text-slate-500">No secret values are displayed in audit records or project summaries.</p></div></section></div>;
  return <><Workspace user={user} projects={projects} selectedProject={selectedProject} selectedProjectId={selectedProjectId} location={location} navigate={navigate} onSelectProject={setSelectedProjectId} onCreate={() => setShowCreate(true)} onDelete={handleDelete} />{showCreate && <ProjectModal onClose={() => setShowCreate(false)} onCreate={(name, organization) => createProject.mutate({ name, organization })} isSaving={createProject.isPending} />}{projectsQuery.error && <div className="fixed bottom-4 right-4 rounded-xl bg-rose-600 px-4 py-3 text-sm font-semibold text-white shadow-xl">Unable to load project data. Please refresh.</div>}{removeProject.error && <div className="fixed bottom-4 right-4 rounded-xl bg-rose-600 px-4 py-3 text-sm font-semibold text-white shadow-xl">Unable to remove this project.</div>}<button onClick={() => logout()} className="fixed bottom-4 left-4 z-40 rounded-lg bg-white/90 px-3 py-1.5 text-[11px] font-semibold text-slate-500 shadow-sm ring-1 ring-slate-200 transition hover:text-slate-800">Sign out</button></>;
}
