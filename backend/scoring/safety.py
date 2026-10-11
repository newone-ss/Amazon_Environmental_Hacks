"""
Bhujal — Geotechnical Safety Veto Engine
=======================================
Evaluates deterministic safety constraints driven by config/safety_rules.yaml.
Any REJECTED rule immediately vetoes civil intervention clearances.
"""

from __future__ import annotations

import logging
from typing import Any

from scoring.base import get_safety_config

from backend.models import (
    SafetyRuleResult,
    SafetyStatus,
    SafetyVerdict,
)

logger = logging.getLogger(__name__)

_REQUIRED_FEATURES = {
    "slope_degrees": (float, (0.0, 90.0)),
    "landslide_susceptibility": (str, ("low", "moderate", "high", "very_high")),
    "seismic_zone": (int, (1, 5)),
    "distance_to_river_m": (float, (0.0, None)),
    "elevation_above_river_m": (float, (0.0, None)),
    "protected_area_type": (str, None),  # Optional
    "soil_type": (str, None),
}


def _validate_features(features: dict[str, Any]) -> dict[str, Any]:
    """Validate and coerce safety rule features with defaults for missing keys."""
    validated = {}
    for key, (expected_type, valid_range) in _REQUIRED_FEATURES.items():
        if key not in features:
            logger.debug("Safety feature '%s' missing, using default", key)
            if key == "slope_degrees":
                validated[key] = 0.0
            elif key == "landslide_susceptibility":
                validated[key] = "low"
            elif key == "seismic_zone":
                validated[key] = 2
            elif key == "distance_to_river_m":
                validated[key] = 1000.0
            elif key == "elevation_above_river_m":
                validated[key] = 50.0
            elif key == "protected_area_type":
                validated[key] = None
            elif key == "soil_type":
                validated[key] = "loam"
            continue

        value = features[key]
        try:
            if expected_type == float:
                validated[key] = float(value)
            elif expected_type == int:
                validated[key] = int(value)
            elif expected_type == str:
                if value is None:
                    validated[key] = None
                else:
                    validated[key] = str(value).strip().lower()
        except (ValueError, TypeError) as exc:
            logger.warning(
                "Invalid value for safety feature '%s': %s. Using default.", key, exc
            )
            if key == "slope_degrees":
                validated[key] = 0.0
            elif key == "landslide_susceptibility":
                validated[key] = "low"
            elif key == "seismic_zone":
                validated[key] = 2
            elif key == "distance_to_river_m":
                validated[key] = 1000.0
            elif key == "elevation_above_river_m":
                validated[key] = 50.0
            elif key == "protected_area_type":
                validated[key] = None
            elif key == "soil_type":
                validated[key] = "loam"
            continue

        # Range validation
        if valid_range and expected_type in (float, int):
            min_val, max_val = valid_range
            if min_val is not None and validated[key] < min_val:
                logger.warning(
                    "Safety feature '%s' value %s below minimum %s. Clamping.",
                    key,
                    validated[key],
                    min_val,
                )
                validated[key] = min_val
            if max_val is not None and validated[key] > max_val:
                logger.warning(
                    "Safety feature '%s' value %s above maximum %s. Clamping.",
                    key,
                    validated[key],
                    max_val,
                )
                validated[key] = max_val

    return validated


