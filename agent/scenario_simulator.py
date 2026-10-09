"""
Bhujal — Climate Sensitivity & Scenario Simulator Agent
========================================================
Specialized agent evaluating watershed sensitivity under rainfall perturbations
and estimating the protective resilience delta delivered by proposed civil structures.
"""

from __future__ import annotations

from typing import Any

from agent.base import AgentResponse, BaseAgent
from backend.models import ScenarioResult


class ScenarioSimulatorAgent(BaseAgent):
    """Simulator agent analyzing climate sensitivity and intervention uplifts."""

    def __init__(self) -> None:
        super().__init__(
            name="ScenarioSimulatorAgent",
            role="Climate Sensitivity & Scenario Simulator",
            system_prompt=(
                "You are a climate adaptation strategist and hydrological modeler. You evaluate "
                "how monsoon variability (-50% drought to +50% surplus) impacts village groundwater "
                "recharge, spring stability, and heat stress. You quantify the protective resilience "
                "buffer delivered by civil engineering structures."
            ),
        )

    def fallback_execute(self, context: dict[str, Any]) -> AgentResponse:
        res: ScenarioResult = context.get("scenario_result")  # type: ignore
        village_name = context.get("village_name", "Target Site")

        fraction = context.get("rainfall_fraction", 1.0)
        pct = round((fraction - 1.0) * 100.0, 1)
        rain_adj = res.rainfall_mm_adjusted if res else 1400.0
        intervention = res.intervention_applied if res else None

        base_scores = {
            s.score_type: s.value for s in (res.baseline_scores if res else [])
        }
        adj_scores = {
            s.score_type: s.value for s in (res.adjusted_scores if res else [])
        }

        recharge_delta = adj_scores.get("recharge_score", 0.0) - base_scores.get(
            "recharge_score", 0.0
        )
        stress_delta = adj_scores.get("heat_water_stress", 0.0) - base_scores.get(
            "heat_water_stress", 0.0
        )

        summary = (
            f"Under a {fraction:.2f}x monsoon scenario ({pct:+g}% anomaly, {rain_adj:.0f} mm), "
            f"groundwater recharge shifts by {recharge_delta:+.1f} points and heat-water stress by {stress_delta:+.1f} points."
        )

        narrative = (
            f"Climate Sensitivity Simulation for {village_name}:\n"
            f"- Scenario Parameter: Precipitation scaled to {fraction:.2f}x normal ({rain_adj:.0f} mm vs. 1400 mm normal).\n"
            f"- Intervention Buffer: {f'Active structural simulation with {intervention}' if intervention else 'No civil structure buffer applied'}.\n"
            f"- Hydrological Impact:\n"
            f"  * Recharge Suitability: Shifted from {base_scores.get('recharge_score', 0):.1f} to {adj_scores.get('recharge_score', 0):.1f} ({recharge_delta:+.1f} pts)\n"
            f"  * Heat-Water Vulnerability: Shifted from {base_scores.get('heat_water_stress', 0):.1f} to {adj_scores.get('heat_water_stress', 0):.1f} ({stress_delta:+.1f} pts)\n"
            f"- Strategic Insight: {'Constructing the proposed intervention mitigates a substantial fraction of drought-induced recharge deficit.' if recharge_delta >= 0 and pct < 0 else 'Unmitigated rainfall deficits will severely depress dry-season water availability unless storage is expanded.'}"
        )

        recs = [
            f"Incorporate a minimum {rain_adj:.0f} mm seasonal rainfall threshold into village emergency water contingency plans.",
            "Design surface check structures with emergency spillways capable of managing +50% excess flash storm surges.",
        ]

        return AgentResponse(
            agent_name=self.name,
            role=self.role,
            summary=summary,
            details=res.model_dump() if res else {},
            narrative=narrative,
            recommendations=recs,
            mode="deterministic_fallback",
        )
