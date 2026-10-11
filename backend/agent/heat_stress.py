"""
Bhujal — Heat-Water Vulnerability Diagnostician Agent
=====================================================
Specialized agent diagnosing compound thermal anomalies, vegetation defoliation,
monsoon deficits, and dry-season drinking water accessibility stress.
"""

from __future__ import annotations

from typing import Any

from agent.base import AgentResponse, BaseAgent
from backend.models import ScoreResult


class HeatWaterStressAgent(BaseAgent):
    """Diagnostician analyzing compound thermal and water scarcity distress."""

    def __init__(self) -> None:
        super().__init__(
            name="HeatWaterStressAgent",
            role="Heat-Water Vulnerability Diagnostician",
            system_prompt=(
                "You are an expert environmental climatologist specializing in compound heat and "
                "water vulnerability across tribal communities in central and eastern India. "
                "You analyze satellite thermal radiometric anomalies (MODIS LST), vegetative "
                "moisture indicators (NDVI), and localized water accessibility deficits. "
                "Translate deterministic stress metrics into urgent, actionable administrative guidance."
            ),
        )

    def fallback_execute(self, context: dict[str, Any]) -> AgentResponse:
        score: ScoreResult = context.get("score")  # type: ignore
        village_name = context.get("village_name", "Target Site")

        val = score.value if score else 0.0
        s_class = score.score_class.value if score else "unknown"
        drivers = score.drivers if score else []

        top_driver = max(drivers, key=lambda d: d.contribution) if drivers else None

        summary = (
            f"Compound heat-water stress at {village_name} is assessed at {s_class.upper()} "
            f"severity ({val:.1f}/100)."
        )

        detail_text = ""
        if top_driver:
            detail_text = (
                f" The primary vulnerability amplifier is '{top_driver.factor}' "
                f"generating a contribution of {top_driver.contribution:.1f} points."
            )

        narrative = (
            f"Compound Heat-Water Vulnerability Diagnosis for {village_name}:\n"
            f"- Severity Classification: {s_class.upper()} ({val:.1f}/100).\n"
            f"- Critical Driver: {detail_text}\n"
            f"- Risk Assessment: Pre-monsoon thermal radiative exposure coincides with dry-season "
            f"water table decline. Tribal settlements in this corridor face compounded physiological "
            f"and agricultural stress when surface water sources dry up before June monsoon arrival."
        )

        recs = [
            f"Establish community heat shelter zones and shaded drinking water points (Stress: {val:.1f}).",
            "Accelerate decentralized rainwater harvesting to buffer pre-monsoon water depletion.",
            "Promote indigenous agroforestry and canopy planting along village settlement boundaries.",
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
