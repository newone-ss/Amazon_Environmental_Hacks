"""
Bhujal — Civil Engineering & Costing Specialist Agent
======================================================
Specialized agent evaluating intervention suitability, dimensions,
bill-of-quantities materials, and MGNREGA-calibrated cost projections.
"""

from __future__ import annotations

from typing import Any

from agent.base import AgentResponse, BaseAgent
from backend.models import Recommendation


class InterventionComposerAgent(BaseAgent):
    """Specialist composing civil engineering structures and cost estimates."""

    def __init__(self) -> None:
        super().__init__(
            name="InterventionComposerAgent",
            role="Civil Engineering & Costing Specialist",
            system_prompt=(
                "You are an experienced watershed civil engineer and quantity surveyor specializing "
                "in rural infrastructure in India. You analyze matched civil structures (check dams, "
                "percolation tanks, contour trenches, farm ponds), bill of quantities materials, "
                "labour allocations under MGNREGA, and indicative cost ranges to formulate "
                "rigorous, execution-ready engineering briefs."
            ),
        )

    def fallback_execute(self, context: dict[str, Any]) -> AgentResponse:
        recs: list[Recommendation] = context.get("recommendations", [])  # type: ignore
        village_name = context.get("village_name", "Target Site")
        is_rejected = context.get("is_rejected", False)

        if is_rejected or not recs:
            return AgentResponse(
                agent_name=self.name,
                role=self.role,
                summary=f"No civil engineering structures recommended for {village_name} due to geotechnical veto or physical constraints.",
                details={"recommendations_count": 0},
                narrative=(
                    f"Civil Engineering Assessment for {village_name}:\n"
                    "Zero civil structures are cleared for deployment. Construction at this site is vetoed "
                    "by geotechnical safety rules or incompatible geomorphology. Planners must not commit "
                    "public watershed funds for structural interventions here."
                ),
                recommendations=[
                    "Explore alternative catchments or non-structural bio-engineering."
                ],
                mode="deterministic_fallback",
            )

        top_rec = recs[0]
        cost_low = top_rec.cost_range_inr.get("low", 0)
        cost_high = top_rec.cost_range_inr.get("high", 0)

        summary = (
            f"Recommended primary intervention for {village_name} is '{top_rec.intervention_name}' "
            f"(suitability score: {top_rec.suitability_score:.2f}) with indicative cost range "
            f"INR {cost_low:,.0f} - {cost_high:,.0f}."
        )

        all_names = [f"{r.intervention_name} ({r.suitability_score:.2f})" for r in recs]
        dims_str = (
            ", ".join(f"{k}: {v}m" for k, v in top_rec.dimensions.items())
            if top_rec.dimensions
            else "Standard"
        )

        narrative = (
            f"Civil Engineering Plan for {village_name}:\n"
            f"- Primary Recommendation: {top_rec.intervention_name} (Category: {top_rec.category.title()})\n"
            f"- Engineering Sizing: {dims_str}\n"
            f"- Materials Specification: {', '.join(top_rec.materials)}\n"
            f"- Labour Allocation: {top_rec.labour_days} person-days under MGNREGA\n"
            f"- Indicative Financial Outlay: INR {cost_low:,.0f} to INR {cost_high:,.0f}\n"
            f"- Alternative Matched Interventions: {', '.join(all_names)}\n"
            f"- Engineering Justification: Matched to local slope, low stream order, and soil infiltration capacity."
        )

        recommendations_list = [
            f"Initiate detailed site survey for {top_rec.intervention_name} (Estimated: INR {cost_low:,.0f} - {cost_high:,.0f}).",
            f"Allocate {top_rec.labour_days} person-days in the upcoming Annual Gram Panchayat MGNREGA shelf of works.",
            "Procure local stone masonry and gabion materials within 15 km haulage radius.",
        ]

        return AgentResponse(
            agent_name=self.name,
            role=self.role,
            summary=summary,
            details={"recommendations": [r.model_dump() for r in recs]},
            narrative=narrative,
            recommendations=recommendations_list,
            mode="deterministic_fallback",
        )
