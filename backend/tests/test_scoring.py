"""
Unit tests for deterministic scoring modules, safety veto rules,
intervention matching, and scenario simulation.
"""

from __future__ import annotations

import pytest
from scoring import (
    calculate_heat_water_stress,
    calculate_recharge_score,
    calculate_spring_drying_index,
    compose_recommendations,
    evaluate_safety_rules,
    evaluate_site,
    simulate_scenario,
)

from backend.models import (
    SafetyStatus,
    ScoreClass,
)


class TestRechargeScoring:
    def test_recharge_score_bounds(self) -> None:
        features = {
            "slope_degrees": 5.0,
            "soil_permeability": 0.8,
            "rainfall_intensity": 0.7,
            "lulc_perviousness": 0.85,
            "lineament_density": 0.6,
            "drainage_density": 0.3,
        }
        res = calculate_recharge_score(features)
        assert 0.0 <= res.value <= 100.0
        assert res.score_type == "recharge_score"
        assert res.score_class in [
            ScoreClass.EXCELLENT,
            ScoreClass.GOOD,
            ScoreClass.MODERATE,
            ScoreClass.POOR,
        ]
        assert len(res.drivers) == 6
        assert sum(d.weight for d in res.drivers) == pytest.approx(1.0, abs=1e-4)

    def test_slope_monotonicity(self) -> None:
        flat_features = {"slope_degrees": 2.0, "soil_permeability": 0.7}
        steep_features = {"slope_degrees": 30.0, "soil_permeability": 0.7}
        score_flat = calculate_recharge_score(flat_features).value
        score_steep = calculate_recharge_score(steep_features).value
        assert score_flat > score_steep


class TestHeatWaterStressScoring:
    def test_stress_bounds_and_severity(self) -> None:
        cool_features = {
            "lst_summer_max_c": 32.0,
            "ndvi_summer": 0.60,
            "rainfall_deficit_pct": 0.0,
            "groundwater_depth_m": 4.0,
            "distance_to_perennial_water_m": 200.0,
            "population_density_per_km2": 50.0,
        }
        hot_features = {
            "lst_summer_max_c": 47.0,
            "ndvi_summer": 0.10,
            "rainfall_deficit_pct": 35.0,
            "groundwater_depth_m": 25.0,
            "distance_to_perennial_water_m": 4000.0,
            "population_density_per_km2": 500.0,
        }
        score_cool = calculate_heat_water_stress(cool_features).value
        score_hot = calculate_heat_water_stress(hot_features).value
        assert score_hot > score_cool
        assert score_hot >= 70.0


class TestSpringDryingIndex:
    def test_no_spring_returns_zero(self) -> None:
        res = calculate_spring_drying_index({}, has_spring=False)
        assert res.value == 0.0
        assert res.score_class == ScoreClass.LOW

    def test_spring_vulnerability_with_deforestation(self) -> None:
        healthy = {
            "elevation_m": 400,
            "catchment_area_ha": 25,
            "forest_loss_pct": 2,
            "rainfall_trend_pct": 0,
        }
        degraded = {
            "elevation_m": 900,
            "catchment_area_ha": 2,
            "forest_loss_pct": 45,
            "rainfall_trend_pct": -18,
        }
        score_healthy = calculate_spring_drying_index(healthy, has_spring=True).value
        score_degraded = calculate_spring_drying_index(degraded, has_spring=True).value
        assert score_degraded > score_healthy


class TestSafetyVetoEngine:
    def test_safe_site_clears(self) -> None:
        features = {
            "slope_degrees": 8.0,
            "landslide_susceptibility": "low",
            "seismic_zone": 2,
            "distance_to_river_m": 600.0,
            "elevation_above_river_m": 25.0,
            "protected_area_type": None,
            "soil_type": "loam",
        }
        verdict = evaluate_safety_rules(features)
        assert verdict.status == SafetyStatus.SAFE
        assert len(verdict.rule_ids) == 0

    def test_slope_steep_triggers_reject(self) -> None:
        features = {"slope_degrees": 38.5}
        verdict = evaluate_safety_rules(features)
        assert verdict.status == SafetyStatus.REJECTED
        assert "SLOPE_STEEP" in verdict.rule_ids

    def test_flood_zone_triggers_reject(self) -> None:
        features = {
            "slope_degrees": 4.0,
            "distance_to_river_m": 110.0,
            "elevation_above_river_m": 2.5,
        }
        verdict = evaluate_safety_rules(features)
        assert verdict.status == SafetyStatus.REJECTED
        assert "FLOOD_ZONE" in verdict.rule_ids

    def test_landslide_triggers_reject(self) -> None:
        features = {"landslide_susceptibility": "high"}
        verdict = evaluate_safety_rules(features)
        assert verdict.status == SafetyStatus.REJECTED
        assert "LANDSLIDE_ZONE" in verdict.rule_ids

    def test_seismic_triggers_conditional(self) -> None:
        features = {
            "slope_degrees": 5.0,
            "landslide_susceptibility": "low",
            "seismic_zone": 4,
            "distance_to_river_m": 500.0,
            "elevation_above_river_m": 20.0,
        }
        verdict = evaluate_safety_rules(features)
        assert verdict.status == SafetyStatus.CONDITIONAL
        assert "SEISMIC_HIGH" in verdict.rule_ids


