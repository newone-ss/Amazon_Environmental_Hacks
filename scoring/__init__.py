"""
Bhujal — Scoring Engine Package
================================
Provides deterministic, config-driven hydrogeological scoring, safety veto evaluations,
civil intervention matching, and climate scenario simulation.
"""

from scoring.engine import (
    evaluate_site,
    get_all_villages,
    get_site_recommendations,
    run_site_scenario,
)
from scoring.interventions import compose_recommendations
from scoring.recharge import calculate_recharge_score
from scoring.safety import evaluate_safety_rules
from scoring.simulator import simulate_scenario
from scoring.springs import calculate_spring_drying_index
from scoring.stress import calculate_heat_water_stress

__all__ = [
    "calculate_heat_water_stress",
    "calculate_recharge_score",
    "calculate_spring_drying_index",
    "compose_recommendations",
    "evaluate_safety_rules",
    "evaluate_site",
    "get_all_villages",
    "get_site_recommendations",
    "run_site_scenario",
    "simulate_scenario",
]
