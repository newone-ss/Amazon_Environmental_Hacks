"""
Bhujal — Lead District Planner & Dossier Orchestrator Agent
============================================================
Chief administrative orchestrator coordinating all domain specialist sub-agents,
reconciling safety vetoes, and synthesizing multi-site executive action dossiers.
"""

from __future__ import annotations

from typing import Any

from agent.base import AgentResponse, BaseAgent
from agent.heat_stress import HeatWaterStressAgent
from agent.hydrogeology import HydrogeologyAgent
from agent.intervention_composer import InterventionComposerAgent
from agent.safety_auditor import SafetyAuditorAgent
from agent.scenario_simulator import ScenarioSimulatorAgent
from agent.springshed import SpringshedAgent
from agent.telemetry import TelemetryQAAgent
from backend.models import SafetyStatus, Site


class LeadPlannerOrchestratorAgent(BaseAgent):
    """Chief decision orchestrator delegating to specialist domain sub-agents."""

    def __init__(self) -> None:
        super().__init__(
            name="LeadPlannerOrchestratorAgent",
            role="Lead District Planner & Dossier Orchestrator",
            system_prompt=(
                "You are the Chief Watershed Planning Officer and Decision-Support Orchestrator "
                "for District Planning Cells across priority agro-ecological zones (Odisha, Madhya Pradesh, "
                "Jharkhand). You synthesize inputs from hydrogeologists, safety auditors, civil engineers, "
                "and climatologists into a concise, authoritative, executive action dossier for District Collectors. "
                "Be decisive, transparent about data quality, and uncompromising on safety."
            ),
        )
        self.hydro_agent = HydrogeologyAgent()
        self.stress_agent = HeatWaterStressAgent()
        self.spring_agent = SpringshedAgent()
        self.safety_agent = SafetyAuditorAgent()
        self.intervention_agent = InterventionComposerAgent()
        self.scenario_agent = ScenarioSimulatorAgent()
        self.telemetry_agent = TelemetryQAAgent()

    def assess_site(self, site: Site) -> dict[str, Any]:
        """
        Execute comprehensive multi-agent assessment for a site,
        invoking all domain specialists and synthesizing results.
        """
        vname = site.village.name
        scores_by_type = {s.score_type: s for s in site.scores}

        # 1. Specialist Agent Executions
        hydro_res = self.hydro_agent.execute(
            {
                "village_name": vname,
                "score": scores_by_type.get("recharge_score"),
            }
        )

        stress_res = self.stress_agent.execute(
            {
                "village_name": vname,
                "score": scores_by_type.get("heat_water_stress"),
            }
        )

        spring_res = self.spring_agent.execute(
            {
                "village_name": vname,
                "score": scores_by_type.get("spring_drying_index"),
                "has_spring": site.village.has_spring,
            }
        )

        safety_res = self.safety_agent.execute(
            {
                "village_name": vname,
                "safety": site.safety,
            }
        )

        is_rejected = bool(site.safety and site.safety.status == SafetyStatus.REJECTED)
        int_res = self.intervention_agent.execute(
            {
                "village_name": vname,
                "recommendations": site.recommendations,
                "is_rejected": is_rejected,
            }
        )

        # 2. Executive Synthesis
        recharge_score = scores_by_type.get("recharge_score")
        stress_score = scores_by_type.get("heat_water_stress")
        recharge_val = recharge_score.value if recharge_score else 0.0
        stress_val = stress_score.value if stress_score else 0.0
        safety_status = site.safety.status.value if site.safety else "SAFE"

        if is_rejected:
            safety_rule_ids = site.safety.rule_ids if site.safety else []
            exec_decision = (
                f"ACTION PROHIBITED: {vname} has been issued a formal SAFETY VETO. "
                f"Construction of heavy civil structures is strictly rejected ({'; '.join(safety_rule_ids)}). "
                f"No watershed civil capital may be allocated."
            )
        elif site.recommendations:
            top_rec = site.recommendations[0]
            exec_decision = (
                f"ACTION APPROVED: {vname} is cleared for civil development ({safety_status}). "
                f"Primary intervention '{top_rec.intervention_name}' approved with indicative budget "
                f"INR {top_rec.cost_range_inr.get('low', 0):,.0f} - {top_rec.cost_range_inr.get('high', 0):,.0f}. "
                f"Recharge suitability: {recharge_val:.1f}/100; Heat stress: {stress_val:.1f}/100."
            )
        else:
            exec_decision = (
                f"ACTION DEFERRED: {vname} is cleared for safety ({safety_status}), but no matching "
                f"structural interventions satisfied topographic criteria. Bio-engineering recommended."
            )

        return {
            "site_id": site.village.id,
            "village_name": vname,
            "safety_status": safety_status,
            "executive_decision": exec_decision,
            "agent_briefings": {
                "hydrogeology": hydro_res.model_dump(),
                "heat_water_stress": stress_res.model_dump(),
                "springshed": spring_res.model_dump(),
                "safety_audit": safety_res.model_dump(),
                "civil_engineering": int_res.model_dump(),
            },
        }

    def fallback_execute(self, context: dict[str, Any]) -> AgentResponse:
        sites: list[Site] = context.get("sites", [])
        assessments = [self.assess_site(s) for s in sites]

        approved_count = sum(1 for a in assessments if a["safety_status"] != "REJECTED")
        vetoed_count = sum(1 for a in assessments if a["safety_status"] == "REJECTED")

        states = sorted({s.village.state for s in sites if s.village.state})
        states_desc = ", ".join(states) if states else "Priority Watersheds"

        summary = (
            f"Evaluated {len(sites)} settlements across {states_desc}. "
            f"{approved_count} cleared for implementation; {vetoed_count} vetoed by geotechnical safety rules."
        )

        narrative = (
            f"Executive Watershed Planning Dossier — {states_desc}\n"
            f"Total Settlements Evaluated: {len(sites)}\n"
            f"- Approved / Cleared: {approved_count}\n"
            f"- Geotechnical Safety Vetoes: {vetoed_count}\n\n"
            "Summary of Strategic Determinations:\n"
            + "\n".join(
                f"- {a['village_name']}: {a['executive_decision']}" for a in assessments
            )
        )

        recs = [
            f"Forward approved site dossiers ({approved_count} locations) to the District Watershed Committee for technical sanctions.",
            f"Enforce immediate construction stop on {vetoed_count} vetoed sites to prevent structural slope failure.",
            "Integrate recommended labour allocations into the upcoming District MGNREGA Annual Action Plan.",
        ]

        return AgentResponse(
            agent_name=self.name,
            role=self.role,
            summary=summary,
            details={"assessments": assessments},
            narrative=narrative,
            recommendations=recs,
            mode="deterministic_fallback",
        )
