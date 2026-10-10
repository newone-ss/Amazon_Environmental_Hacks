"""
Bhujal — Scoring Engine Package
================================
Provides deterministic, config-driven hydrogeological scoring, safety veto evaluations,
civil intervention matching, and climate scenario simulation.
"""

from scoring.base import (
    ConfigError,
    FeatureError,
    ScoringError,
    clamp,
    classify_score,
    compute_weighted_score,
    get_costs_config,
    get_demo_sites_config,
    get_interventions_config,
    get_safety_config,
    get_scenario_config,
    get_weights_config,
    normalize_linear,
)
from scoring.engine import (
    evaluate_site,
    get_all_villages,
    get_site_raw_data,
    get_site_recommendations,
    run_site_scenario,
)
from scoring.interventions import compose_recommendations
from scoring.pathways import (
    AdaptationPathway,
    PathwayStep,
    calculate_pathway_npv,
    generate_adaptation_pathway,
    generate_pathway_comparison,
    generate_pathway_visualization_data,
    load_pathway_config,
    pathway_to_dict,
)
from scoring.recharge import calculate_recharge_score
from scoring.safety import evaluate_safety_rules
from scoring.simulator import simulate_scenario
from scoring.springs import calculate_spring_drying_index
from scoring.stress import calculate_heat_water_stress

__all__ = [
    "AdaptationPathway",
    "ConfigError",
    "FeatureError",
    "PathwayStep",
    "ScoringError",
    "calculate_heat_water_stress",
    "calculate_pathway_npv",
    "calculate_recharge_score",
    "calculate_spring_drying_index",
    "clamp",
    "classify_score",
    "compose_recommendations",
    "compute_weighted_score",
    "evaluate_safety_rules",
    "evaluate_site",
    "generate_adaptation_pathway",
    "generate_pathway_comparison",
    "generate_pathway_visualization_data",
    "get_all_villages",
    "get_costs_config",
    "get_demo_sites_config",
    "get_interventions_config",
    "get_safety_config",
    "get_scenario_config",
    "get_site_raw_data",
    "get_site_recommendations",
    "get_weights_config",
    "load_pathway_config",
    "normalize_linear",
    "pathway_to_dict",
    "run_site_scenario",
    "simulate_scenario",
]
