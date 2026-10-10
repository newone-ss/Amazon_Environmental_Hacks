"""
Bhujal — Auto DPR (Detailed Project Report) Generator
=======================================================
Generates government-ready Detailed Project Reports in GoI format.
Outputs: .docx (main report), .xlsx (cost abstracts), .kml (site boundaries), .zip package.
"""

from __future__ import annotations

import importlib.util
import io
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from backend.models import (
    SafetyStatus,
    ScoreClass,
    Site,
)
from scoring import evaluate_site

# Check for weasyprint availability (optional)
WEASYPRINT_AVAILABLE = importlib.util.find_spec("weasyprint") is not None

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

# ── Scheme Mapping ──────────────────────────────────────────────────

SCHEME_MAPPING: dict[str, dict[str, Any]] = {
    "check_dam": {
        "primary_scheme": "MGNREGA",
        "eligible_schemes": ["MGNREGA", "PMKSY-Watershed", "CAMPA"],
        "funding_pattern": "Central:State = 60:40 (90:10 for NE/Himalayan)",
        "technical_sanction_authority": "Executive Engineer, WRD",
        "admin_approval_authority": "District Collector",
    },
    "percolation_tank": {
        "primary_scheme": "MGNREGA",
        "eligible_schemes": ["MGNREGA", "PMKSY-Watershed", "JJM-Source Sustainability"],
        "funding_pattern": "Central:State = 60:40",
        "technical_sanction_authority": "Executive Engineer, WRD",
        "admin_approval_authority": "District Collector",
    },
    "contour_trench": {
        "primary_scheme": "MGNREGA",
        "eligible_schemes": ["MGNREGA", "CAMPA", "NABARD-WDF"],
        "funding_pattern": "Central:State = 60:40",
        "technical_sanction_authority": "Assistant Engineer, WRD",
        "admin_approval_authority": "Block Development Officer",
    },
    "spring_shed_treatment": {
        "primary_scheme": "MGNREGA",
        "eligible_schemes": ["MGNREGA", "JJM-Spring Revival", "CAMPA", "NABARD-WDF"],
        "funding_pattern": "Central:State = 60:40 (100% CSS for spring revival under JJM)",
        "technical_sanction_authority": "Executive Engineer, PHED/WRD",
        "admin_approval_authority": "District Collector",
    },
    "rooftop_rainwater_harvesting": {
        "primary_scheme": "JJM",
        "eligible_schemes": ["JJM", "MGNREGA", "AMRUT", "Smart Cities Mission"],
        "funding_pattern": "Central:State = 50:50 (JJM), 60:40 (MGNREGA)",
        "technical_sanction_authority": "Executive Engineer, PHED",
        "admin_approval_authority": "District Collector / ULB Commissioner",
    },
    "farm_pond": {
        "primary_scheme": "PMKSY",
        "eligible_schemes": ["PMKSY-Per Drop More Crop", "MGNREGA", "RKVY"],
        "funding_pattern": "Central:State = 60:40 (90:10 for NE/Himalayan)",
        "technical_sanction_authority": "Assistant Engineer, Agriculture/WRD",
        "admin_approval_authority": "District Collector",
    },
    "gabion_structure": {
        "primary_scheme": "MGNREGA",
        "eligible_schemes": [
            "MGNREGA",
            "PMKSY-Watershed",
            "Flood Management Programme",
        ],
        "funding_pattern": "Central:State = 60:40",
        "technical_sanction_authority": "Executive Engineer, WRD",
        "admin_approval_authority": "District Collector",
    },
}

STATE_SCHEME_NUANCES: dict[str, dict[str, str]] = {
    "Odisha": {
        "MGNREGA": "Odisha MGNREGA (wage: INR 350/day)",
        "JJM": "Odisha JJM - Basudha Scheme convergence",
        "PMKSY": "PMKSY 2.0 - Odisha Watershed",
    },
    "Madhya Pradesh": {
        "MGNREGA": "MP MGNREGA (wage: INR 243/day)",
        "JJM": "MP JJM - Nal Jal Yojana",
        "PMKSY": "PMKSY - MP Jal Grahan Vikas",
    },
    "Jharkhand": {
        "MGNREGA": "Jharkhand MGNREGA (wage: INR 255/day)",
        "JJM": "Jharkhand JJM - Har Ghar Jal",
        "PMKSY": "PMKSY - Jharkhand Watershed",
    },
}


# ── DPR Data Classes ────────────────────────────────────────────────


@dataclass
class DPRPackage:
    """Complete DPR package for a site or multi-site project."""

    project_id: str
    project_name: str
    sites: list[Site]
    generated_at: datetime
    docx_bytes: bytes
    xlsx_bytes: bytes
    kml_bytes: bytes | None
    pdf_bytes: bytes | None
    manifest: dict[str, Any]


def _format_inr(amount: float) -> str:
    """Format amount in Indian Rupees with commas."""
    return f"₹{amount:,.0f}"


def _format_inr_lakhs(amount: float) -> str:
    """Format amount in Lakhs."""
    return f"₹{amount / 100000:.2f} Lakhs"


def _format_inr_crores(amount: float) -> str:
    """Format amount in Crores."""
    return f"₹{amount / 10000000:.2f} Crores"