class TestInterventionsAndSimulation:
    def test_no_interventions_when_rejected(self) -> None:
        recs = compose_recommendations({"slope_degrees": 10.0}, is_rejected=True)
        assert recs == []

    def test_check_dam_recommendation_when_suitable(self) -> None:
        features = {
            "slope_degrees": 8.0,
            "catchment_area_ha": 15.0,
            "stream_order": 2,
            "soil_type": "sandy_loam",
        }
        recs = compose_recommendations(features, is_rejected=False)
        rec_ids = [r.intervention_id for r in recs]
        assert "check_dam" in rec_ids

    def test_scenario_sensitivity_and_uplift(self) -> None:
        features = {"slope_degrees": 6.0, "soil_permeability": 0.7}
        baseline = [calculate_recharge_score(features)]
        # Test 1.3x rainfall (+30%) with check dam uplift (+12 pts)
        sim = simulate_scenario(
            site_id="site_001",
            baseline_scores=baseline,
            rainfall_fraction=1.3,
            include_intervention="check_dam",
        )
        assert sim.rainfall_mm_adjusted == pytest.approx(1820.0, abs=1.0)
        assert sim.adjusted_scores[0].value > sim.baseline_scores[0].value


class TestEvaluateSiteIntegration:
    """Integration tests for the full evaluate_site pipeline."""

    def test_site_001_laxmipur_safe(self) -> None:
        site = evaluate_site("site_001")
        assert site is not None
        assert site.village.name == "Laxmipur"
        assert site.village.state == "Odisha"
        assert site.safety.status == SafetyStatus.SAFE
        assert len(site.recommendations) > 0
        rec_ids = [r.intervention_id for r in site.recommendations]
        assert "check_dam" in rec_ids

    def test_site_002_mundaguda_rejected(self) -> None:
        site = evaluate_site("site_002")
        assert site is not None
        assert site.village.name == "Mundaguda"
        assert site.safety.status == SafetyStatus.REJECTED
        assert "SLOPE_STEEP" in site.safety.rule_ids
        assert site.recommendations == []

    def test_site_004_dukum_conditional(self) -> None:
        site = evaluate_site("site_004")
        assert site is not None
        assert site.village.name == "Dukum"
        assert site.safety.status == SafetyStatus.CONDITIONAL
        assert "SLOPE_MODERATE" in site.safety.rule_ids
        assert len(site.recommendations) > 0

    def test_site_mp_004_bajag_scarp_rejected(self) -> None:
        site = evaluate_site("site_mp_004")
        assert site is not None
        assert site.village.name == "Bajag Scarp"
        assert site.village.state == "Madhya Pradesh"
        assert site.safety.status == SafetyStatus.REJECTED
        assert "SLOPE_STEEP" in site.safety.rule_ids

    def test_site_jh_004_porahat_scarp_rejected(self) -> None:
        site = evaluate_site("site_jh_004")
        assert site is not None
        assert site.village.name == "Porahat Scarp"
        assert site.village.state == "Jharkhand"
        assert site.safety.status == SafetyStatus.REJECTED
        assert "SLOPE_STEEP" in site.safety.rule_ids

    def test_all_sites_have_three_scores(self) -> None:
        from scoring import get_all_villages

        villages = get_all_villages()
        for village in villages:
            site = evaluate_site(village.id)
            assert site is not None, f"Site {village.id} not found"
            assert len(site.scores) == 3, (
                f"Expected 3 scores for {village.id}, got {len(site.scores)}"
            )
            score_types = {s.score_type for s in site.scores}
            assert score_types == {
                "recharge_score",
                "heat_water_stress",
                "spring_drying_index",
            }

    def test_score_classification_consistency(self) -> None:
        """Test that score classification uses the new enum values correctly."""
        from scoring import (
            calculate_recharge_score,
        )

        # Test recharge score classifications
        high_recharge = {
            "slope_degrees": 2.0,
            "soil_permeability": 0.9,
            "rainfall_intensity": 0.8,
            "lulc_perviousness": 0.9,
            "lineament_density": 0.8,
            "drainage_density": 0.2,
        }
        res = calculate_recharge_score(high_recharge)
        assert res.value >= 85
        assert res.score_class == ScoreClass.EXCELLENT

        low_recharge = {
            "slope_degrees": 35.0,
            "soil_permeability": 0.2,
            "rainfall_intensity": 0.3,
            "lulc_perviousness": 0.3,
            "lineament_density": 0.1,
            "drainage_density": 0.9,
        }
        res = calculate_recharge_score(low_recharge)
        # With current weights, min realistic score is around 16 (LOW class)
        assert res.value <= 30  # LOW class is 15-29
        assert res.score_class in (ScoreClass.LOW, ScoreClass.CRITICAL)

    def test_safety_feature_validation(self) -> None:
        """Test that safety rules validate features properly."""
        # Missing features should not crash
        verdict = evaluate_safety_rules({})
        assert verdict.status == SafetyStatus.SAFE

        # Invalid feature types should be handled gracefully
        verdict = evaluate_safety_rules(
            {"slope_degrees": "invalid", "seismic_zone": "high"}
        )
        assert verdict.status in (
            SafetyStatus.SAFE,
            SafetyStatus.CONDITIONAL,
            SafetyStatus.REJECTED,
        )

    def test_deterministic_scores_reproducible(self) -> None:
        """Test that the same inputs always produce the same scores."""
        site1 = evaluate_site("site_001")
        site2 = evaluate_site("site_001")

        for s1, s2 in zip(site1.scores, site2.scores):
            assert s1.value == s2.value
            assert s1.score_class == s2.score_class
            assert s1.drivers == s2.drivers
