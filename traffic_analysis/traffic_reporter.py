"""Traffic analysis reporting and exports."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from ._common import make_decision
from .models import TrafficAnalysis

class TrafficReporter:
    """Render bilingual traffic summaries and local PDF/Excel artifacts."""
    def __init__(self) -> None:
        """Initialize reporting state."""
        self.decisions = []
        self.assumptions = []
    def summary(self, analysis: TrafficAnalysis, *, language: str = "en") -> dict[str, Any]:
        """Return a summary report."""
        if language not in {"en", "ar"}:
            raise ValueError("language must be en or ar")
        title = "Traffic Summary Report" if language == "en" else "تقرير ملخص حركة المرور"
        return {"title": title, "analysis_id": analysis.analysis_id, "mode": analysis.mode.value, "link_count": len(analysis.links), "top_utilized_links": sorted([{"link_id": link.link_id, "peak_utilization_percent": link.traffic_data.peak_utilization_percent} for link in analysis.links], key=lambda item: item["peak_utilization_percent"] or -1, reverse=True)[:10], "bottleneck_count": len(analysis.bottlenecks), "anomaly_count": len(analysis.anomalies), "upgrade_count": len(analysis.upgrade_recommendations), "limitations": analysis.limitations, "evidence_ids": analysis.evidence_ids, "assumptions": analysis.assumptions}
    def to_json(self, payload: Mapping[str, Any], path: str | Path | None = None) -> str:
        """Serialize report data to JSON."""
        text = json.dumps(dict(payload), indent=2, ensure_ascii=False, default=str) + "\\n"
        if path is not None:
            target = Path(path); target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text, encoding="utf-8")
        return text
    def to_pdf(self, payload: Mapping[str, Any], path: str | Path) -> str:
        """Export a concise PDF report."""
        target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
        pdf = canvas.Canvas(str(target), pagesize=A4); _, height = A4; y = height - 40
        for line in json.dumps(dict(payload), indent=2, ensure_ascii=False, default=str).splitlines():
            if y < 40: pdf.showPage(); y = height - 40
            pdf.setFont("Helvetica", 8); pdf.drawString(36, y, line[:180]); y -= 11
        pdf.save(); return str(target)
    def to_excel(self, analysis: TrafficAnalysis, path: str | Path) -> str:
        """Export link utilization and capacity findings to XLSX."""
        from openpyxl import Workbook
        target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
        workbook = Workbook(); sheet = workbook.active; sheet.title = "Traffic Links"
        sheet.append(["link_id", "source", "destination", "speed_mbps", "avg_utilization_percent", "peak_utilization_percent", "source_type"])
        for link in analysis.links:
            sheet.append([link.link_id, f"{link.source_device}:{link.source_interface}", f"{link.destination_device}:{link.destination_interface}", link.link_speed_mbps, link.traffic_data.avg_utilization_percent, link.traffic_data.peak_utilization_percent, link.traffic_data.source.value])
        workbook.save(target); return str(target)
