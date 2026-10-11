"""
Bhujal — Springhead Catchment Sentry Agent
===========================================
Specialized agent evaluating seasonal drying hazards and baseflow depletion
for mountain springs (jhola/jharna) in tribal micro-watersheds.
"""

from __future__ import annotations

from typing import Any

from agent.base import AgentResponse, BaseAgent
from backend.models import ScoreResult


class SpringshedAgent(BaseAgent):
    """Sentry evaluating mountain springhead baseflow vulnerability."""

    def __init__(self) -> None:
        super().__init__(
            name="SpringshedAgent",
            role="Springhead Catchment Sentry",
            system_prompt=(
                "You are an expert hydrogeologist and springshed management specialist working on "
                "mountain water security in the Eastern Ghats. You evaluate spring drying risk, "
                "catchment deforestation, upslope flow accumulation, and monsoon trends to prescribe "
                "ridge-to-valley springshed revitalisation protocols. Ground your findings strictly in the data."
            ),
        )

    def fallback_execute(self, context: dict[str, Any]) -> AgentResponse:
        score: ScoreResult = context.get("score")  # type: ignore
        village_name = context.get("village_name", "Target Site")
        has_spring = context.get("has_spring", True)

        if not has_spring or (score and score.value == 0.0):
            return AgentResponse(
                agent_name=self.name,
                role=self.role,
                summary=f"No active springhead infrastructure or discharge point recorded at {village_name}.",
                details={"has_spring": False},
                narrative=(
                    f"Springshed Assessment for {village_name}: No perennial or seasonal springs are documented "
                    f"in the administrative registry for this micro-catchment. Surface water harvesting and "
                    f"subsurface bore recharge protocols apply instead."
                ),
                recommendations=[
                    "Focus watershed planning on surface storage structures rather than springshed treatment."
                ],
                mode="deterministic_fallback",
            )

        val = score.value if score else 0.0
        s_class = score.score_class.value if score else "unknown"
        drivers = score.drivers if score else []

        top_driver = max(drivers, key=lambda d: d.contribution) if drivers else None

        summary = (
            f"Springhead drying risk at {village_name} is evaluated as {s_class.upper()} "
            f"({val:.1f}/100 vulnerability index)."
        )

        detail_text = ""
        if top_driver:
            detail_text = f" Contributing degradation factor: '{top_driver.factor}' ({top_driver.contribution:.1f} pts)."

        narrative = (
            f"Springhead Vulnerability Assessment for {village_name}:\n"
            f"- Baseflow Risk Tier: {s_class.upper()} ({val:.1f}/100).\n"
            f"- Catchment Diagnostic: {detail_text}\n"
            f"- Hydrological Dynamics: Mountain springs in this terrain rely on fractured recharge zones "
            f"in elevated ridges. High forest canopy loss or small recharge catchments diminish "
            f"winter-to-summer baseflow retention, resulting in spring dry-up by March or April."
        )

        recs = [
            f"Implement comprehensive springshed treatment in the recharge zone (Vulnerability: {val:.1f}).",
            "Excavate staggered contour trenches and planting pits on slopes above the spring outlet.",
            "Enclose the immediate recharge area to prevent cattle trampling and soil compaction.",
            "Install a flow-monitoring v-notch weir to establish baseline seasonal discharge time series.",
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
