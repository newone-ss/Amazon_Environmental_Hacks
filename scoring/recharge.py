"""
Bhujal — Groundwater Recharge Scoring Engine
=============================================
Calculates multi-criteria recharge suitability (0-100) using
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


def calculate_recharge_score(
    features: dict[str, Any],
    data_tag: DataTag = DataTag.ILLUSTRATIVE,
) -> ScoreResult:
    """
    Calculate deterministic recharge suitability score from terrain and climatic features.

    Required/optional keys in features:
      - slope_degrees: float (0 - 90)
      - soil_permeability: float (0.0 - 1.0)
      - rainfall_intensity: float (0.0 - 1.0)
      - lulc_perviousness: float (0.0 - 1.0)
      - lineament_density: float (0.0 - 1.0)
      - drainage_density: float (0.0 - 1.0)
    """
    cfg = load_weights_config()
    weights_spec = cfg.get("recharge_score", {}).get("factors", {})

    # 1. Normalize individual factors to [0.0, 1.0]
    raw_slope = float(features.get("slope_degrees", 10.0))
    # Flatter slopes favor infiltration: 0 deg -> 1.0, >= 35 deg -> 0.0
    norm_slope = max(0.0, min(1.0, 1.0 - (raw_slope / 35.0)))

    norm_soil = max(0.0, min(1.0, float(features.get("soil_permeability", 0.5))))
    norm_rain = max(0.0, min(1.0, float(features.get("rainfall_intensity", 0.6))))
    norm_lulc = max(0.0, min(1.0, float(features.get("lulc_perviousness", 0.7))))
    norm_lineament = max(0.0, min(1.0, float(features.get("lineament_density", 0.5))))

    raw_drainage = float(features.get("drainage_density", 0.5))
    # Lower drainage density favors longer infiltration opportunity
    norm_drainage = max(0.0, min(1.0, 1.0 - raw_drainage))

    normalized_map = {
        "slope": norm_slope,
        "soil_permeability": norm_soil,
        "rainfall_intensity": norm_rain,
        "lulc_perviousness": norm_lulc,
        "lineament_density": norm_lineament,
        "drainage_density": norm_drainage,
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
    tiers = cfg.get("classification", {}).get("recharge_score", {})
    if final_val >= tiers.get("excellent", [75, 100])[0]:
        s_class = ScoreClass.EXCELLENT
    elif final_val >= tiers.get("good", [50, 75])[0]:
        s_class = ScoreClass.GOOD
    elif final_val >= tiers.get("moderate", [25, 50])[0]:
        s_class = ScoreClass.MODERATE
    else:
        s_class = ScoreClass.POOR

    return ScoreResult(
        score_type="recharge_score",
        value=final_val,
        score_class=s_class,
        drivers=drivers,
        confidence=Confidence(level=ConfidenceLevel.MEDIUM, numeric=0.72),
        data_quality_note="Multi-criteria overlay derived from SRTM 30m DEM, SoilGrids 250m, and CHIRPS precipitation.",
        data_tag=data_tag,
    )
