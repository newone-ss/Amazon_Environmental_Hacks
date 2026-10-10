"""
Bhujal — Base Scoring Module
=============================
Shared utilities for all deterministic scoring engines:
- Config caching
- Normalization helpers
- Classification logic
- Validation and error handling
"""

from __future__ import annotations

import functools
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


@functools.lru_cache(maxsize=4)
def _load_yaml_config(filename: str) -> dict[str, Any]:
    """Load and cache YAML config files."""
    path = CONFIG_DIR / filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        raise RuntimeError(f"Configuration file not found: {path}")
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Invalid YAML in {path}: {exc}")


def get_weights_config() -> dict[str, Any]:
    return _load_yaml_config("weights.yaml")


def get_safety_config() -> dict[str, Any]:
    return _load_yaml_config("safety_rules.yaml")


def get_interventions_config() -> dict[str, Any]:
    return _load_yaml_config("interventions.yaml")


def get_costs_config() -> dict[str, Any]:
    return _load_yaml_config("costs.yaml")


def get_scenario_config() -> dict[str, Any]:
    return _load_yaml_config("scenario.yaml")


def get_demo_sites_config() -> dict[str, Any]:
    return _load_yaml_config("demo_sites.yaml")


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a value to the specified range."""
    return max(min_val, min(max_val, value))


def normalize_linear(
    value: float,
    in_min: float,
    in_max: float,
    out_min: float = 0.0,
    out_max: float = 1.0,
    inverse: bool = False,
) -> float:
    """
    Normalize value from [in_min, in_max] to [out_min, out_max].

    If inverse=True, higher input maps to lower output.
    """
    if in_max == in_min:
        return out_min
    normalized = (value - in_min) / (in_max - in_min)
    normalized = clamp(normalized)
    if inverse:
        normalized = 1.0 - normalized
    return out_min + normalized * (out_max - out_min)


def compute_weighted_score(
    normalized_factors: dict[str, float],
    weights_spec: dict[str, dict[str, Any]],
) -> tuple[float, list[Driver]]:
    """
    Compute weighted score and driver breakdown.

    Returns:
        (total_score_0_to_100, list_of_drivers)
    """
    drivers: list[Driver] = []
    total_score = 0.0

    for factor_name, factor_cfg in weights_spec.items():
        weight = float(factor_cfg.get("weight", 0.0))
        val = normalized_factors.get(factor_name, 0.5)
        contrib = round(val * weight * 100.0, 2)
        total_score += contrib
        drivers.append(Driver(factor=factor_name, weight=weight, contribution=contrib))

    final_score = round(clamp(total_score, 0.0, 100.0), 1)
    return final_score, drivers


def classify_score(
    score_type: str,
    value: float,
    classification_config: dict[str, Any] | None = None,
) -> ScoreClass:
    """
    Classify a 0-100 score into its tier using weights.yaml classification thresholds.

    Falls back to generic thresholds if score_type not found.
    """
    if classification_config is None:
        classification_config = get_weights_config().get("classification", {})

    tiers = classification_config.get(score_type, {})

    if score_type == "recharge_score":
        if value >= tiers.get("excellent", [75, 100])[0]:
            return ScoreClass.EXCELLENT
        if value >= tiers.get("good", [50, 75])[0]:
            return ScoreClass.GOOD
        if value >= tiers.get("moderate", [25, 50])[0]:
            return ScoreClass.MODERATE
        return ScoreClass.POOR

    elif score_type == "heat_water_stress":
        if value >= tiers.get("critical", [75, 100])[0]:
            return ScoreClass.CRITICAL
        if value >= tiers.get("high", [50, 75])[0]:
            return ScoreClass.HIGH
        if value >= tiers.get("moderate", [25, 50])[0]:
            return ScoreClass.MODERATE
        return ScoreClass.LOW

    elif score_type == "spring_drying_index":
        if value >= tiers.get("very_high", [75, 100])[0]:
            return ScoreClass.VERY_HIGH
        if value >= tiers.get("high", [50, 75])[0]:
            return ScoreClass.HIGH
        if value >= tiers.get("moderate", [25, 50])[0]:
            return ScoreClass.MODERATE
        return ScoreClass.LOW

    # Generic fallback
    if value >= 75:
        return ScoreClass.EXCELLENT
    if value >= 50:
        return ScoreClass.GOOD
    if value >= 25:
        return ScoreClass.MODERATE
    return ScoreClass.POOR


def build_score_result(
    score_type: str,
    value: float,
    drivers: list[Driver],
    confidence_level: ConfidenceLevel,
    confidence_numeric: float,
    data_quality_note: str,
    data_tag: DataTag,
) -> ScoreResult:
    """Construct a standardized ScoreResult with classification."""
    score_class = classify_score(score_type, value)
    return ScoreResult(
        score_type=score_type,
        value=value,
        score_class=score_class,
        drivers=drivers,
        confidence=Confidence(level=confidence_level, numeric=confidence_numeric),
        data_quality_note=data_quality_note,
        data_tag=data_tag,
    )


class ScoringError(Exception):
    """Base exception for scoring errors."""


class ConfigError(ScoringError):
    """Configuration loading or validation error."""


class FeatureError(ScoringError):
    """Missing or invalid feature data error."""
