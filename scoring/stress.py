"""
Bhujal — Heat-Water Stress Scoring Engine
==========================================
Calculates compound heat and water vulnerability (0-100) using
deterministic weighted overlays driven by config/weights.yaml.
Adheres strictly to Rule 4 of agent.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from backend.models import (
    Confidence,
    ConfidenceLevel,
    DataTag,
    Driver,
    ScoreClass,
    ScoreResult,
)

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_weights_config() -> dict[str, Any]:
    weights_path = CONFIG_DIR / "weights.yaml"
    with open(weights_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def calculate_heat_water_stress(
    features: dict[str, Any],
    data_tag: DataTag = DataTag.ILLUSTRATIVE,
) -> ScoreResult:
    """
    Calculate compound heat-water stress score from surface thermal and water accessibility indicators.

    Keys in features:
      - lst_summer_max_c: float (surface temperature in Celsius, e.g., 30.0 - 50.0)
      - ndvi_summer: float (0.0 - 1.0, lower NDVI = higher stress)
      - rainfall_deficit_pct: float (percentage departure, e.g., 0.0 - 50.0)
      - groundwater_depth_m: float (meters to water table, e.g., 2.0 - 30.0)
      - distance_to_perennial_water_m: float (meters, e.g., 50.0 - 5000.0)
      - population_density_per_km2: float (people / sq km, e.g., 20.0 - 800.0)
    """
    cfg = load_weights_config()
    weights_spec = cfg.get("heat_water_stress", {}).get("factors", {})

    # 1. Normalize individual factors to [0.0, 1.0] where 1.0 = maximum stress
    raw_lst = float(features.get("lst_summer_max_c", 38.0))
    # 30°C -> 0.0, 48°C -> 1.0
    norm_lst = max(0.0, min(1.0, (raw_lst - 30.0) / 18.0))

    raw_ndvi = float(features.get("ndvi_summer", 0.35))
    # Lower NDVI = less evapotranspiration cooling = higher stress
    norm_ndvi = max(0.0, min(1.0, 1.0 - raw_ndvi))

    raw_deficit = float(features.get("rainfall_deficit_pct", 10.0))
    # 0% deficit -> 0.0, >= 30% deficit -> 1.0
    norm_deficit = max(0.0, min(1.0, raw_deficit / 30.0))

    raw_gw = float(features.get("groundwater_depth_m", 12.0))
    # 3m depth -> 0.0, 25m depth -> 1.0
    norm_gw = max(0.0, min(1.0, max(0.0, raw_gw - 3.0) / 22.0))

    raw_dist_water = float(features.get("distance_to_perennial_water_m", 1000.0))
    # 0m -> 0.0, 4000m -> 1.0
    norm_dist_water = max(0.0, min(1.0, raw_dist_water / 4000.0))

    raw_pop_density = float(features.get("population_density_per_km2", 150.0))
    # 0 -> 0.0, 500 -> 1.0
    norm_pop = max(0.0, min(1.0, raw_pop_density / 500.0))

    normalized_map = {
        "lst_summer_max": norm_lst,
        "ndvi_summer": norm_ndvi,
        "rainfall_deficit": norm_deficit,
        "groundwater_depth": norm_gw,
        "distance_to_perennial_water": norm_dist_water,
        "population_density": norm_pop,
    }

    # 2. Weighted summation
    drivers: list[Driver] = []
    total_score = 0.0

    for factor_name, factor_cfg in weights_spec.items():
        w = float(factor_cfg.get("weight", 0.0))
        val = normalized_map.get(factor_name, 0.5)
        contrib = round(val * w * 100.0, 2)
        total_score += contrib
        drivers.append(Driver(factor=factor_name, weight=w, contribution=contrib))

    final_val = round(max(0.0, min(100.0, total_score)), 1)

    # 3. Classification tier
    tiers = cfg.get("classification", {}).get("heat_water_stress", {})
    if final_val >= tiers.get("critical", [75, 100])[0]:
        s_class = ScoreClass.CRITICAL
    elif final_val >= tiers.get("high", [50, 75])[0]:
        s_class = ScoreClass.HIGH
    elif final_val >= tiers.get("moderate", [25, 50])[0]:
        s_class = ScoreClass.MODERATE
    else:
        s_class = ScoreClass.LOW

    return ScoreResult(
        score_type="heat_water_stress",
        value=final_val,
        score_class=s_class,
        drivers=drivers,
        confidence=Confidence(level=ConfidenceLevel.HIGH, numeric=0.81),
        data_quality_note="Compound thermal and hydrological index from MODIS LST (1km), MODIS NDVI, and CHIRPS precipitation departure.",
        data_tag=data_tag,
    )
