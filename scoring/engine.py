"""
Bhujal — Unified Spatial Evaluation Engine
===========================================
Coordinates site retrieval, multi-criteria scoring, safety veto evaluations,
and civil intervention composition.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from backend.models import (
    DataTag,
    Recommendation,
    SafetyStatus,
    ScenarioResult,
    Site,
    Village,
)
from scoring.interventions import compose_recommendations
from scoring.recharge import calculate_recharge_score
from scoring.safety import evaluate_safety_rules
from scoring.simulator import simulate_scenario
from scoring.springs import calculate_spring_drying_index
from scoring.stress import calculate_heat_water_stress

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@lru_cache(maxsize=1)
def _load_demo_sites_config() -> dict[str, Any]:
    with open(CONFIG_DIR / "demo_sites.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_all_villages() -> list[Village]:
    """Retrieve all villages in the demonstration Area of Interest."""
    cfg = _load_demo_sites_config()
    villages: list[Village] = []
    for s in cfg.get("sites", []):
        dtag = DataTag(s.get("data_tag", "illustrative"))
        v = Village(
            id=s["id"],
            name=s["name"],
            block=s["block"],
            district=s["district"],
            state=s["state"],
            lat=float(s["lat"]),
            lon=float(s["lon"]),
            elevation_m=float(s["elevation_m"])
            if s.get("elevation_m") is not None
            else None,
            population=int(s["population"])
            if s.get("population") is not None
            else None,
            has_spring=bool(s.get("has_spring", False)),
            data_tag=dtag,
        )
        villages.append(v)
    return villages


def get_site_raw_data(site_id: str) -> dict[str, Any] | None:
    """Find a demo site raw record by identifier."""
    cfg = _load_demo_sites_config()
    for s in cfg.get("sites", []):
        if s["id"] == site_id:
            return s
    return None


def evaluate_site(site_id: str) -> Site | None:
    """
    Perform complete deterministic hydro-climatic analysis, safety evaluation,
    and intervention matching for a specified site.
    """
    raw = get_site_raw_data(site_id)
    if not raw:
        return None

    dtag = DataTag(raw.get("data_tag", "illustrative"))
    village = Village(
        id=raw["id"],
        name=raw["name"],
        block=raw["block"],
        district=raw["district"],
        state=raw["state"],
        lat=float(raw["lat"]),
        lon=float(raw["lon"]),
        elevation_m=float(raw["elevation_m"])
        if raw.get("elevation_m") is not None
        else None,
        population=int(raw["population"])
        if raw.get("population") is not None
        else None,
        has_spring=bool(raw.get("has_spring", False)),
        data_tag=dtag,
    )

    features = raw.get("features", {}).copy()
    if "elevation_m" not in features and village.elevation_m is not None:
        features["elevation_m"] = village.elevation_m

    # Ground missing hydro-climatic indicators with lazy, cached empirical derived data
    from scoring.derived_loader import get_settlement_derived_data

    settlement_telemetry = get_settlement_derived_data(site_id)
    if settlement_telemetry:
        gw_station = settlement_telemetry.get("groundwater", {}).get("nearest_station")
        if (
            gw_station
            and "groundwater_depth_m" not in features
            and gw_station.get("post_monsoon_depth_m") is not None
        ):
            features["groundwater_depth_m"] = gw_station["post_monsoon_depth_m"]

        temp_grid = settlement_telemetry.get("temperature", {})
        if (
            temp_grid
            and "lst_summer_max_c" not in features
            and temp_grid.get("summer_mean_max_c") is not None
        ):
            features["lst_summer_max_c"] = temp_grid["summer_mean_max_c"]

    # 1. Deterministic Scores
    recharge_res = calculate_recharge_score(
        features, data_tag=dtag, field_provenance=raw.get("field_provenance", {})
    )
    stress_res = calculate_heat_water_stress(
        features, data_tag=dtag, field_provenance=raw.get("field_provenance", {})
    )
    spring_res = calculate_spring_drying_index(
        features,
        has_spring=village.has_spring,
        data_tag=dtag,
        field_provenance=raw.get("field_provenance", {}),
    )

    scores = [recharge_res, stress_res, spring_res]

    # 2. Safety Veto Evaluation
    safety_verdict = evaluate_safety_rules(features)
    is_rejected = safety_verdict.status == SafetyStatus.REJECTED

    # 3. Civil Intervention Matching & Costing
    recommendations = compose_recommendations(
        features,
        has_spring=village.has_spring,
        is_rejected=is_rejected,
        state=village.state,
    )

    return Site(
        village=village,
        scores=scores,
        safety=safety_verdict,
        recommendations=recommendations,
    )


def run_site_scenario(
    site_id: str,
    rainfall_fraction: float = 1.0,
    include_intervention: str | None = None,
) -> ScenarioResult | None:
    """Execute scenario simulation for a site using its computed baseline scores."""
    site = evaluate_site(site_id)
    if not site:
        return None

    return simulate_scenario(
        site_id=site_id,
        baseline_scores=site.scores,
        rainfall_fraction=rainfall_fraction,
        include_intervention=include_intervention,
    )


def get_site_recommendations(site_id: str) -> list[Recommendation] | None:
    """Retrieve recommendations for a site."""
    site = evaluate_site(site_id)
    if not site:
        return None
    return site.recommendations


def clear_caches() -> None:
    """Clear all LRU caches (useful for testing or config reload)."""
    _load_demo_sites_config.cache_clear()
    from scoring.derived_loader import (
        load_derived_groundwater,
        load_derived_rainfall,
        load_derived_settlements,
        load_derived_temperature,
    )

    load_derived_groundwater.cache_clear()
    load_derived_rainfall.cache_clear()
    load_derived_settlements.cache_clear()
    load_derived_temperature.cache_clear()
