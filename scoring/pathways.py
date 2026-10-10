"""
Bhujal — Dynamic Adaptation Pathways Engine
============================================
Multi-period climate adaptation planning under SSP scenarios.
Generates sequential intervention pathways with decision nodes for adaptive management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from scoring.engine import evaluate_site, run_site_scenario

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@dataclass
class PathwayStep:
    """A single step in an adaptation pathway."""

    period: str  # e.g., "2025-2030"
    year_start: int
    year_end: int
    rainfall_fraction: float
    ssp_scenario: str
    baseline_scores: dict[str, float]
    recommended_interventions: list[dict[str, Any]]
    decision_node: bool = False
    trigger_condition: str | None = None
    trigger_threshold: float | None = None
    alternative_pathway: str | None = None
    cumulative_cost_inr: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass
class AdaptationPathway:
    """Complete adaptation pathway for a site."""

    site_id: str
    site_name: str
    ssp_scenario: str
    steps: list[PathwayStep]
    total_cost_inr: float
    final_recharge_score: float
    final_stress_score: float
    final_spring_risk: float
    success_probability: float


@dataclass
class PathwayConfig:
    """Configuration for pathway generation."""

    periods: list[tuple[int, int]] = field(
        default_factory=lambda: [
            (2025, 2030),
            (2030, 2035),
            (2035, 2040),
            (2040, 2045),
            (2045, 2050),
        ]
    )
    ssp_scenarios: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            "SSP1-2.6": {"rainfall_trend": 0.02, "temp_trend": 0.01},  # Sustainable
            "SSP2-4.5": {"rainfall_trend": -0.01, "temp_trend": 0.02},  # Middle of road
            "SSP5-8.5": {"rainfall_trend": -0.03, "temp_trend": 0.04},  # Fossil-fueled
        }
    )
    intervention_lifespan_years: dict[str, int] = field(
        default_factory=lambda: {
            "check_dam": 15,
            "percolation_tank": 20,
            "contour_trench": 10,
            "spring_shed_treatment": 25,
            "rooftop_rainwater_harvesting": 20,
            "farm_pond": 15,
            "gabion_structure": 20,
        }
    )
    decision_triggers: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            "recharge_score": {"critical": 30, "warning": 50},
            "heat_water_stress": {"critical": 70, "warning": 50},
            "spring_drying_index": {"critical": 70, "warning": 50},
        }
    )
    cost_escalation_per_period: float = 0.05
    discount_rate: float = 0.08


@dataclass
class _RawPathwayConfig:
    """Raw config loaded from YAML before conversion to PathwayConfig."""

    periods: list[list[int]]
    ssp_scenarios: dict[str, dict[str, float]]
    intervention_lifespan_years: dict[str, int]
    decision_triggers: dict[str, dict[str, float]]
    cost_escalation_per_period: float = 0.05
    discount_rate: float = 0.08


def load_pathway_config() -> PathwayConfig:
    """Load pathway configuration from YAML or return defaults."""
    config_path = CONFIG_DIR / "pathways.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            raw = _RawPathwayConfig(**data)
            return PathwayConfig(
                periods=[tuple(p) for p in raw.periods],
                ssp_scenarios=raw.ssp_scenarios,
                intervention_lifespan_years=raw.intervention_lifespan_years,
                decision_triggers=raw.decision_triggers,
                cost_escalation_per_period=raw.cost_escalation_per_period,
                discount_rate=raw.discount_rate,
            )
    return PathwayConfig()


def _get_ssp_rainfall_fraction(
    ssp: str, period_idx: int, base_fraction: float = 1.0
) -> float:
    """
    Calculate rainfall fraction for a given SSP scenario and period.

    SSP1-2.6: slight increase (+2%/decade)
    SSP2-4.5: slight decrease (-1%/decade)
    SSP5-8.5: significant decrease (-3%/decade)
    """
    config = load_pathway_config()
    ssp_config = config.ssp_scenarios.get(ssp, config.ssp_scenarios["SSP2-4.5"])
    trend = ssp_config.get("rainfall_trend", 0.0)
    # 5-year periods, so 0.5 decades per period
    decades_elapsed = period_idx * 0.5
    return round(base_fraction * (1.0 + trend * decades_elapsed), 2)


def _get_ssp_temperature_increase(ssp: str, period_idx: int) -> float:
    """Calculate temperature increase for SSP scenario."""
    config = load_pathway_config()
    ssp_config = config.ssp_scenarios.get(ssp, config.ssp_scenarios["SSP2-4.5"])
    trend = ssp_config.get("temp_trend", 0.0)
    decades_elapsed = period_idx * 0.5
    return round(trend * decades_elapsed * 10, 1)  # °C per decade


def _check_decision_triggers(
    scores: dict[str, float],
    triggers: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    """Check if any decision triggers are activated."""
    triggered = []
    for score_name, thresholds in triggers.items():
        value = scores.get(score_name, 0)
        if value >= thresholds.get("critical", 100):
            triggered.append(
                {
                    "score": score_name,
                    "level": "critical",
                    "threshold": thresholds["critical"],
                    "current_value": value,
                    "action": f"Immediate intervention required: {score_name} at {value}",
                }
            )
        elif value >= thresholds.get("warning", 100):
            triggered.append(
                {
                    "score": score_name,
                    "level": "warning",
                    "threshold": thresholds["warning"],
                    "current_value": value,
                    "action": f"Prepare contingency: {score_name} approaching threshold",
                }
            )
    return triggered


def _select_interventions_for_period(
    site_id: str,
    scores: dict[str, float],
    period_idx: int,
    existing_interventions: list[str],
    config: PathwayConfig,
) -> list[dict[str, Any]]:
    """Select appropriate interventions for a planning period based on scores and triggers."""
    site = evaluate_site(site_id)
    if not site:
        return []

    recommendations = []
    triggers = _check_decision_triggers(scores, config.decision_triggers)

    # Priority 1: Critical triggers - immediate action
    critical_triggers = [t for t in triggers if t["level"] == "critical"]
    if critical_triggers:
        for trigger in critical_triggers:
            if (
                trigger["score"] == "recharge_score"
                and "check_dam" not in existing_interventions
            ):
                recommendations.append(
                    {
                        "intervention_id": "check_dam",
                        "priority": "immediate",
                        "reason": f"Critical recharge score ({trigger['current_value']}) - check dam needed",
                        "estimated_cost": 300000,
                    }
                )
            elif (
                trigger["score"] == "spring_drying_index"
                and "spring_shed_treatment" not in existing_interventions
            ):
                recommendations.append(
                    {
                        "intervention_id": "spring_shed_treatment",
                        "priority": "immediate",
                        "reason": f"Critical spring drying risk ({trigger['current_value']}) - springshed treatment needed",
                        "estimated_cost": 400000,
                    }
                )
            elif (
                trigger["score"] == "heat_water_stress"
                and "rooftop_rainwater_harvesting" not in existing_interventions
            ):
                recommendations.append(
                    {
                        "intervention_id": "rooftop_rainwater_harvesting",
                        "priority": "immediate",
                        "reason": f"Critical heat-water stress ({trigger['current_value']}) - RWH needed",
                        "estimated_cost": 25000,
                    }
                )

    # Priority 2: Warning triggers - planned action
    warning_triggers = [t for t in triggers if t["level"] == "warning"]
    if warning_triggers and not critical_triggers:
        for trigger in warning_triggers:
            if (
                trigger["score"] == "recharge_score"
                and "percolation_tank" not in existing_interventions
            ):
                recommendations.append(
                    {
                        "intervention_id": "percolation_tank",
                        "priority": "planned",
                        "reason": f"Declining recharge score ({trigger['current_value']}) - percolation tank planned",
                        "estimated_cost": 550000,
                    }
                )
            elif (
                trigger["score"] == "heat_water_stress"
                and "farm_pond" not in existing_interventions
            ):
                recommendations.append(
                    {
                        "intervention_id": "farm_pond",
                        "priority": "planned",
                        "reason": f"Increasing heat stress ({trigger['current_value']}) - farm pond planned",
                        "estimated_cost": 150000,
                    }
                )

    # Priority 3: Maintenance/rotation of existing interventions
    for intervention in existing_interventions:
        lifespan = config.intervention_lifespan_years.get(intervention, 20)
        if period_idx * 5 >= lifespan:
            # Intervention needs replacement/rehabilitation
            recommendations.append(
                {
                    "intervention_id": intervention,
                    "priority": "maintenance",
                    "reason": f"{intervention} approaching end of design life ({lifespan} years)",
                    "estimated_cost": 100000,
                }
            )

    return recommendations


def generate_adaptation_pathway(
    site_id: str,
    ssp_scenario: str = "SSP2-4.5",
    base_rainfall_fraction: float = 1.0,
) -> AdaptationPathway:
    """
    Generate a complete multi-period adaptation pathway for a site.

    Args:
        site_id: Site identifier
        ssp_scenario: SSP scenario (SSP1-2.6, SSP2-4.5, SSP5-8.5)
        base_rainfall_fraction: Baseline rainfall fraction for period 0

    Returns:
        AdaptationPathway with steps for each planning period
    """
    site = evaluate_site(site_id)
    if not site:
        raise ValueError(f"Site {site_id} not found")

    config = load_pathway_config()
    steps: list[PathwayStep] = []
    existing_interventions: list[str] = []
    cumulative_cost = 0.0

    # Initial baseline scores
    baseline_scores = {s.score_type: s.value for s in site.scores}

    for period_idx, (year_start, year_end) in enumerate(config.periods):
        period_label = f"{year_start}-{year_end}"

        # Calculate climate forcing for this period
        rainfall_frac = _get_ssp_rainfall_fraction(
            ssp_scenario, period_idx, base_rainfall_fraction
        )
        temp_increase = _get_ssp_temperature_increase(ssp_scenario, period_idx)

        # Run scenario simulation
        scenario_result = run_site_scenario(
            site_id=site_id,
            rainfall_fraction=rainfall_frac,
            include_intervention=existing_interventions[0]
            if existing_interventions
            else None,
        )

        if scenario_result:
            current_scores = {
                s.score_type: s.value for s in scenario_result.adjusted_scores
            }
        else:
            current_scores = baseline_scores.copy()

        # Adjust heat stress for temperature increase
        if "heat_water_stress" in current_scores:
            # Temperature increase adds to heat stress
            current_scores["heat_water_stress"] = min(
                100, current_scores["heat_water_stress"] + temp_increase * 2
            )

        # Select interventions for this period
        period_interventions = _select_interventions_for_period(
            site_id, current_scores, period_idx, existing_interventions, config
        )

        # Track new interventions
        new_interventions = [
            i["intervention_id"]
            for i in period_interventions
            if i["priority"] != "maintenance"
        ]
        existing_interventions.extend(new_interventions)

        # Calculate period cost with escalation
        period_cost = sum(i.get("estimated_cost", 0) for i in period_interventions)
        period_cost *= (1 + config.cost_escalation_per_period) ** period_idx
        cumulative_cost += period_cost

        # Check for decision nodes
        triggers = _check_decision_triggers(current_scores, config.decision_triggers)
        decision_node = len(triggers) > 0
        trigger_info = triggers[0] if triggers else None

        step = PathwayStep(
            period=period_label,
            year_start=year_start,
            year_end=year_end,
            rainfall_fraction=rainfall_frac,
            ssp_scenario=ssp_scenario,
            baseline_scores=current_scores,
            recommended_interventions=period_interventions,
            decision_node=decision_node,
            trigger_condition=trigger_info["score"] if trigger_info else None,
            trigger_threshold=trigger_info["threshold"] if trigger_info else None,
            alternative_pathway=f"accelerated_{ssp_scenario}"
            if decision_node
            else None,
            cumulative_cost_inr=cumulative_cost,
            notes=[
                (
                    f"SSP: {ssp_scenario}, Rainfall: {rainfall_frac:.2f}x, Temp: +{temp_increase:.1f}°C"
                ),
                (
                    f"Recharge: {current_scores.get('recharge_score', 0):.1f}, "
                    f"Stress: {current_scores.get('heat_water_stress', 0):.1f}, "
                    f"Spring Risk: {current_scores.get('spring_drying_index', 0):.1f}"
                ),
            ]
            + [t["action"] for t in triggers],
        )
        steps.append(step)

    # Calculate success probability based on final scores
    final_scores = steps[-1].baseline_scores
    recharge_final = final_scores.get("recharge_score", 0)
    stress_final = final_scores.get("heat_water_stress", 100)
    spring_final = final_scores.get("spring_drying_index", 100)

    success_prob = (
        (recharge_final / 100) * 0.4
        + ((100 - stress_final) / 100) * 0.3
        + ((100 - spring_final) / 100) * 0.3
    )

    return AdaptationPathway(
        site_id=site_id,
        site_name=site.village.name,
        ssp_scenario=ssp_scenario,
        steps=steps,
        total_cost_inr=cumulative_cost,
        final_recharge_score=recharge_final,
        final_stress_score=stress_final,
        final_spring_risk=spring_final,
        success_probability=round(success_prob, 2),
    )


def generate_pathway_comparison(
    site_id: str,
    scenarios: list[str] | None = None,
) -> dict[str, AdaptationPathway]:
    """Generate pathways for multiple SSP scenarios for comparison."""
    if scenarios is None:
        scenarios = ["SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]

    pathways = {}
    for ssp in scenarios:
        try:
            pathways[ssp] = generate_adaptation_pathway(site_id, ssp)
        except Exception as exc:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).error(
                "Pathway generation failed for %s: %s", ssp, exc
            )

    return pathways


def pathway_to_dict(pathway: AdaptationPathway) -> dict[str, Any]:
    """Convert pathway to dictionary for API/JSON serialization."""
    return {
        "site_id": pathway.site_id,
        "site_name": pathway.site_name,
        "ssp_scenario": pathway.ssp_scenario,
        "total_cost_inr": pathway.total_cost_inr,
        "final_scores": {
            "recharge_score": pathway.final_recharge_score,
            "heat_water_stress": pathway.final_stress_score,
            "spring_drying_index": pathway.final_spring_risk,
        },
        "success_probability": pathway.success_probability,
        "steps": [
            {
                "period": step.period,
                "year_start": step.year_start,
                "year_end": step.year_end,
                "rainfall_fraction": step.rainfall_fraction,
                "ssp_scenario": step.ssp_scenario,
                "scores": step.baseline_scores,
                "interventions": step.recommended_interventions,
                "decision_node": step.decision_node,
                "trigger": {
                    "condition": step.trigger_condition,
                    "threshold": step.trigger_threshold,
                    "alternative": step.alternative_pathway,
                }
                if step.decision_node
                else None,
                "cumulative_cost_inr": step.cumulative_cost_inr,
                "notes": step.notes,
            }
            for step in pathway.steps
        ],
    }


def generate_pathway_visualization_data(pathway: AdaptationPathway) -> dict[str, Any]:
    """Generate data structure optimized for frontend pathway visualization (like IPCC AR6 Fig 16.3)."""
    return {
        "site_id": pathway.site_id,
        "site_name": pathway.site_name,
        "ssp_scenario": pathway.ssp_scenario,
        "timeline": {
            "periods": [step.period for step in pathway.steps],
            "recharge_scores": [
                step.baseline_scores.get("recharge_score", 0) for step in pathway.steps
            ],
            "stress_scores": [
                step.baseline_scores.get("heat_water_stress", 0)
                for step in pathway.steps
            ],
            "spring_risk_scores": [
                step.baseline_scores.get("spring_drying_index", 0)
                for step in pathway.steps
            ],
            "decision_nodes": [
                {
                    "period": step.period,
                    "trigger": step.trigger_condition,
                    "threshold": step.trigger_threshold,
                }
                for step in pathway.steps
                if step.decision_node
            ],
            "cumulative_cost": [step.cumulative_cost_inr for step in pathway.steps],
        },
        "intervention_timeline": _build_intervention_timeline(pathway),
        "summary": {
            "total_cost_inr": pathway.total_cost_inr,
            "success_probability": pathway.success_probability,
            "final_recharge": pathway.final_recharge_score,
            "final_stress": pathway.final_stress_score,
        },
    }


def _build_intervention_timeline(pathway: AdaptationPathway) -> list[dict[str, Any]]:
    """Build intervention timeline for Gantt-style visualization."""
    timeline = []
    for step in pathway.steps:
        for intervention in step.recommended_interventions:
            timeline.append(
                {
                    "intervention_id": intervention["intervention_id"],
                    "period": step.period,
                    "priority": intervention["priority"],
                    "reason": intervention["reason"],
                    "cost": intervention.get("estimated_cost", 0),
                }
            )
    return timeline


def calculate_pathway_npv(
    pathway: AdaptationPathway, discount_rate: float | None = None
) -> float:
    """Calculate Net Present Value of pathway costs."""
    config = load_pathway_config()
    rate = discount_rate or config.discount_rate
    npv = 0.0
    for step in pathway.steps:
        period_cost = sum(
            i.get("estimated_cost", 0) for i in step.recommended_interventions
        )
        years_from_now = step.year_start - 2025
        npv += period_cost / ((1 + rate) ** years_from_now)
    return round(npv, 2)
