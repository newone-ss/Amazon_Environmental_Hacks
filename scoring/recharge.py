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
    field_provenance: dict[str, str] | None = None,
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

    # Compute confidence based on field provenance
    if field_provenance is None:
        # Fallback to original confidence and note
        confidence_level = ConfidenceLevel.MEDIUM
        confidence_numeric = 0.72
        data_quality_note = (
            "Multi-criteria overlay derived from SRTM 30m DEM, "
            "SoilGrids 250m, and CHIRPS precipitation."
        )
    else:
        # Fields used in recharge score
        used_fields = [
            "slope_degrees",
            "soil_permeability",
            "rainfall_intensity",
            "lulc_perviousness",
            "lineament_density",
            "drainage_density",
        ]
        derived_count = 0
        for field in used_fields:
            prov = field_provenance.get(field, "unknown")
            if prov == "derived":
                derived_count += 1
        non_derived_count = len(used_fields) - derived_count
        # Base confidence 0.72, penalize 0.1 for each non-derived field
        confidence_numeric = 0.72 - (0.1 * non_derived_count)
        confidence_numeric = max(0.0, min(1.0, confidence_numeric))  # clamp
        # Determine confidence level
        if confidence_numeric >= 0.8:
            confidence_level = ConfidenceLevel.HIGH
        elif confidence_numeric >= 0.5:
            confidence_level = ConfidenceLevel.MEDIUM
        else:
            confidence_level = ConfidenceLevel.LOW
        # Update data quality note with provenance info
        data_quality_note = (
            f"Multi-criteria overlay derived from SRTM 30m DEM, "
            f"SoilGrids 250m, and CHIRPS precipitation. "
            f"Field provenance: {derived_count}/{len(used_fields)} derived, "
            f"{non_derived_count} curated/assumed."
        )

    return build_score_result(
        score_type="recharge_score",
        value=score_val,
        drivers=drivers,
        confidence_level=confidence_level,
        confidence_numeric=confidence_numeric,
        data_quality_note=data_quality_note,
        data_tag=data_tag,
    )
