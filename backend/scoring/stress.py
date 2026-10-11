"""
Bhujal — Heat-Water Stress Scoring Engine
==========================================
Calculates compound heat and water vulnerability (0-100) using
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
    compute_weighted_score,
    get_weights_config,
    normalize_linear,
)


def calculate_heat_water_stress(
    features: dict[str, Any],
    data_tag: DataTag = DataTag.ILLUSTRATIVE,
    field_provenance: dict[str, str] | None = None,
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
    cfg = get_weights_config()
    weights_spec = cfg.get("heat_water_stress", {}).get("factors", {})

    # Normalize individual factors to [0.0, 1.0] where 1.0 = maximum stress
    raw_lst = float(features.get("lst_summer_max_c", 38.0))
    norm_lst = normalize_linear(raw_lst, 30.0, 48.0)

    raw_ndvi = float(features.get("ndvi_summer", 0.35))
    norm_ndvi = normalize_linear(raw_ndvi, 0.0, 1.0, inverse=True)

    raw_deficit = float(features.get("rainfall_deficit_pct", 10.0))
    norm_deficit = normalize_linear(raw_deficit, 0.0, 30.0)

    raw_gw = float(features.get("groundwater_depth_m", 12.0))
    norm_gw = normalize_linear(raw_gw, 3.0, 25.0)

    raw_dist_water = float(features.get("distance_to_perennial_water_m", 1000.0))
    norm_dist_water = normalize_linear(raw_dist_water, 0.0, 4000.0)

    raw_pop_density = float(features.get("population_density_per_km2", 150.0))
    norm_pop = normalize_linear(raw_pop_density, 0.0, 500.0)

    normalized_map = {
        "lst_summer_max": norm_lst,
        "ndvi_summer": norm_ndvi,
        "rainfall_deficit": norm_deficit,
        "groundwater_depth": norm_gw,
        "distance_to_perennial_water": norm_dist_water,
        "population_density": norm_pop,
    }

    score_val, drivers = compute_weighted_score(normalized_map, weights_spec)

    # Compute confidence based on field provenance
    if field_provenance is None:
        # Fallback to original confidence and note
        confidence_level = ConfidenceLevel.HIGH
        confidence_numeric = 0.81
        data_quality_note = (
            "Compound thermal and hydrological index from MODIS LST (1km), "
            "MODIS NDVI, and CHIRPS precipitation departure."
        )
    else:
        # Fields used in heat_water_stress score
        used_fields = [
            "lst_summer_max_c",
            "ndvi_summer",
            "rainfall_deficit_pct",
            "groundwater_depth_m",
            "distance_to_perennial_water_m",
            "population_density_per_km2",
        ]
        derived_count = 0
        for field in used_fields:
            prov = field_provenance.get(field, "unknown")
            if prov == "derived":
                derived_count += 1
        non_derived_count = len(used_fields) - derived_count
        # Base confidence 0.81, penalize 0.1 for each non-derived field
        confidence_numeric = 0.81 - (0.1 * non_derived_count)
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
            f"Compound thermal and hydrological index from MODIS LST (1km), "
            f"MODIS NDVI, and CHIRPS precipitation departure. "
            f"Field provenance: {derived_count}/{len(used_fields)} derived, "
            f"{non_derived_count} curated/assumed."
        )

    return build_score_result(
        score_type="heat_water_stress",
        value=score_val,
        drivers=drivers,
        confidence_level=confidence_level,
        confidence_numeric=confidence_numeric,
        data_quality_note=data_quality_note,
        data_tag=data_tag,
    )
