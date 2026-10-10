"""
Bhujal — Groundwater Recharge Scoring Engine
=============================================
Calculates multi-criteria recharge suitability (0-100) using
deterministic weighted overlays driven by config/weights.yaml.
"""

from __future__ import annotations

from typing import Any

from backend.models import (
    ConfidenceLevel,
    DataTag,
    ScoreResult,
)
from scoring.base import (
    build_score_result,
    clamp,
    compute_weighted_score,
    get_weights_config,
    normalize_linear,
)


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
    cfg = get_weights_config()
    weights_spec = cfg.get("recharge_score", {}).get("factors", {})

    # Normalize individual factors to [0.0, 1.0]
    raw_slope = float(features.get("slope_degrees", 10.0))
    norm_slope = normalize_linear(raw_slope, 0.0, 35.0, inverse=True)

    norm_soil = clamp(float(features.get("soil_permeability", 0.5)))
    norm_rain = clamp(float(features.get("rainfall_intensity", 0.6)))
    norm_lulc = clamp(float(features.get("lulc_perviousness", 0.7)))
    norm_lineament = clamp(float(features.get("lineament_density", 0.5)))

    raw_drainage = float(features.get("drainage_density", 0.5))
    norm_drainage = normalize_linear(raw_drainage, 0.0, 1.0, inverse=True)

    normalized_map = {
        "slope": norm_slope,
        "soil_permeability": norm_soil,
        "rainfall_intensity": norm_rain,
        "lulc_perviousness": norm_lulc,
        "lineament_density": norm_lineament,
        "drainage_density": norm_drainage,
    }

    score_val, drivers = compute_weighted_score(normalized_map, weights_spec)

    return build_score_result(
        score_type="recharge_score",
        value=score_val,
        drivers=drivers,
        confidence_level=ConfidenceLevel.MEDIUM,
        confidence_numeric=0.72,
        data_quality_note=(
            "Multi-criteria overlay derived from SRTM 30m DEM, "
            "SoilGrids 250m, and CHIRPS precipitation."
        ),
        data_tag=data_tag,
    )