def evaluate_safety_rules(features: dict[str, Any]) -> SafetyVerdict:
    """
    Evaluate deterministic geotechnical and environmental veto rules for a site.

    Keys evaluated:
      - slope_degrees: float
      - landslide_susceptibility: str ('low', 'moderate', 'high', 'very_high')
      - seismic_zone: int (1 - 5)
      - distance_to_river_m: float
      - elevation_above_river_m: float
      - protected_area_type: str | None
      - soil_type: str
    """
    # Validate and coerce features
    features = _validate_features(features)

    cfg = get_safety_config()
    rule_definitions = cfg.get("rules", [])

    rules_evaluated: list[SafetyRuleResult] = []
    triggered_reject_ids: list[str] = []
    triggered_reject_reasons: list[str] = []
    triggered_conditional_ids: list[str] = []
    triggered_conditional_reasons: list[str] = []

    slope = features.get("slope_degrees", 0.0)
    landslide = features.get("landslide_susceptibility", "low")
    seismic = features.get("seismic_zone", 2)
    dist_river = features.get("distance_to_river_m", 1000.0)
    elev_river = features.get("elevation_above_river_m", 50.0)
    protected_area = features.get("protected_area_type")
    soil_type = features.get("soil_type", "loam")

    for rule in rule_definitions:
        r_id = rule.get("id", "UNKNOWN")
        verdict_str = rule.get("verdict", "CONDITIONAL").upper()
        verdict = SafetyStatus(verdict_str)
        triggered = False
        reason = ""

        if r_id == "SLOPE_STEEP":
            thresh = float(rule.get("threshold", 35))
            if slope > thresh:
                triggered = True
                reason = f"Slope of {slope:.1f}° exceeds the {thresh}° safety limit for earthwork structures."

        elif r_id == "LANDSLIDE_ZONE":
            if landslide in ("high", "very_high"):
                triggered = True
                reason = f"Site is in a {landslide} landslide susceptibility zone."

        elif r_id == "SEISMIC_HIGH":
            thresh = int(rule.get("threshold", 4))
            if seismic >= thresh:
                triggered = True
                reason = f"Seismic zone {seismic} requires earthquake-resistant design."

        elif r_id == "FLOOD_ZONE":
            d_thresh = float(rule.get("threshold", 200))
            e_thresh = float(rule.get("elev_threshold", 5))
            if dist_river < d_thresh and elev_river < e_thresh:
                triggered = True
                reason = (
                    f"Site is {dist_river:.1f}m from active river channel "
                    f"and only {elev_river:.1f}m above riverbed."
                )

        elif r_id == "FOREST_PROTECTED":
            if protected_area and str(protected_area).strip():
                triggered = True
                reason = (
                    f"Site is inside protected conservation boundary ({protected_area}): "
                    "construction prohibited without clearance."
                )

        elif r_id == "SOIL_UNSTABLE":
            if soil_type in ("expansive_clay", "peat", "organic"):
                triggered = True
                reason = (
                    f"Soil type '{soil_type}' requires engineering stabilization "
                    "before civil construction."
                )

        elif r_id == "SLOPE_MODERATE":
            thresh = float(rule.get("threshold", 20))
            if thresh < slope <= 35:
                triggered = True
                reason = (
                    f"Slope of {slope:.1f}° requires terracing, berms, "
                    "and reinforced retaining walls."
                )

        rule_result = SafetyRuleResult(
            rule_id=r_id,
            triggered=triggered,
            verdict=verdict if triggered else SafetyStatus.SAFE,
            reason=reason,
        )
        rules_evaluated.append(rule_result)

        if triggered:
            if verdict == SafetyStatus.REJECTED:
                triggered_reject_ids.append(r_id)
                triggered_reject_reasons.append(reason)
            elif verdict == SafetyStatus.CONDITIONAL:
                triggered_conditional_ids.append(r_id)
                triggered_conditional_reasons.append(reason)

    if triggered_reject_ids:
        final_status = SafetyStatus.REJECTED
        active_ids = triggered_reject_ids
        active_reasons = triggered_reject_reasons
    elif triggered_conditional_ids:
        final_status = SafetyStatus.CONDITIONAL
        active_ids = triggered_conditional_ids
        active_reasons = triggered_conditional_reasons
    else:
        final_status = SafetyStatus.SAFE
        active_ids = []
        active_reasons = [
            "Site cleared: all geotechnical and environmental safety checks passed."
        ]

    return SafetyVerdict(
        status=final_status,
        rule_ids=active_ids,
        reasons=active_reasons,
        rules_evaluated=rules_evaluated,
    )
