"""
Bhujal — Spring-Drying Risk Heuristic Engine
=============================================
Calculates heuristic springhead desiccation risk (0-100) using
deterministic morphometric and hydrological indicators from config/weights.yaml.
"""

from __future__ import annotations

from typing import Any

from backend.models import (
    Confidence,
    ConfidenceLevel,
    DataTag,
    ScoreClass,
    ScoreResult,
)
from scoring.base import (
    build_score_result,
    compute_weighted_score,
    get_weights_config,
    normalize_linear,
)

_GEOLOGY_RISK_MAP: dict[str, float] = {
    "alluvium": 0.20,
    "laterite": 0.35,
    "weathered_basalt": 0.45,
    "weathered_granite": 0.50,
    "khondalite": 0.65,
    "charnockite": 0.85,
}


def calculate_spring_drying_index(
    features: dict[str, Any],
    has_spring: bool = True,
    data_tag: DataTag = DataTag.ILLUSTRATIVE,
    field_provenance: dict[str, str] | None = None,
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
        return ScoreResult(
            score_type="spring_drying_index",
            value=0.0,
            score_class=ScoreClass.LOW,
            drivers=[],
            confidence=Confidence(level=ConfidenceLevel.HIGH, numeric=1.0),
            data_quality_note="No perennial or seasonal springhead recorded in village catchment.",
            data_tag=data_tag,
        )

    cfg = get_weights_config()
    weights_spec = cfg.get("spring_drying_index", {}).get("factors", {})

    raw_elev = float(features.get("elevation_m", 500.0))
    norm_elev = normalize_linear(raw_elev, 200.0, 1000.0)

    raw_catchment = float(features.get("catchment_area_ha", 10.0))
    norm_catchment = normalize_linear(raw_catchment, 1.0, 25.0, inverse=True)

    raw_forest_loss = float(features.get("forest_loss_pct", 10.0))
    norm_forest_loss = normalize_linear(raw_forest_loss, 0.0, 40.0)

    geology_str = str(features.get("geology", "weathered_granite")).lower()
    norm_geology = _GEOLOGY_RISK_MAP.get(geology_str, 0.50)

    raw_trend = float(features.get("rainfall_trend_pct", -5.0))
    if raw_trend >= 0.0:
        norm_trend = 0.0
    else:
        norm_trend = normalize_linear(abs(raw_trend), 0.0, 20.0)

    raw_slope = float(features.get("slope_degrees", 15.0))
    norm_slope = normalize_linear(raw_slope, 0.0, 35.0)

    normalized_map = {
        "spring_elevation": norm_elev,
        "catchment_area": norm_catchment,
        "forest_cover_change": norm_forest_loss,
        "geology_permeability": norm_geology,
        "rainfall_trend": norm_trend,
        "slope_of_catchment": norm_slope,
    }

    score_val, drivers = compute_weighted_score(normalized_map, weights_spec)

    # Compute confidence based on field provenance
    if field_provenance is None:
        # Fallback to original confidence and note
        confidence_level = ConfidenceLevel.MEDIUM
        confidence_numeric = 0.68
        data_quality_note = (
            "Heuristic morphometric vulnerability derived from Hansen Forest Change, "
            "DEM catchment delineation, and CHIRPS rainfall trends."
        )
    else:
        # Fields used in spring_drying_index score
        used_fields = [
            "elevation_m",
            "catchment_area_ha",
            "forest_loss_pct",
            "geology",
            "rainfall_trend_pct",
            "slope_degrees",
        ]
        derived_count = 0
        for field in used_fields:
            prov = field_provenance.get(field, "unknown")
            if prov == "derived":
                derived_count += 1
        non_derived_count = len(used_fields) - derived_count
        # Base confidence 0.68, penalize 0.1 for each non-derived field
        confidence_numeric = 0.68 - (0.1 * non_derived_count)
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
            f"Heuristic morphometric vulnerability derived from Hansen Forest Change, "
            f"DEM catchment delineation, and CHIRPS rainfall trends. "
            f"Field provenance: {derived_count}/{len(used_fields)} derived, "
            f"{non_derived_count} curated/assumed."
        )

    return build_score_result(
        score_type="spring_drying_index",
        value=score_val,
        drivers=drivers,
        confidence_level=confidence_level,
        confidence_numeric=confidence_numeric,
        data_quality_note=data_quality_note,
        data_tag=data_tag,
    )
