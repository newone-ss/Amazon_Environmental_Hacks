"""
Bhujal — Spring-Drying Risk Heuristic Engine
=============================================
Calculates heuristic springhead desiccation risk (0-100) using
deterministic morphometric and hydrological indicators from config/weights.yaml.
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


def calculate_spring_drying_index(
    features: dict[str, Any],
    has_spring: bool = True,
    data_tag: DataTag = DataTag.ILLUSTRATIVE,
) -> ScoreResult:
    """
    Calculate springhead drying risk index (0-100). Higher score indicates greater risk of baseflow cessation.

    Keys in features:
      - elevation_m: float (spring elevation in meters AMSL, e.g., 200 - 1200)
      - catchment_area_ha: float (contributing area upslope, e.g., 1.0 - 50.0)
      - forest_loss_pct: float (forest disturbance in catchment, e.g., 0.0 - 50.0)
      - geology: str (rock type permeability: charnockite, khondalite, granite, laterite, alluvium)
      - rainfall_trend_pct: float (30-year trend, e.g., -20.0 to +10.0)
      - slope_degrees: float (mean slope of the contributing catchment)
    """
    if not has_spring:
        # If no spring exists at the site, return zeroed index with explanatory note
        return ScoreResult(
            score_type="spring_drying_index",
            value=0.0,
            score_class=ScoreClass.LOW,
            drivers=[],
            confidence=Confidence(level=ConfidenceLevel.HIGH, numeric=1.0),
            data_quality_note="No perennial or seasonal springhead recorded in village catchment.",
            data_tag=data_tag,
        )

    cfg = load_weights_config()
    weights_spec = cfg.get("spring_drying_index", {}).get("factors", {})

    # 1. Normalize individual factors to [0.0, 1.0] where 1.0 = maximum drying risk
    raw_elev = float(features.get("elevation_m", 500.0))
    # Higher springs more vulnerable: 200m -> 0.0, 1000m -> 1.0
    norm_elev = max(0.0, min(1.0, (raw_elev - 200.0) / 800.0))

    raw_catchment = float(features.get("catchment_area_ha", 10.0))
    # Smaller catchment = less recharge volume = higher drying risk
    # 25 ha -> 0.0, <= 1 ha -> 1.0
    norm_catchment = max(0.0, min(1.0, 1.0 - (min(raw_catchment, 25.0) / 25.0)))

    raw_forest_loss = float(features.get("forest_loss_pct", 10.0))
    # Higher forest loss = reduced infiltration & baseflow = higher risk
    # 0% loss -> 0.0, >= 40% loss -> 1.0
    norm_forest_loss = max(0.0, min(1.0, raw_forest_loss / 40.0))

    # Geology permeability mapping to drying risk (lower permeability rock = higher risk of drying)
    geology_str = str(features.get("geology", "weathered_granite")).lower()
    geo_risk_map = {
        "alluvium": 0.2,
        "laterite": 0.35,
        "weathered_basalt": 0.45,
        "weathered_granite": 0.50,
        "khondalite": 0.65,
        "charnockite": 0.85,
    }
    norm_geology = geo_risk_map.get(geology_str, 0.50)

    # Rainfall trend: negative trend (declining monsoon) = higher risk
    raw_trend = float(features.get("rainfall_trend_pct", -5.0))
    # 0% or positive -> 0.0, -20% -> 1.0
    if raw_trend >= 0.0:
        norm_trend = 0.0
    else:
        norm_trend = max(0.0, min(1.0, abs(raw_trend) / 20.0))

    raw_slope = float(features.get("slope_degrees", 15.0))
    # Steeper slopes = faster flash runoff, less baseflow recharge = higher risk
    norm_slope = max(0.0, min(1.0, raw_slope / 35.0))

    normalized_map = {
        "spring_elevation": norm_elev,
        "catchment_area": norm_catchment,
        "forest_cover_change": norm_forest_loss,
        "geology_permeability": norm_geology,
        "rainfall_trend": norm_trend,
        "slope_of_catchment": norm_slope,
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
    tiers = cfg.get("classification", {}).get("spring_drying_index", {})
    if final_val >= tiers.get("very_high", [75, 100])[0]:
        s_class = ScoreClass.VERY_HIGH
    elif final_val >= tiers.get("high", [50, 75])[0]:
        s_class = ScoreClass.HIGH
    elif final_val >= tiers.get("moderate", [25, 50])[0]:
        s_class = ScoreClass.MODERATE
    else:
        s_class = ScoreClass.LOW

    return ScoreResult(
        score_type="spring_drying_index",
        value=final_val,
        score_class=s_class,
        drivers=drivers,
        confidence=Confidence(level=ConfidenceLevel.MEDIUM, numeric=0.68),
        data_quality_note="Heuristic morphometric vulnerability derived from Hansen Forest Change, DEM catchment delineation, and CHIRPS rainfall trends.",
        data_tag=data_tag,
    )
