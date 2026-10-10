"""
Bhujal — Climate Scenario and Sensitivity Simulator
====================================================
Simulates rainfall perturbations (-50% to +50%) and intervention uplifts
driven by config/scenario.yaml.
"""

from __future__ import annotations

from backend.models import (
    ScenarioResult,
    ScoreResult,
)
from scoring.base import (
    classify_score,
    get_scenario_config,
    get_weights_config,
)


def simulate_scenario(
    site_id: str,
    baseline_scores: list[ScoreResult],
    rainfall_fraction: float = 1.0,
    include_intervention: str | None = None,
) -> ScenarioResult:
    """
    Run a what-if rainfall scenario for a site.

    Adjusts baseline scores using linear sensitivity coefficients and adds
    post-intervention uplifts if an approved intervention is specified.
    """
    cfg = get_scenario_config()
    weights_cfg = get_weights_config()

    baseline_rainfall = float(cfg.get("baseline_monsoon_rainfall_mm", 1400.0))
    adjusted_rainfall = round(baseline_rainfall * rainfall_fraction, 1)

    sensitivities = cfg.get("sensitivities", {})
    uplifts_map = cfg.get("intervention_uplift", {})
    applied_uplifts = (
        uplifts_map.get(include_intervention, {}) if include_intervention else {}
    )

    notes: list[str] = []
    pct_change = round((rainfall_fraction - 1.0) * 100.0, 1)

    if pct_change != 0.0:
        notes.append(
            f"Monsoon rainfall scaled to {rainfall_fraction:.2f}x ({pct_change:+g}% anomaly)."
        )
    else:
        notes.append("Normal monsoon rainfall baseline (1.00x).")

    if include_intervention:
        notes.append(
            f"Simulating civil structure intervention: '{include_intervention}'."
        )

    adjusted_scores: list[ScoreResult] = []

    for score in baseline_scores:
        stype = score.score_type
        sens_entry = sensitivities.get(stype, {})
        coeff = float(sens_entry.get("rainfall_coefficient", 0.0))

        delta = coeff * (rainfall_fraction - 1.0)
        uplift = float(applied_uplifts.get(stype, 0.0))

        new_val = round(max(0.0, min(100.0, score.value + delta + uplift)), 1)
        new_class = classify_score(
            stype, new_val, weights_cfg.get("classification", {})
        )

        adj_score = ScoreResult(
            score_type=stype,
            value=new_val,
            score_class=new_class,
            drivers=score.drivers,
            confidence=score.confidence,
            data_quality_note=f"Adjusted from baseline {score.value} (delta: {delta:+.1f}, uplift: {uplift:+.1f})",
            data_tag=score.data_tag,
        )
        adjusted_scores.append(adj_score)

    return ScenarioResult(
        site_id=site_id,
        baseline_scores=baseline_scores,
        adjusted_scores=adjusted_scores,
        rainfall_mm_baseline=baseline_rainfall,
        rainfall_mm_adjusted=adjusted_rainfall,
        intervention_applied=include_intervention,
        notes=notes,
    )
