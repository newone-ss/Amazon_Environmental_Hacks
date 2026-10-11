"""
Bhujal — Hydrogeological Recharge Analyst Agent
================================================
Specialized agent analyzing groundwater infiltration suitability,
topographic gradients, soil textures, and secondary fracture conduits.
"""

from __future__ import annotations

from typing import Any

from agent.base import AgentResponse, BaseAgent
from backend.models import ScoreResult


class HydrogeologyAgent(BaseAgent):
    """Analyst evaluating groundwater recharge dynamics."""

    def __init__(self) -> None:
        super().__init__(
            name="HydrogeologyAgent",
            role="Hydrogeological Recharge Analyst",
            system_prompt=(
                "You are an expert hydrogeologist specializing in crystalline hard-rock aquifers "
                "of India's Eastern Ghats. You analyze deterministic recharge suitability scores, "
                "topographic slope, soil permeability, and fracture lineaments to produce objective, "
                "scientifically rigorous planning recommendations for block watershed development. "
                "Never invent numerical values; base your narrative strictly on the provided data."
            ),
        )

    def fallback_execute(self, context: dict[str, Any]) -> AgentResponse:
        score: ScoreResult = context.get("score")  # type: ignore
        village_name = context.get("village_name", "Target Site")

        val = score.value if score else 0.0
        s_class = score.score_class.value if score else "unknown"
        drivers = score.drivers if score else []

        top_driver = max(drivers, key=lambda d: d.contribution) if drivers else None
        lowest_driver = min(drivers, key=lambda d: d.contribution) if drivers else None

        summary = (
            f"Groundwater recharge suitability at {village_name} is classified as {s_class.upper()} "
            f"with an overall index of {val:.1f}/100."
        )

        driver_narrative = ""
        if top_driver:
            driver_narrative += (
                f" The primary favorable factor is '{top_driver.factor}' "
                f"(contributing {top_driver.contribution:.1f} points at weight {top_driver.weight})."
            )
        if lowest_driver and lowest_driver != top_driver:
            driver_narrative += (
                f" The primary hydrological limiting factor is '{lowest_driver.factor}' "
                f"(contributing only {lowest_driver.contribution:.1f} points)."
            )

        narrative = (
            f"Hydrogeological Assessment for {village_name}:\n"
            f"- Infiltration Potential: {s_class.title()} ({val:.1f}/100).\n"
            f"- Analytical Drivers: {driver_narrative}\n"
            f"- Hydrogeological Context: Situated in Eastern Ghats charnockite/granite complex. "
            f"Artificial recharge interventions should focus on harvesting monsoon runoff along low-order "
            f"drainage corridors to maximize secondary porosity infiltration."
        )

        recs = [
            f"Prioritize recharge structures along verified lineament fracture traces ({val:.1f} index).",
            "Maintain vegetative surface mulch to prolong hydrological contact time on hillslopes.",
            "Verify local weathering thickness via 2D electrical resistivity sounding prior to deep excavation.",
        ]

        return AgentResponse(
            agent_name=self.name,
            role=self.role,
            summary=summary,
            details=score.model_dump() if score else {},
            narrative=narrative,
            recommendations=recs,
            mode="deterministic_fallback",
        )
