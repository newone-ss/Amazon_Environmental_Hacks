"""
Unit tests for the 7 specialized domain agents and report generation.
"""

from __future__ import annotations

from agent import (
    HeatWaterStressAgent,
    HydrogeologyAgent,
    LeadPlannerOrchestratorAgent,
    SafetyAuditorAgent,
    SpringshedAgent,
    TelemetryQAAgent,
    create_report,
)
from backend.models import (
    Observation,
    SafetyStatus,
    SafetyVerdict,
    ScoreClass,
    ScoreResult,
)
from scoring import evaluate_site, get_all_villages


class TestDomainSpecialistAgents:
    def test_hydrogeology_agent(self) -> None:
        agent = HydrogeologyAgent()
        score = ScoreResult(
            score_type="recharge_score",
            value=75.0,
            score_class=ScoreClass.EXCELLENT,
            drivers=[],
            confidence={"level": "high", "numeric": 0.85},  # type: ignore
        )
        res = agent.execute({"village_name": "Laxmipur", "score": score})
        assert res.agent_name == "HydrogeologyAgent"
        assert "Laxmipur" in res.summary
        assert len(res.recommendations) > 0

    def test_heat_water_stress_agent(self) -> None:
        agent = HeatWaterStressAgent()
        score = ScoreResult(
            score_type="heat_water_stress",
            value=82.0,
            score_class=ScoreClass.CRITICAL,
            drivers=[],
            confidence={"level": "high", "numeric": 0.9},  # type: ignore
        )
        res = agent.execute({"village_name": "Parajam", "score": score})
        assert res.agent_name == "HeatWaterStressAgent"
        assert "CRITICAL" in res.summary

    def test_springshed_agent(self) -> None:
        agent = SpringshedAgent()
        score = ScoreResult(
            score_type="spring_drying_index",
            value=68.0,
            score_class=ScoreClass.HIGH,
            drivers=[],
            confidence={"level": "medium", "numeric": 0.7},  # type: ignore
        )
        res = agent.execute(
            {"village_name": "Dukum", "score": score, "has_spring": True}
        )
        assert res.agent_name == "SpringshedAgent"
        assert "HIGH" in res.summary

    def test_safety_auditor_agent_veto(self) -> None:
        agent = SafetyAuditorAgent()
        verdict = SafetyVerdict(
            status=SafetyStatus.REJECTED,
            rule_ids=["SLOPE_STEEP"],
            reasons=["Slope exceeds 35°"],
        )
        res = agent.execute({"village_name": "Mundaguda", "safety": verdict})
        assert "REJECTED" in res.summary
        assert "SLOPE_STEEP" in res.summary

    def test_telemetry_qa_agent(self) -> None:
        agent = TelemetryQAAgent()
        obs = Observation(
            observation_id="obs_test",
            site_id="site_001",
            observer_name="Field Worker",
            observation_type="spring_flow",
            value=2.8,
            unit="L/s",
            notes="Measured at pipe",
            timestamp="2026-10-09T12:00:00Z",  # type: ignore
        )
        res = agent.execute({"village_name": "Laxmipur", "observation": obs})
        assert res.agent_name == "TelemetryQAAgent"
        assert "spring_flow" in res.summary


class TestOrchestratorAndReporting:
    def test_orchestrator_assessment(self) -> None:
        orchestrator = LeadPlannerOrchestratorAgent()
        site = evaluate_site("site_001")
        assert site is not None
        assessment = orchestrator.assess_site(site)
        assert assessment["site_id"] == "site_001"
        assert "agent_briefings" in assessment
        assert "hydrogeology" in assessment["agent_briefings"]
        assert "safety_audit" in assessment["agent_briefings"]

    def test_report_creation(self) -> None:
        villages = get_all_villages()
        sites = [
            evaluate_site(v.id) for v in villages if evaluate_site(v.id) is not None
        ]  # type: ignore
        orchestrator = LeadPlannerOrchestratorAgent()
        res = orchestrator.execute({"sites": sites})
        rpt = create_report(sites, res.summary, res.narrative)
        assert rpt.site_count == len(sites)
        assert rpt.format == "html"
        assert rpt.download_url.endswith(".html")
