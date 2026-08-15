"""Evidence-bounded benchmark scoring and reporting."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .design_quality_metrics import MetricResult
from .pilot_evidence_registry import PilotEvidenceRecord, PilotStatus
from .reliability_statistics import ReliabilityStatistic


class EvidenceBoundedClaim(BaseModel):
    """A measured statement with explicit evidence and limitations."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str
    statement: str
    allowed: bool
    metric_name: str
    numerator: float
    denominator: int
    evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class BenchmarkReport(BaseModel):
    """Repeatable benchmark report with no unsupported maturity language."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    corpus_fingerprint: str
    run_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: tuple[dict[str, Any], ...] = ()
    reliability_statistics: tuple[dict[str, Any], ...] = ()
    claims: tuple[EvidenceBoundedClaim, ...] = ()
    pilot_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    maturity_statement: str = "Measured benchmark evidence is available only within the declared corpus, scope, sample, and limitations."


class ScoringReporter(BaseDesigner):
    """Generate scoring artifacts that cannot overclaim beyond measured evidence."""

    def __init__(self) -> None:
        """Initialize reporter."""
        super().__init__("ScoringReporter")
        self.record_decision("claim_policy", "measured_evidence_only", "reporter emits metric-bound statements and refuses engineer-equivalence claims")

    def generate(self, *, report_id: str, corpus_fingerprint: str, run_id: str, metrics: Iterable[MetricResult] = (), reliability_statistics: Iterable[ReliabilityStatistic] = (), pilots: Iterable[PilotEvidenceRecord] = ()) -> BenchmarkReport:
        """Generate a report from measured results and scoped pilot records."""
        metric_items = tuple(metrics)
        statistic_items = tuple(reliability_statistics)
        pilot_items = tuple(pilots)
        claims: list[EvidenceBoundedClaim] = []
        limitations: list[str] = []
        for metric in metric_items:
            allowed = metric.denominator > 0 and bool(metric.evidence_ids)
            if not allowed:
                limitations.append(f"{metric.metric_name}: insufficient sample or evidence identifiers")
            claims.append(EvidenceBoundedClaim(claim_id=f"claim:{metric.metric_name}", statement=f"Measured {metric.metric_name}: numerator={metric.numerator}, denominator={metric.denominator}, rate={metric.rate}, mean={metric.mean}.", allowed=allowed, metric_name=metric.metric_name, numerator=metric.numerator, denominator=metric.denominator, evidence_ids=metric.evidence_ids, limitations=("scope limited to measured observations",) if allowed else ("not publishable as a quality claim",)))
        for pilot in pilot_items:
            if pilot.status != PilotStatus.VALIDATED:
                limitations.append(f"pilot {pilot.pilot_id}: human validation incomplete")
            limitations.extend(f"pilot {pilot.pilot_id}: {item}" for item in pilot.limitations)
        if not pilot_items:
            limitations.append("no pilot evidence records supplied")
        report = BenchmarkReport(report_id=report_id, corpus_fingerprint=corpus_fingerprint, run_id=run_id, metrics=tuple(item.model_dump(mode="json") for item in metric_items), reliability_statistics=tuple(item.model_dump(mode="json") for item in statistic_items), claims=tuple(claims), pilot_ids=tuple(item.pilot_id for item in pilot_items), limitations=tuple(dict.fromkeys(limitations)))
        self.record_decision(f"benchmark_report:{report_id}", "generated", "report claims are limited to metrics with evidence and declared sample size")
        return report

    def to_markdown(self, report: BenchmarkReport) -> str:
        """Render a bilingual scoring report."""
        lines = [f"# Production Evidence & Benchmark Report / تقرير أدلة الإنتاج والمقارنة", "", f"**Run / التشغيل:** {report.run_id}", f"**Corpus fingerprint / بصمة corpus:** `{report.corpus_fingerprint}`", f"**Generated / التوليد:** {report.generated_at.isoformat()}", "", "## Measured Metrics / المقاييس المقاسة", "", "| Metric | Numerator | Denominator | Rate | Claim allowed |", "| --- | ---: | ---: | ---: | --- |"]
        for claim in report.claims:
            lines.append(f"| {claim.metric_name} | {claim.numerator} | {claim.denominator} | {claim.statement.split('rate=')[-1].rstrip('.') if 'rate=' in claim.statement else 'n/a'} | {claim.allowed} |")
        lines.extend(["", "## Limitations / الحدود", ""])
        lines.extend(f"- {item}" for item in report.limitations) if report.limitations else lines.append("- none recorded / لا توجد حدود مسجلة")
        lines.extend(["", f"> {report.maturity_statement}", "> لا يجوز تحويل هذه النتائج إلى ادعاء تكافؤ مع المهندس أو جاهزية إنتاجية خارج النطاق المقاس."])
        return "\n".join(lines) + "\n"

    def write_json(self, report: BenchmarkReport, output_path: str | Path) -> Path:
        """Write benchmark report JSON."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return target
