"""
Bhujal — Civil Engineering Intervention Composer and Costing Engine
=====================================================================
Matches site terrain and hydrogeological properties against config/interventions.yaml
and estimates indicative MGNREGA cost bounds from config/costs.yaml.
"""

from __future__ import annotations

from typing import Any

from backend.models import Recommendation
from scoring.base import (
    get_costs_config,
    get_interventions_config,
)


def compose_recommendations(
    features: dict[str, Any],
    has_spring: bool = False,
    is_rejected: bool = False,
    state: str = "Odisha",
) -> list[Recommendation]:
    """
    Evaluate site parameters against candidate interventions and return matched recommendations.

    If is_rejected is True (e.g. slope > 35° or landslide zone), returns empty recommendations
    because civil structures cannot safely be constructed.
    """
    if is_rejected:
        return []

    int_cfg = get_interventions_config()
    cost_cfg = get_costs_config()

    candidates = int_cfg.get("interventions", [])
    cost_tables = cost_cfg.get("intervention_costs", {})
    labour_rates = cost_cfg.get("labour_rates_by_state", {})
    default_labour_rate = cost_cfg.get("labour_rate_inr_per_day", 350)
    labour_rate = labour_rates.get(
        state, labour_rates.get("All-India", default_labour_rate)
    )

    slope = float(features.get("slope_degrees", 10.0))
    catchment = float(features.get("catchment_area_ha", 10.0))
    stream_order = int(features.get("stream_order", 2))
    soil_type = str(features.get("soil_type", "loam")).lower()
    geology = str(features.get("geology", "weathered_granite")).lower()
    is_settlement = bool(features.get("settlement", False))
    lulc_class = str(features.get("lulc_class", "forest")).lower()
    stream_bed = str(features.get("stream_bed_material", "gravelly")).lower()

    recommendations: list[Recommendation] = []

    for item in candidates:
        i_id = item["id"]
        suit = item.get("suitability", {})
        matched = True
        match_score = 0.5
        assumptions: list[str] = []

        # Check slope bounds
        min_slope = suit.get("min_slope_deg")
        max_slope = suit.get("max_slope_deg")
        if min_slope is not None and slope < min_slope:
            matched = False
        if max_slope is not None and slope > max_slope:
            matched = False
        if matched and min_slope is not None and max_slope is not None:
            mid_slope = (min_slope + max_slope) / 2.0
            diff = abs(slope - mid_slope) / (max_slope - min_slope + 1e-5)
            match_score += max(0.0, 0.3 * (1.0 - diff))
            assumptions.append(
                f"Slope ({slope:.1f}°) satisfies bounds [{min_slope}°, {max_slope}°]."
            )

        # Check catchment area
        min_catchment = suit.get("min_catchment_area_ha")
        if min_catchment is not None:
            if catchment < min_catchment:
                matched = False
            else:
                match_score += 0.1
                assumptions.append(
                    f"Catchment area ({catchment:.1f} ha) meets minimum {min_catchment} ha."
                )

        # Check stream order
        max_order = suit.get("max_stream_order")
        if max_order is not None:
            if stream_order > max_order:
                matched = False
            else:
                assumptions.append(
                    f"Stream order ({stream_order}) does not exceed maximum {max_order}."
                )

        # Check soil types
        req_soils = suit.get("soil_types")
        if req_soils is not None:
            req_soils_lower = [s.lower() for s in req_soils]
            if soil_type not in req_soils_lower:
                matched = False
            else:
                match_score += 0.1
                assumptions.append(f"Soil type '{soil_type}' is compatible.")

        # Check geology
        req_geology = suit.get("geology")
        if req_geology is not None:
            req_geology_lower = [g.lower() for g in req_geology]
            if geology not in req_geology_lower:
                matched = False
            else:
                match_score += 0.1
                assumptions.append(f"Underlying lithology '{geology}' is permeable.")

        # Check spring requirement
        if suit.get("has_spring", False) and not has_spring:
            matched = False

        # Check settlement requirement (e.g. rooftop RWH)
        if suit.get("settlement", False) and not is_settlement:
            matched = False

        # Check land use (e.g. farm pond)
        req_lu = suit.get("land_use")
        if req_lu is not None:
            req_lu_lower = [lu.lower() for lu in req_lu]
            if lulc_class not in req_lu_lower:
                matched = False
            else:
                assumptions.append(
                    f"Land use '{lulc_class}' compatible with pond excavation."
                )

        # Check stream bed material (e.g. gabions)
        req_bed = suit.get("stream_bed_material")
        if req_bed is not None:
            req_bed_lower = [b.lower() for b in req_bed]
            if stream_bed not in req_bed_lower:
                matched = False
            else:
                assumptions.append(
                    f"Stream bed '{stream_bed}' provides stable foundation for gabions."
                )

        if matched:
            cost_info = cost_tables.get(i_id, {"low": 100000, "high": 300000})
            cost_range = {
                "low": int(cost_info.get("low", 100000)),
                "high": int(cost_info.get("high", 300000)),
            }

            rec_assumptions = (
                list(assumptions)
                if assumptions
                else [f"Design calibrated for {item['name']}"]
            )
            rec_assumptions.append(
                f"Labour costing reflects {state} MGNREGA wage benchmark (INR {labour_rate}/person-day)."
            )

            rec = Recommendation(
                intervention_id=i_id,
                intervention_name=item["name"],
                category=item["category"],
                dimensions=item.get("default_dimensions", {}),
                materials=item.get("materials", []),
                labour_days=int(item.get("labour_days", 30)),
                cost_range_inr=cost_range,
                assumptions=rec_assumptions,
                suitability_score=round(min(1.0, match_score), 2),
            )
            recommendations.append(rec)

    recommendations.sort(key=lambda r: r.suitability_score, reverse=True)
    return recommendations
