"""
Bhujal — Action Dossier and Planning Report Generator
======================================================
Compiles planner-ready HTML administrative dossiers summarizing
multi-agent findings, safety vetoes, civil engineering bills of quantities,
and climate scenario projections.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.models import ReportResult, Site

REPORTS_DIR = Path(__file__).resolve().parent.parent / "data" / "reports"


def generate_action_dossier_html(
    sites: list[Site],
    orchestrator_summary: str,
    orchestrator_narrative: str,
    scenario_info: dict[str, Any] | None = None,
) -> str:
    """Render self-contained, publication-grade HTML action dossier."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    rows_html = ""
    for s in sites:
        v = s.village
        scores_dict = {sc.score_type: sc for sc in s.scores}
        recharge = scores_dict.get("recharge_score")
        stress = scores_dict.get("heat_water_stress")
        spring = scores_dict.get("spring_drying_index")

        safety_status = s.safety.status.value if s.safety else "SAFE"
        safety_color = (
            "#15803d"
            if safety_status == "SAFE"
            else ("#b45309" if safety_status == "CONDITIONAL" else "#b91c1c")
        )

        top_rec = s.recommendations[0] if s.recommendations else None
        if top_rec:
            rec_text = f"<strong>{top_rec.intervention_name}</strong><br>INR {top_rec.cost_range_inr.get('low', 0):,} - {top_rec.cost_range_inr.get('high', 0):,}<br><small>{top_rec.labour_days} MGNREGA days</small>"
        elif safety_status == "REJECTED":
            rec_text = "<span style='color: #b91c1c;'>VETOED (Safety Hazard)</span>"
        else:
            rec_text = "<span>Bio-engineering only</span>"

        rows_html += f"""
        <tr>
            <td><strong>{v.name}</strong><br><small>{v.block} Block</small></td>
            <td><span class="badge" style="background: {safety_color}; color: #fff;">{safety_status}</span></td>
            <td>{recharge.value:.1f} <small>({recharge.score_class.value})</small></td>
            <td>{stress.value:.1f} <small>({stress.score_class.value})</small></td>
            <td>{f"{spring.value:.1f} ({spring.score_class.value})" if v.has_spring else "N/A (No Spring)"}</td>
            <td>{rec_text}</td>
            <td><span class="badge badge-subtle">{v.data_tag.value.upper()}</span></td>
        </tr>
        """

    scenario_block = ""
    if scenario_info:
        scenario_block = f"""
        <div class="card">
            <h3>Climate Sensitivity Scenario</h3>
            <p><strong>Precipitation Anomaly:</strong> {scenario_info.get("rainfall_fraction", 1.0):.2f}x baseline normal</p>
            <p><strong>Simulation Notes:</strong> {"; ".join(scenario_info.get("notes", []))}</p>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bhujal Action Dossier — Koraput District</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #1e293b;
            background: #f8fafc;
            line-height: 1.6;
            margin: 0;
            padding: 32px 16px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 40px;
        }}
        .header {{
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 24px;
            margin-bottom: 28px;
        }}
        h1 {{
            font-size: 26px;
            margin: 0 0 8px 0;
            color: #0f172a;
        }}
        .meta-line {{
            font-size: 14px;
            color: #64748b;
        }}
        .card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        .card h3 {{
            margin-top: 0;
            color: #0f172a;
            font-size: 18px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px 14px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
            vertical-align: top;
        }}
        th {{
            background: #f1f5f9;
            color: #334155;
            font-weight: 600;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 700;
            border-radius: 4px;
            letter-spacing: 0.5px;
        }}
        .badge-subtle {{
            background: #e2e8f0;
            color: #475569;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            font-size: 12px;
            color: #94a3b8;
            text-align: center;
        }}
        @media print {{
            body {{ background: #fff; padding: 0; }}
            .container {{ box-shadow: none; border-radius: 0; padding: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Bhujal: Watershed Planning Action Dossier</h1>
            <div class="meta-line">
                <strong>Area of Interest:</strong> Koraput District, Odisha &bull; 
                <strong>Generated:</strong> {timestamp} &bull; 
                <strong>Authority:</strong> District Watershed Management Cell
            </div>
        </div>

        <div class="card">
            <h3>Executive Determination</h3>
            <p><strong>Summary:</strong> {orchestrator_summary}</p>
            <div style="white-space: pre-line; font-size: 14px; color: #334155;">{orchestrator_narrative}</div>
        </div>

        {scenario_block}

        <h3>Site Assessments & Civil Interventions</h3>
        <table>
            <thead>
                <tr>
                    <th>Settlement</th>
                    <th>Safety Status</th>
                    <th>Recharge Score</th>
                    <th>Heat-Water Stress</th>
                    <th>Spring Drying Index</th>
                    <th>Intervention & Cost</th>
                    <th>Provenance</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>

        <div class="footer">
            Bhujal Decision-Support System &bull; Amazon Environmental Hacks 2026 &bull; Strict Empirical Governance Protocol
        </div>
    </div>
</body>
</html>
"""
    return html


def create_report(
    sites: list[Site],
    orchestrator_summary: str,
    orchestrator_narrative: str,
    scenario_info: dict[str, Any] | None = None,
) -> ReportResult:
    """Generate and write the action dossier to the local reports directory."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_id = f"rpt_{uuid.uuid4().hex[:10]}"
    filename = f"{report_id}.html"
    filepath = REPORTS_DIR / filename

    html_content = generate_action_dossier_html(
        sites=sites,
        orchestrator_summary=orchestrator_summary,
        orchestrator_narrative=orchestrator_narrative,
        scenario_info=scenario_info,
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return ReportResult(
        report_id=report_id,
        title="Bhujal Comprehensive Watershed Planning Dossier",
        generated_at=datetime.now(timezone.utc),
        site_count=len(sites),
        download_url=f"/reports/{filename}",
        format="html",
        summary=orchestrator_summary,
    )
