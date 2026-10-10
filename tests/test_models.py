"""
Tests for Pydantic models and API contract.
Validates that all models can be instantiated and serialised.
"""

import pytest
from pydantic import ValidationError

from backend.models import (
    Confidence,
    ConfidenceLevel,
    DataTag,
    Driver,
    MetaResponse,
    ObservationCreate,
    Recommendation,
    SafetyRuleResult,
    SafetyStatus,
    SafetyVerdict,
    ScenarioRequest,
    ScoreClass,
    ScoreResult,
    Site,
    Village,
)

# ── ScoreResult ────────────────────────────────


class TestScoreResult:
    def test_valid_score(self) -> None:
        score = ScoreResult(
            score_type="recharge_score",
            value=62.5,
            score_class=ScoreClass.GOOD,
            drivers=[
                Driver(factor="slope", weight=0.25, contribution=18.75),
                Driver(factor="soil_permeability", weight=0.20, contribution=14.0),
            ],
            confidence=Confidence(level=ConfidenceLevel.MEDIUM, numeric=0.65),
            data_quality_note="SRTM 30m + SoilGrids 250m",
            data_tag=DataTag.ILLUSTRATIVE,
        )
        assert score.value == 62.5
        assert score.score_class == ScoreClass.GOOD
        assert len(score.drivers) == 2
        assert score.confidence.level == ConfidenceLevel.MEDIUM

    def test_score_value_bounds(self) -> None:
        with pytest.raises(ValidationError):
            ScoreResult(
                score_type="test",
                value=150.0,  # Out of bounds
                score_class=ScoreClass.GOOD,
                drivers=[],
                confidence=Confidence(level=ConfidenceLevel.LOW, numeric=0.3),
            )

    def test_score_serialization(self) -> None:
        score = ScoreResult(
            score_type="heat_water_stress",
            value=80.0,
            score_class=ScoreClass.CRITICAL,
            drivers=[],
            confidence=Confidence(level=ConfidenceLevel.HIGH, numeric=0.9),
            data_quality_note="MODIS 1km",
        )
        data = score.model_dump()
        assert data["score_type"] == "heat_water_stress"
        assert data["value"] == 80.0
        assert data["confidence"]["level"] == "high"


# ── SafetyVerdict ──────────────────────────────


class TestSafetyVerdict:
    def test_safe_verdict(self) -> None:
        verdict = SafetyVerdict(status=SafetyStatus.SAFE)
        assert verdict.status == SafetyStatus.SAFE
        assert verdict.rule_ids == []

    def test_rejected_verdict(self) -> None:
        verdict = SafetyVerdict(
            status=SafetyStatus.REJECTED,
            rule_ids=["SLOPE_STEEP"],
            reasons=["Slope of 42° exceeds the 35° safety limit"],
            rules_evaluated=[
                SafetyRuleResult(
                    rule_id="SLOPE_STEEP",
                    triggered=True,
                    verdict=SafetyStatus.REJECTED,
                    reason="Slope of 42° exceeds the 35° safety limit",
                )
            ],
        )
        assert verdict.status == SafetyStatus.REJECTED
        assert "SLOPE_STEEP" in verdict.rule_ids


# ── Village & Site ─────────────────────────────


class TestVillage:
    def test_village_creation(self) -> None:
        v = Village(
            id="site_001",
            name="Laxmipur",
            block="Koraput",
            district="Koraput",
            state="Odisha",
            lat=18.8124,
            lon=82.7133,
        )
        assert v.name == "Laxmipur"
        assert v.data_tag == DataTag.ILLUSTRATIVE  # Default


class TestSite:
    def test_site_with_scores(self) -> None:
        village = Village(
            id="site_001",
            name="Laxmipur",
            block="Koraput",
            district="Koraput",
            state="Odisha",
            lat=18.8124,
            lon=82.7133,
        )
        site = Site(village=village, scores=[], safety=None, recommendations=[])
        assert site.village.id == "site_001"


# ── Scenario ───────────────────────────────────


class TestScenario:
    def test_scenario_request_bounds(self) -> None:
        req = ScenarioRequest(site_id="site_001", rainfall_fraction=0.7)
        assert req.rainfall_fraction == 0.7

    def test_scenario_request_out_of_bounds(self) -> None:
        with pytest.raises(ValidationError):
            ScenarioRequest(site_id="site_001", rainfall_fraction=2.0)


# ── Observation ────────────────────────────────


class TestObservation:
    def test_observation_create(self) -> None:
        obs = ObservationCreate(
            site_id="site_001",
            observation_type="spring_flow",
            value=2.5,
            unit="litres_per_second",
        )
        assert obs.observation_type == "spring_flow"


# ── Recommendation ─────────────────────────────


class TestRecommendation:
    def test_recommendation(self) -> None:
        rec = Recommendation(
            intervention_id="check_dam",
            intervention_name="Check Dam",
            category="recharge",
            dimensions={"length_m": 10, "height_m": 2},
            materials=["stone masonry"],
            labour_days=45,
            cost_range_inr={"low": 150000, "high": 500000},
            assumptions=["Slope < 15°"],
            suitability_score=0.82,
        )
        assert rec.cost_range_inr["low"] == 150000


# ── Meta ───────────────────────────────────────


class TestMeta:
    def test_meta_response(self) -> None:
        meta = MetaResponse(
            aoi_name="Koraput District",
            aoi_state="Odisha",
            total_villages=5,
        )
        assert meta.version == "0.1.0"
