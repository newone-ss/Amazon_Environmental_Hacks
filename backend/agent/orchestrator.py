"""
Bhujal — Lead District Planner & Dossier Orchestrator Agent
============================================================
Chief administrative orchestrator coordinating all domain specialist sub-agents,
reconciling safety vetoes, and synthesizing multi-site executive action dossiers.
"""

from __future__ import annotations

from datetime import datetime

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    from datetime import timezone

    UTC = timezone.utc
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

    def consult(
        self,
        site: Site,
        query: str,
        agent_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Interactive multi-agent planner consultation for a specific site.
        Evaluates the planner's query against geotechnical safety vetoes,
        lithology, hydrological scores, and state-calibrated MGNREGA structures.
        """
        assessment = self.assess_site(site)
        vname = site.village.name
        safety_status = assessment["safety_status"]
        is_rejected = safety_status == "REJECTED"
        q_lower = query.lower()

        scores_by_type = {s.score_type: s for s in site.scores}
        recharge_s = scores_by_type.get("recharge_score")
        heat_s = scores_by_type.get("heat_water_stress")
        spring_s = scores_by_type.get("spring_drying_index")

        recharge_val = recharge_s.value if recharge_s else 50.0
        heat_val = heat_s.value if heat_s else 50.0
        spring_val = spring_s.value if spring_s else 0.0

        # Attempt Bedrock invocation if enabled
        prompt = (
            f"Context: Village {vname}, State {site.village.state}, District {site.village.district}.\n"
            f"Safety Status: {safety_status}.\n"
            f"Scores: Recharge Suitability {recharge_val:.1f}/100, Heat Stress {heat_val:.1f}/100, Spring Drying Index {spring_val:.1f}/100.\n"
            f"Recommendations: {[r.intervention_name for r in site.recommendations] if site.recommendations else 'None'}.\n"
            f"User Planner Query: {query}\n"
            f"Provide an authoritative, safety-first response as Lead District Planner Orchestrator."
        )
        bedrock_narrative = self._invoke_bedrock(prompt)

        if bedrock_narrative:
            return {
                "site_id": site.village.id,
                "village_name": vname,
                "query": query,
                "agent_name": self.name,
                "role": self.role,
                "safety_status": safety_status,
                "response": bedrock_narrative,
                "recommendations": [
                    f"Follow geotechnical directives for {vname} ({safety_status}).",
                    "Coordinate with local Gram Panchayat and MGNREGA Programme Officer.",
                ],
                "mode": "bedrock",
                "timestamp": datetime.now(UTC).isoformat(),
            }

        # Deterministic grounded reasoning fallback
        recs: list[str] = []
        if is_rejected:
            rules = site.safety.rule_ids if site.safety else []
            reasons = site.safety.reasons if site.safety else []
            answer = (
                f"SAFETY VETO ENFORCED: As Lead District Planner, I must advise that {vname} is classified as REJECTED "
                f"due to geotechnical hazard rules ({', '.join(rules)}). "
                f"Specifically: {'; '.join(reasons)}. "
                "No civil structural build (such as check dams, percolation tanks, or masonry weirs) can be sanctioned "
                "under MGNREGA or District Watershed funds at this location, as doing so introduces unacceptable risks "
                "of slope destabilization or scarp collapse. "
                "Recommended alternative: Divert allocations strictly to bio-engineering (afforestation, Vetiver grass vegetative barriers, "
                "contour hedgerows) and groundwater monitoring."
            )
            recs = [
                "Prohibit capital sanction for concrete or heavy masonry civil works at this site.",
                "Implement non-structural bio-engineering and soil conservation works.",
                "Review downstream catchments with slopes < 20° for possible artificial recharge placement.",
            ]
        elif "spring" in q_lower or "jhola" in q_lower or "water table" in q_lower:
            has_sp = site.village.has_spring
            sp_note = (
                "A recognized gravity-fed spring exists at this site. Recharge zone protection in the upper recharge ridge is critical to arrest pre-monsoon discharge decline."
                if has_sp
                else "No primary registered perennial springhead is recorded in the baseline database for this settlement, though perched seasonal fractures may be present."
            )
            answer = (
                f"Springshed Assessment for {vname}: "
                f"Spring drying vulnerability index is rated at {spring_val:.1f}/100. "
                f"{sp_note} Recharge suitability is {recharge_val:.1f}/100. Continuous staggered contour trenches (CCT) on upper barren ridges are prioritized."
            )
            recs = [
                "Map upper micro-catchment recharge zone using GPS field tracking.",
                "Construct Continuous Contour Trenches (CCT) and loose boulder structures in upper 1st order streams.",
                "Engage community Jal Sathis to monitor monthly discharge telemetry.",
            ]
        elif "heat" in q_lower or "temperature" in q_lower or "summer" in q_lower:
            answer = (
                f"Heat-Water Compound Vulnerability for {vname}: "
                f"Composite heat-water stress score is {heat_val:.1f}/100. "
                f"In pre-monsoon months (April-June), elevated Land Surface Temperature (LST) and depleted soil moisture "
                f"create compound distress for tribal farmsteads. "
                f"Hydrological interventions that maintain surface pondage and shallow water tables directly mitigate local microclimate extremes."
            )
            recs = [
                "Fast-track shallow water harvesting bodies prior to May peak temperatures.",
                "Combine farm ponds with shade tree agroforestry along bunds.",
                "Schedule MGNREGA earthworks during cooler morning hours to protect wage-seekers.",
            ]
        elif (
            "cost" in q_lower
            or "budget" in q_lower
            or "mgnrega" in q_lower
            or "wage" in q_lower
        ):
            if site.recommendations:
                top_rec = site.recommendations[0]
                low_c = top_rec.cost_range_inr.get("low", 0)
                high_c = top_rec.cost_range_inr.get("high", 0)
                answer = (
                    f"MGNREGA Budget & Cost Specification for {vname} ({site.village.state}): "
                    f"Primary recommended structure: '{top_rec.intervention_name}'. "
                    f"Indicative capital cost range: INR {low_c:,.0f} to INR {high_c:,.0f} (approx. {(high_c / 100000):.2f} Lakhs). "
                    f"Estimated unskilled labour component: {top_rec.labour_days} person-days, calibrated to the state schedule of rates. "
                    f"Material-to-labour ratio complies with standard MGNREGA 60:40 guidelines."
                )
                recs = [
                    f"Submit work proposal under MGNREGA code 60:40 for {top_rec.intervention_name}.",
                    f"Sanction allocation of {top_rec.labour_days} person-days in the Gram Panchayat annual action plan.",
                ]
            else:
                answer = f"No civil structures are cleared for MGNREGA construction at {vname} under current geotechnical criteria."
                recs = [
                    "Explore administrative funding for watershed bio-fencing and nursery creation."
                ]
        else:
            if site.recommendations:
                top_rec = site.recommendations[0]
                answer = (
                    f"Lead District Planner Assessment for {vname}: "
                    f"The settlement is verified as {safety_status} for watershed development. "
                    f"Hydrogeological recharge suitability is {recharge_val:.1f}/100, and heat stress is {heat_val:.1f}/100. "
                    f"The multi-agent committee endorses '{top_rec.intervention_name}' as the optimal site-level intervention. "
                    f"This structure will maximize infiltration into fractured bedrock while remaining stable during peak monsoon discharge."
                )
                recs = [
                    f"Sanction technical survey for {top_rec.intervention_name}.",
                    "Conduct Gram Sabha consultation for location siting in common revenue lands.",
                    "Download the comprehensive DPR ZIP package for administrative technical sanction.",
                ]
            else:
                answer = (
                    f"Lead District Planner Assessment for {vname}: "
                    f"Site is cleared as {safety_status}, but standard civil structures did not meet minimum suitability thresholds. "
                    "Decentralized loose boulder check dams and plantation bunds are recommended."
                )
                recs = [
                    "Commission site inspection by Junior Engineer before finalizing intervention."
                ]

        return {
            "site_id": site.village.id,
            "village_name": vname,
            "query": query,
            "agent_name": self.name,
            "role": self.role,
            "safety_status": safety_status,
            "response": answer,
            "recommendations": recs,
            "mode": "deterministic_fallback",
            "timestamp": datetime.now(UTC).isoformat(),
        }