# ── DOCX Generation ────────────────────────────────────────────────


def _add_heading(doc: Document, text: str, level: int = 1) -> None:
    """Add a styled heading."""
    heading = doc.add_heading(text, level=level)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0, 51, 102)
    return heading


def _add_table_with_style(
    doc: Document, headers: list[str], rows: list[list[str]]
) -> None:
    """Add a formatted table."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    hdr_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        for paragraph in hdr_cells[i].paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(10)

    # Data rows
    for row_idx, row_data in enumerate(rows):
        row_cells = table.rows[row_idx + 1].cells
        for col_idx, cell_text in enumerate(row_data):
            row_cells[col_idx].text = str(cell_text)
            for paragraph in row_cells[col_idx].paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.size = Pt(10)

    # Set column widths
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            cell.width = Inches(1.5)

    doc.add_paragraph()  # spacing


def _generate_dpr_docx(sites: list[Site], project_name: str, project_id: str) -> bytes:
    """Generate the main DPR document in .docx format."""
    doc = Document()

    # Styles
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)

    # ── COVER PAGE ──────────────────────────────────────────────
    for _ in range(4):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("DETAILED PROJECT REPORT")
    run.bold = True
    run.font.size = Pt(24)
    run.font.color.rgb = RGBColor(0, 51, 102)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run(project_name)
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(0, 51, 102)

    doc.add_paragraph()

    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = info.add_run(f"Project ID: {project_id}\n")
    run.font.size = Pt(12)
    run = info.add_run(
        f"Generated: {datetime.now(timezone.utc).strftime('%d %B %Y')}\n"
    )
    run.font.size = Pt(12)
    run = info.add_run("Bhujal Decision Support System\n")
    run.font.size = Pt(12)
    run.italic = True
    run = info.add_run("Amazon Environmental Hacks 2026")
    run.font.size = Pt(12)

    doc.add_page_break()

    # ── TABLE OF CONTENTS (placeholder) ─────────────────────────
    _add_heading(doc, "Table of Contents", level=1)
    toc_items = [
        "1. Executive Summary",
        "2. Project Background and Rationale",
        "3. Site Details and Hydro-Climatic Profile",
        "4. Safety and Geotechnical Assessment",
        "5. Proposed Interventions and Technical Specifications",
        "6. Cost Estimates and Financial Analysis",
        "7. Implementation Arrangements",
        "8. Monitoring and Evaluation Framework",
        "9. Scheme Convergence and Funding Plan",
        "Annexure I: Site-wise Hydro-Climatic Scores",
        "Annexure II: Safety Veto Details",
        "Annexure III: Intervention Design Parameters",
        "Annexure IV: Abstract of Cost Estimates",
        "Annexure V: Scheme-wise Funding Breakup",
        "Annexure VI: Implementation Timeline",
        "Annexure VII: Coordinates and KML Reference",
    ]
    for item in toc_items:
        p = doc.add_paragraph(item)
        p.paragraph_format.space_after = Pt(4)

    doc.add_page_break()

    # ── 1. EXECUTIVE SUMMARY ────────────────────────────────────
    _add_heading(doc, "1. Executive Summary", level=1)
    total_cost = sum(
        sum(r.cost_range_inr.get("high", 0) for r in s.recommendations) for s in sites
    )
    total_labour = sum(sum(r.labour_days for r in s.recommendations) for s in sites)
    approved_sites = [s for s in sites if s.safety.status != SafetyStatus.REJECTED]
    vetoed_sites = [s for s in sites if s.safety.status == SafetyStatus.REJECTED]

    exec_text = (
        f"This Detailed Project Report (DPR) presents the hydro-climatic assessment, "
        f"safety evaluation, and engineering interventions for {len(sites)} settlement(s) "
        f"across priority watersheds. The analysis follows the Bhujal decision-support framework, "
        f"integrating deterministic multi-criteria scoring (recharge suitability, heat-water stress, "
        f"spring drying risk) with geotechnical safety vetoes and MGNREGA-calibrated costing."
    )
    doc.add_paragraph(exec_text)

    exec_text2 = (
        f"Of the {len(sites)} sites evaluated, {len(approved_sites)} are cleared for civil "
        f"interventions while {len(vetoed_sites)} have been issued safety vetoes. "
        f"The total indicative capital outlay for approved interventions is {_format_inr(total_cost)} "
        f"({_format_inr_lakhs(total_cost)}), generating approximately {total_labour:,} "
        f"MGNREGA person-days of employment."
    )
    doc.add_paragraph(exec_text2)

    # Summary table
    summary_rows = []
    for s in sites:
        status = s.safety.status.value if s.safety else "SAFE"
        cost = sum(r.cost_range_inr.get("high", 0) for r in s.recommendations)
        labour = sum(r.labour_days for r in s.recommendations)
        summary_rows.append(
            [
                s.village.name,
                s.village.district,
                s.village.state,
                status,
                _format_inr(cost),
                str(labour),
            ]
        )
    _add_table_with_style(
        doc,
        ["Village", "District", "State", "Safety", "Est. Cost", "Labour Days"],
        summary_rows,
    )

    doc.add_page_break()

    # ── 2. PROJECT BACKGROUND ───────────────────────────────────
    _add_heading(doc, "2. Project Background and Rationale", level=1)
    doc.add_paragraph(
        "Mountainous and plateau tribal watersheds across central and eastern India—specifically "
        "in Odisha, Madhya Pradesh, and Jharkhand—suffer from severe hydro-climatic paradoxes. "
        "Despite receiving moderate to heavy annual monsoon precipitation (1,100 mm to 1,600 mm), "
        "steep topographic gradients, low secondary porosity in hard-rock granitic, basaltic, and "
        "gneissic basements, and rapid surface runoff velocity result in accelerated drainage. "
        "Consequently, over 50% of the rural and indigenous population faces acute pre-monsoon "
        "drinking water insecurity, perched spring drying, and compounded summer heat distress "
        "(MODIS LST >40°C)."
    )
    doc.add_paragraph(
        "Traditional watershed development programs frequently suffer from two critical limitations: "
        "(1) Locational Blindness—interventions placed without quantitative verification of slope "
        "stability, stream order constraints, fracture permeability, or downstream flood hazards; "
        "(2) False Precision—planning software routinely conceals data sparsity or claims black-box "
        '"AI" infallibility without communicating hydrogeological confidence intervals. '
        "This DPR addresses these gaps through transparent deterministic scoring, explicit safety vetoes, "
        "and scheme-linked costing."
    )

    # ── 3. SITE DETAILS ────────────────────────────────────────
    _add_heading(doc, "3. Site Details and Hydro-Climatic Profile", level=1)
    for s in sites:
        _add_heading(doc, f"3.1 {s.village.name} ({s.village.id})", level=2)
        details = [
            ["Parameter", "Value"],
            ["Village", s.village.name],
            ["Block", s.village.block],
            ["District", s.village.district],
            ["State", s.village.state],
            ["Coordinates", f"{s.village.lat:.4f}°N, {s.village.lon:.4f}°E"],
            [
                "Elevation",
                f"{s.village.elevation_m:.0f} m AMSL"
                if s.village.elevation_m
                else "N/A",
            ],
            [
                "Population",
                f"{s.village.population:,}" if s.village.population else "N/A",
            ],
            ["Spring Present", "Yes" if s.village.has_spring else "No"],
            ["Data Quality", s.village.data_tag.value.title()],
        ]
        _add_table_with_style(doc, ["Parameter", "Value"], details[1:])

        # Scores table
        _add_heading(doc, "Hydro-Climatic Scores", level=3)
        score_rows = []
        for score in s.scores:
            score_rows.append(
                [
                    score.score_type.replace("_", " ").title(),
                    f"{score.value:.1f}/100",
                    score.score_class.value.title(),
                    f"{score.confidence.numeric:.0%}",
                    score.data_tag.value.title(),
                ]
            )
        _add_table_with_style(
            doc,
            ["Score Type", "Value", "Classification", "Confidence", "Data Tag"],
            score_rows,
        )

    doc.add_page_break()

    # ── 4. SAFETY ASSESSMENT ───────────────────────────────────
    _add_heading(doc, "4. Safety and Geotechnical Assessment", level=1)
    for s in sites:
        if s.safety:
            _add_heading(
                doc, f"4.1 {s.village.name} — {s.safety.status.value}", level=2
            )
            if s.safety.rule_ids:
                p = doc.add_paragraph("Triggered Safety Rules:")
                p.runs[0].bold = True
                for rule_id in s.safety.rule_ids:
                    reason = next(
                        (r for r in s.safety.reasons if rule_id in r), rule_id
                    )
                    doc.add_paragraph(f"• {rule_id}: {reason}", style="List Bullet")
            else:
                doc.add_paragraph(
                    "All safety checks passed. Site cleared for civil works."
                )

            # Rules evaluated table
            if s.safety.rules_evaluated:
                rule_rows = []
                for r in s.safety.rules_evaluated:
                    rule_rows.append(
                        [
                            r.rule_id,
                            "Yes" if r.triggered else "No",
                            r.verdict.value,
                            r.reason or "—",
                        ]
                    )
                _add_table_with_style(
                    doc, ["Rule ID", "Triggered", "Verdict", "Reason"], rule_rows
                )

    doc.add_page_break()

    # ── 5. PROPOSED INTERVENTIONS ──────────────────────────────
    _add_heading(doc, "5. Proposed Interventions and Technical Specifications", level=1)
    for s in sites:
        if s.safety and s.safety.status == SafetyStatus.REJECTED:
            continue
        _add_heading(doc, f"5.1 {s.village.name}", level=2)
        if not s.recommendations:
            doc.add_paragraph(
                "No structural interventions matched site criteria. Bio-engineering recommended."
            )
            continue

        for i, rec in enumerate(s.recommendations, 1):
            _add_heading(
                doc,
                f"5.1.{i} {rec.intervention_name} (Suitability: {rec.suitability_score:.0%})",
                level=3,
            )

            # Dimensions
            dim_rows = [["Parameter", "Value"]]
            for k, v in rec.dimensions.items():
                dim_rows.append([k.replace("_", " ").title(), str(v)])
            _add_table_with_style(doc, ["Parameter", "Value"], dim_rows[1:])

            # Materials
            p = doc.add_paragraph("Materials:")
            p.runs[0].bold = True
            for mat in rec.materials:
                doc.add_paragraph(mat, style="List Bullet")

            # Cost & Labour
            cost_low = rec.cost_range_inr.get("low", 0)
            cost_high = rec.cost_range_inr.get("high", 0)
            doc.add_paragraph(
                f"Indicative Cost Range: {_format_inr(cost_low)} – {_format_inr(cost_high)}"
            )
            doc.add_paragraph(f"MGNREGA Labour: {rec.labour_days} person-days")

            # Assumptions
            p = doc.add_paragraph("Design Assumptions:")
            p.runs[0].bold = True
            for a in rec.assumptions:
                doc.add_paragraph(a, style="List Bullet")

            # Scheme mapping
            scheme_info = SCHEME_MAPPING.get(rec.intervention_id, {})
            p = doc.add_paragraph("Scheme Convergence:")
            p.runs[0].bold = True
            doc.add_paragraph(
                f"Primary Scheme: {scheme_info.get('primary_scheme', 'MGNREGA')}"
            )
            doc.add_paragraph(
                f"Eligible Schemes: {', '.join(scheme_info.get('eligible_schemes', ['MGNREGA']))}"
            )
            doc.add_paragraph(
                f"Funding Pattern: {scheme_info.get('funding_pattern', 'Central:State = 60:40')}"
            )
            doc.add_paragraph(
                f"Technical Sanction: {scheme_info.get('technical_sanction_authority', 'EE, WRD')}"
            )
            doc.add_paragraph(
                f"Admin Approval: {scheme_info.get('admin_approval_authority', 'District Collector')}"
            )

    doc.add_page_break()

    # ── 6. COST ESTIMATES ──────────────────────────────────────
    _add_heading(doc, "6. Cost Estimates and Financial Analysis", level=1)

    # Abstract of Cost
    _add_heading(doc, "6.1 Abstract of Cost Estimates", level=2)
    cost_rows = [
        [
            "Village",
            "Intervention",
            "Low (INR)",
            "High (INR)",
            "Labour Days",
            "Primary Scheme",
        ]
    ]
    for s in sites:
        if s.safety and s.safety.status == SafetyStatus.REJECTED:
            cost_rows.append([s.village.name, "SAFETY VETO", "—", "—", "—", "—"])
            continue
        for r in s.recommendations:
            scheme_info = SCHEME_MAPPING.get(r.intervention_id, {})
            cost_rows.append(
                [
                    s.village.name,
                    r.intervention_name,
                    _format_inr(r.cost_range_inr.get("low", 0)),
                    _format_inr(r.cost_range_inr.get("high", 0)),
                    str(r.labour_days),
                    scheme_info.get("primary_scheme", "MGNREGA"),
                ]
            )

    _add_table_with_style(doc, cost_rows[0], cost_rows[1:])

    # Totals
    total_low = sum(
        r.cost_range_inr.get("low", 0) for s in sites for r in s.recommendations
    )
    total_high = sum(
        r.cost_range_inr.get("high", 0) for s in sites for r in s.recommendations
    )
    doc.add_paragraph(
        f"Total Indicative Cost Range: {_format_inr(total_low)} – {_format_inr(total_high)}"
    )
    doc.add_paragraph(f"Contingency (10%): {_format_inr(total_high * 0.10)}")
    doc.add_paragraph(f"Supervision (5%): {_format_inr(total_high * 0.05)}")
    doc.add_paragraph(
        f"Grand Total (with contingencies): {_format_inr(total_high * 1.15)}"
    )

    # ── 7. IMPLEMENTATION ARRANGEMENTS ─────────────────────────
    _add_heading(doc, "7. Implementation Arrangements", level=1)
    doc.add_paragraph("Institutional Framework:")
    impl_items = [
        "District Collector — Administrative Head & Final Approving Authority",
        "District Watershed Committee — Technical Sanction & Monitoring",
        "Executive Engineer, WRD/PHED — Technical Design & Estimate Preparation",
        "Block Development Officer — MGNREGA Convergence & Labour Deployment",
        "Gram Panchayat — Implementation Agency (MGNREGA works)",
        "Village Water & Sanitation Committee (VWSC) — O&M Responsibility",
    ]
    for item in impl_items:
        doc.add_paragraph(item, style="List Bullet")

    # ── 8. M&E FRAMEWORK ────────────────────────────────────────
    _add_heading(doc, "8. Monitoring and Evaluation Framework", level=1)
    me_items = [
        "Baseline: Pre-monsoon groundwater levels, spring discharge, LST/NDVI",
        "Process: Monthly progress reports, labour attendance, material quality checks",
        "Output: Structures completed, person-days generated, water storage capacity created",
        "Outcome: Post-monsoon groundwater rise, spring flow revival, heat stress reduction",
        "Impact: Drinking water security (JJM indicators), irrigation coverage, climate resilience",
        "Community Monitoring: Jal Mitra observations via Bhujal participatory module",
    ]
    for item in me_items:
        doc.add_paragraph(item, style="List Bullet")

    # ── 9. SCHEME CONVERGENCE ──────────────────────────────────
    _add_heading(doc, "9. Scheme Convergence and Funding Plan", level=1)
    scheme_summary: dict[str, float] = {}
    for s in sites:
        for r in s.recommendations:
            scheme_info = SCHEME_MAPPING.get(r.intervention_id, {})
            primary = scheme_info.get("primary_scheme", "MGNREGA")
            cost = r.cost_range_inr.get("high", 0)
            scheme_summary[primary] = scheme_summary.get(primary, 0) + cost

    scheme_rows = [["Scheme", "Estimated Allocation (INR)", "Share"]]
    for scheme, amount in scheme_summary.items():
        scheme_rows.append(
            [scheme, _format_inr(amount), f"{amount / total_high * 100:.1f}%"]
        )
    _add_table_with_style(doc, scheme_rows[0], scheme_rows[1:])

    # State-specific nuances
    for s in sites:
        state_nuances = STATE_SCHEME_NUANCES.get(s.village.state, {})
        if state_nuances:
            p = doc.add_paragraph(f"{s.village.state} Scheme Nuances:")
            p.runs[0].bold = True
            for scheme, detail in state_nuances.items():
                doc.add_paragraph(f"{scheme}: {detail}", style="List Bullet")

    doc.add_page_break()

    # ── ANNEXURES ──────────────────────────────────────────────
    _add_heading(doc, "Annexure I: Site-wise Hydro-Climatic Scores", level=1)
    for s in sites:
        _add_heading(doc, f"{s.village.name} ({s.village.id})", level=3)
        annex_rows = [["Score", "Value", "Class", "Confidence", "Data Tag"]]
        for score in s.scores:
            annex_rows.append(
                [
                    score.score_type.replace("_", " ").title(),
                    f"{score.value:.1f}",
                    score.score_class.value.title(),
                    f"{score.confidence.numeric:.0%}",
                    score.data_tag.value.title(),
                ]
            )
        _add_table_with_style(doc, annex_rows[0], annex_rows[1:])

    _add_heading(doc, "Annexure II: Safety Veto Details", level=1)
    for s in sites:
        if s.safety:
            _add_heading(doc, f"{s.village.name}", level=3)
            if s.safety.rules_evaluated:
                rule_rows = [["Rule ID", "Triggered", "Verdict", "Reason"]]
                for r in s.safety.rules_evaluated:
                    rule_rows.append(
                        [
                            r.rule_id,
                            "Yes" if r.triggered else "No",
                            r.verdict.value,
                            r.reason or "—",
                        ]
                    )
                _add_table_with_style(doc, rule_rows[0], rule_rows[1:])

    _add_heading(doc, "Annexure III: Intervention Design Parameters", level=1)
    for s in sites:
        if s.recommendations:
            _add_heading(doc, f"{s.village.name}", level=3)
            for r in s.recommendations:
                p = doc.add_paragraph(f"{r.intervention_name}")
                p.runs[0].bold = True
                for k, v in r.dimensions.items():
                    doc.add_paragraph(
                        f"{k.replace('_', ' ').title()}: {v}", style="List Bullet"
                    )

    _add_heading(doc, "Annexure IV: Abstract of Cost Estimates", level=1)
    _add_heading(doc, "See Section 6.1", level=2)

    _add_heading(doc, "Annexure V: Scheme-wise Funding Breakup", level=1)
    _add_heading(doc, "See Section 9", level=2)

    _add_heading(doc, "Annexure VI: Implementation Timeline", level=1)
    timeline_rows = [["Period", "Activity", "Responsible Agency", "Milestone"]]
    timeline_data = [
        ["Month 1-2", "DPR Technical Sanction", "EE, WRD/PHED", "TS Approved"],
        [
            "Month 2-3",
            "Administrative Approval & Tender",
            "District Collector / BDO",
            "AA & Work Order",
        ],
        [
            "Month 3-6",
            "Construction (MGNREGA)",
            "Gram Panchayat / BDO",
            "Structures Completed",
        ],
        ["Month 6-7", "Quality Check & Measurement Book", "AE/JE, WRD", "MB Closed"],
        [
            "Month 7-8",
            "Wage Payment & Asset Handover",
            "BDO / VWSC",
            "Assets Functional",
        ],
        ["Post-Monsoon", "Impact Assessment", "Bhujal + VWSC", "Report Submitted"],
    ]
    _add_table_with_style(doc, timeline_rows[0], timeline_data)

    _add_heading(doc, "Annexure VII: Coordinates and KML Reference", level=1)
    coord_rows = [["Village", "Latitude", "Longitude", "Elevation (m)"]]
    for s in sites:
        coord_rows.append(
            [
                s.village.name,
                f"{s.village.lat:.6f}",
                f"{s.village.lon:.6f}",
                f"{s.village.elevation_m:.1f}" if s.village.elevation_m else "N/A",
            ]
        )
    _add_table_with_style(doc, coord_rows[0], coord_rows[1:])

    # Save to bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# ── XLSX Generation ────────────────────────────────────────────────


def _generate_dpr_xlsx(sites: list[Site]) -> bytes:
    """Generate cost abstracts and financial tables in .xlsx format."""
    wb = Workbook()

    # Styles
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(
        start_color="003366", end_color="003366", fill_type="solid"
    )
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    money_format = "#,##0"

    def style_header(ws, row, max_col):
        for col in range(1, max_col + 1):
            cell = ws.cell(row=row, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

    def style_data(ws, start_row, end_row, max_col):
        for r in range(start_row, end_row + 1):
            for c in range(1, max_col + 1):
                cell = ws.cell(row=r, column=c)
                cell.border = thin_border
                cell.alignment = Alignment(
                    horizontal="center", vertical="center", wrap_text=True
                )

    # ── Sheet 1: Cost Abstract ─────────────────────────────────
    ws1 = wb.active
    ws1.title = "Cost Abstract"

    headers = [
        "Village",
        "District",
        "State",
        "Intervention",
        "Category",
        "Low Cost (INR)",
        "High Cost (INR)",
        "Labour Days",
        "Primary Scheme",
    ]
    for col, h in enumerate(headers, 1):
        ws1.cell(row=1, column=col, value=h)
    style_header(ws1, 1, len(headers))

    row = 2
    for s in sites:
        if s.safety and s.safety.status == SafetyStatus.REJECTED:
            ws1.cell(row=row, column=1, value=s.village.name)
            ws1.cell(row=row, column=2, value=s.village.district)
            ws1.cell(row=row, column=3, value=s.village.state)
            ws1.cell(row=row, column=4, value="SAFETY VETO")
            for c in range(5, len(headers) + 1):
                ws1.cell(row=row, column=c, value="—")
            row += 1
            continue

        for r in s.recommendations:
            scheme_info = SCHEME_MAPPING.get(r.intervention_id, {})
            ws1.cell(row=row, column=1, value=s.village.name)
            ws1.cell(row=row, column=2, value=s.village.district)
            ws1.cell(row=row, column=3, value=s.village.state)
            ws1.cell(row=row, column=4, value=r.intervention_name)
            ws1.cell(row=row, column=5, value=r.category)
            ws1.cell(row=row, column=6, value=r.cost_range_inr.get("low", 0))
            ws1.cell(row=row, column=7, value=r.cost_range_inr.get("high", 0))
            ws1.cell(row=row, column=8, value=r.labour_days)
            ws1.cell(
                row=row, column=9, value=scheme_info.get("primary_scheme", "MGNREGA")
            )
            row += 1

    # Totals
    total_low = sum(
        r.cost_range_inr.get("low", 0) for s in sites for r in s.recommendations
    )
    total_high = sum(
        r.cost_range_inr.get("high", 0) for s in sites for r in s.recommendations
    )
    total_labour = sum(r.labour_days for s in sites for r in s.recommendations)

    ws1.cell(row=row, column=1, value="TOTAL")
    ws1.cell(row=row, column=6, value=total_low)
    ws1.cell(row=row, column=7, value=total_high)
    ws1.cell(row=row, column=8, value=total_labour)
    for c in range(1, len(headers) + 1):
        ws1.cell(row=row, column=c).font = Font(bold=True)
    row += 1

    ws1.cell(row=row, column=1, value="Contingency (10%)")
    ws1.cell(row=row, column=7, value=round(total_high * 0.10))
    row += 1
    ws1.cell(row=row, column=1, value="Supervision (5%)")
    ws1.cell(row=row, column=7, value=round(total_high * 0.05))
    row += 1
    ws1.cell(row=row, column=1, value="GRAND TOTAL")
    ws1.cell(row=row, column=7, value=round(total_high * 1.15))
    for c in range(1, len(headers) + 1):
        ws1.cell(row=row, column=c).font = Font(bold=True)

    style_data(ws1, 2, row, len(headers))

    # Format currency columns
    for r in range(2, row + 1):
        for c in [6, 7]:
            ws1.cell(row=r, column=c).number_format = money_format

    # Auto-width
    for col in range(1, len(headers) + 1):
        ws1.column_dimensions[get_column_letter(col)].width = 18

    # ── Sheet 2: Scheme-wise Funding ───────────────────────────
    ws2 = wb.create_sheet("Scheme Funding")
    scheme_headers = [
        "Scheme",
        "Total Allocation (INR)",
        "Share (%)",
        "Funding Pattern",
        "Technical Sanction",
        "Admin Approval",
    ]
    for col, h in enumerate(scheme_headers, 1):
        ws2.cell(row=1, column=col, value=h)
    style_header(ws2, 1, len(scheme_headers))

    scheme_summary: dict[str, float] = {}
    for s in sites:
        for r in s.recommendations:
            scheme_info = SCHEME_MAPPING.get(r.intervention_id, {})
            primary = scheme_info.get("primary_scheme", "MGNREGA")
            cost = r.cost_range_inr.get("high", 0)
            scheme_summary[primary] = scheme_summary.get(primary, 0) + cost

    row = 2
    for scheme, amount in scheme_summary.items():
        scheme_info = SCHEME_MAPPING.get(
            next(
                (
                    r.intervention_id
                    for s in sites
                    for r in s.recommendations
                    if SCHEME_MAPPING.get(r.intervention_id, {}).get("primary_scheme")
                    == scheme
                ),
                "",
            ),
            {},
        )
        ws2.cell(row=row, column=1, value=scheme)
        ws2.cell(row=row, column=2, value=amount)
        ws2.cell(
            row=row,
            column=3,
            value=round(amount / total_high * 100, 1) if total_high else 0,
        )
        ws2.cell(
            row=row,
            column=4,
            value=scheme_info.get("funding_pattern", "Central:State = 60:40"),
        )
        ws2.cell(
            row=row,
            column=5,
            value=scheme_info.get("technical_sanction_authority", "EE, WRD"),
        )
        ws2.cell(
            row=row,
            column=6,
            value=scheme_info.get("admin_approval_authority", "District Collector"),
        )
        ws2.cell(row=row, column=2).number_format = money_format
        row += 1

    ws2.cell(row=row, column=1, value="TOTAL")
    ws2.cell(row=row, column=2, value=total_high)
    ws2.cell(row=row, column=2).number_format = money_format
    for c in range(1, len(scheme_headers) + 1):
        ws2.cell(row=row, column=c).font = Font(bold=True)

    style_data(ws2, 2, row, len(scheme_headers))
    for col in range(1, len(scheme_headers) + 1):
        ws2.column_dimensions[get_column_letter(col)].width = 22

    # ── Sheet 3: Site Scores ───────────────────────────────────
    ws3 = wb.create_sheet("Site Scores")
    score_headers = [
        "Village",
        "District",
        "State",
        "Recharge Score",
        "Recharge Class",
        "Heat-Water Stress",
        "Stress Class",
        "Spring Drying Risk",
        "Spring Class",
        "Safety Status",
        "Data Tag",
    ]
    for col, h in enumerate(score_headers, 1):
        ws3.cell(row=1, column=col, value=h)
    style_header(ws3, 1, len(score_headers))

    row = 2
    for s in sites:
        scores = {sc.score_type: sc for sc in s.scores}
        ws3.cell(row=row, column=1, value=s.village.name)
        ws3.cell(row=row, column=2, value=s.village.district)
        ws3.cell(row=row, column=3, value=s.village.state)
        recharge = scores.get("recharge_score")
        stress = scores.get("heat_water_stress")
        spring = scores.get("spring_drying_index")
        ws3.cell(row=row, column=4, value=recharge.value if recharge else 0)
        ws3.cell(
            row=row,
            column=5,
            value=recharge.score_class.value if recharge else ScoreClass.POOR.value,
        )
        ws3.cell(row=row, column=6, value=stress.value if stress else 0)
        ws3.cell(
            row=row,
            column=7,
            value=stress.score_class.value if stress else ScoreClass.LOW.value,
        )
        ws3.cell(row=row, column=8, value=spring.value if spring else 0)
        ws3.cell(
            row=row,
            column=9,
            value=spring.score_class.value if spring else ScoreClass.LOW.value,
        )
        ws3.cell(
            row=row, column=10, value=s.safety.status.value if s.safety else "SAFE"
        )
        ws3.cell(row=row, column=11, value=s.village.data_tag.value)
        row += 1

    style_data(ws3, 2, row - 1, len(score_headers))
    for col in range(1, len(score_headers) + 1):
        ws3.column_dimensions[get_column_letter(col)].width = 18

    # ── Sheet 4: Coordinates for KML/GIS ───────────────────────
    ws4 = wb.create_sheet("Coordinates")
    coord_headers = [
        "Village",
        "Latitude",
        "Longitude",
        "Elevation (m)",
        "State",
        "District",
        "Block",
    ]
    for col, h in enumerate(coord_headers, 1):
        ws4.cell(row=1, column=col, value=h)
    style_header(ws4, 1, len(coord_headers))

    row = 2
    for s in sites:
        ws4.cell(row=row, column=1, value=s.village.name)
        ws4.cell(row=row, column=2, value=s.village.lat)
        ws4.cell(row=row, column=3, value=s.village.lon)
        ws4.cell(row=row, column=4, value=s.village.elevation_m or 0)
        ws4.cell(row=row, column=5, value=s.village.state)
        ws4.cell(row=row, column=6, value=s.village.district)
        ws4.cell(row=row, column=7, value=s.village.block)
        row += 1

    style_data(ws4, 2, row - 1, len(coord_headers))
    for col in range(1, len(coord_headers) + 1):
        ws4.column_dimensions[get_column_letter(col)].width = 15

    # Save to bytes
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# ── KML Generation ────────────────────────────────────────────────


def _generate_dpr_kml(sites: list[Site]) -> bytes:
    """Generate KML file with site locations and intervention footprints."""
    kml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        "  <Document>",
        "    <name>Bhujal DPR Site Locations</name>",
        "    <description>Generated by Bhujal Decision Support System</description>",
    ]

    # Styles
    kml_parts.append('    <Style id="safe_site">')
    kml_parts.append(
        "      <IconStyle><color>ff00ff00</color><scale>1.2</scale></IconStyle>"
    )
    kml_parts.append("    </Style>")
    kml_parts.append('    <Style id="vetoed_site">')
    kml_parts.append(
        "      <IconStyle><color>ffff0000</color><scale>1.2</scale></IconStyle>"
    )
    kml_parts.append("    </Style>")
    kml_parts.append('    <Style id="intervention">')
    kml_parts.append(
        "      <LineStyle><color>ff0000ff</color><width>3</width></LineStyle>"
    )
    kml_parts.append("    </Style>")

    for s in sites:
        status = s.safety.status.value if s.safety else "SAFE"
        style_ref = "safe_site" if status == "SAFE" else "vetoed_site"

        kml_parts.append("    <Placemark>")
        kml_parts.append(f"      <name>{s.village.name} ({s.village.id})</name>")
        kml_parts.append("      <description><![CDATA[")
        kml_parts.append(f"        <b>Village:</b> {s.village.name}<br/>")
        kml_parts.append(f"        <b>Block:</b> {s.village.block}<br/>")
        kml_parts.append(f"        <b>District:</b> {s.village.district}<br/>")
        kml_parts.append(f"        <b>State:</b> {s.village.state}<br/>")
        kml_parts.append(
            f"        <b>Elevation:</b> {s.village.elevation_m:.0f} m<br/>"
            if s.village.elevation_m
            else ""
        )
        kml_parts.append(
            f"        <b>Population:</b> {s.village.population:,}<br/>"
            if s.village.population
            else ""
        )
        kml_parts.append(
            f"        <b>Spring:</b> {'Yes' if s.village.has_spring else 'No'}<br/>"
        )
        kml_parts.append(f"        <b>Safety Status:</b> {status}<br/>")
        if s.recommendations:
            kml_parts.append("        <b>Recommended Interventions:</b><br/>")
            for r in s.recommendations:
                kml_parts.append(
                    f"        - {r.intervention_name} ({_format_inr(r.cost_range_inr.get('high', 0))})<br/>"
                )
        kml_parts.append("      ]]></description>")
        kml_parts.append(f"      <styleUrl>#{style_ref}</styleUrl>")
        kml_parts.append("      <Point>")
        kml_parts.append(
            f"        <coordinates>{s.village.lon:.6f},{s.village.lat:.6f},{s.village.elevation_m or 0}</coordinates>"
        )
        kml_parts.append("      </Point>")
        kml_parts.append("    </Placemark>")

    kml_parts.append("  </Document>")
    kml_parts.append("</kml>")

    return "\n".join(kml_parts).encode("utf-8")


# ── PDF Generation ────────────────────────────────────────────────


def _generate_dpr_pdf(docx_bytes: bytes) -> bytes | None:
    """Convert DOCX to PDF using weasyprint (requires HTML conversion)."""
    if not WEASYPRINT_AVAILABLE:
        return None
    # Note: Full DOCX→PDF conversion is complex. This is a placeholder.
    # In production, use LibreOffice headless or a dedicated conversion service.
    return None


# ── Main DPR Package Generator ────────────────────────────────────


def generate_dpr_package(
    site_ids: list[str],
    project_name: str | None = None,
    include_pdf: bool = False,
) -> DPRPackage:
    """
    Generate complete DPR package for given site IDs.

    Returns DPRPackage with docx, xlsx, kml, and optional pdf bytes.
    """
    sites = [evaluate_site(sid) for sid in site_ids]
    sites = [s for s in sites if s is not None]

    if not sites:
        raise ValueError("No valid sites found")

    project_id = (
        f"DPR_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{len(sites)}sites"
    )
    if project_name is None:
        project_name = (
            f"Bhujal Watershed DPR — {', '.join(s.village.name for s in sites[:3])}"
        )
        if len(sites) > 3:
            project_name += f" +{len(sites) - 3} more"

    # Generate all formats
    docx_bytes = _generate_dpr_docx(sites, project_name, project_id)
    xlsx_bytes = _generate_dpr_xlsx(sites)
    kml_bytes = _generate_dpr_kml(sites)
    pdf_bytes = (
        _generate_dpr_pdf(docx_bytes) if include_pdf and WEASYPRINT_AVAILABLE else None
    )

    # Manifest
    manifest = {
        "project_id": project_id,
        "project_name": project_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sites": [s.village.id for s in sites],
        "site_count": len(sites),
        "total_cost_high_inr": sum(
            r.cost_range_inr.get("high", 0) for s in sites for r in s.recommendations
        ),
        "total_labour_days": sum(
            r.labour_days for s in sites for r in s.recommendations
        ),
        "files": {
            "docx": f"{project_id}.docx",
            "xlsx": f"{project_id}.xlsx",
            "kml": f"{project_id}.kml",
            "pdf": f"{project_id}.pdf" if pdf_bytes else None,
        },
        "generator": "Bhujal DPR Generator v0.2.0",
    }

    return DPRPackage(
        project_id=project_id,
        project_name=project_name,
        sites=sites,
        generated_at=datetime.now(timezone.utc),
        docx_bytes=docx_bytes,
        xlsx_bytes=xlsx_bytes,
        kml_bytes=kml_bytes,
        pdf_bytes=pdf_bytes,
        manifest=manifest,
    )


def create_dpr_zip(dpr_package: DPRPackage) -> bytes:
    """Create a ZIP archive containing all DPR files."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{dpr_package.project_id}.docx", dpr_package.docx_bytes)
        zf.writestr(f"{dpr_package.project_id}.xlsx", dpr_package.xlsx_bytes)
        if dpr_package.kml_bytes:
            zf.writestr(f"{dpr_package.project_id}.kml", dpr_package.kml_bytes)
        if dpr_package.pdf_bytes:
            zf.writestr(f"{dpr_package.project_id}.pdf", dpr_package.pdf_bytes)
        # Add manifest as JSON
        zf.writestr(
            f"{dpr_package.project_id}_manifest.json",
            json.dumps(dpr_package.manifest, indent=2),
        )
    return buffer.getvalue()
