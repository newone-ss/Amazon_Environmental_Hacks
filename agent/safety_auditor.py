"""
Bhujal — Geotechnical Safety Auditor Agent
===========================================
Specialized agent enforcing deterministic geotechnical hazard boundaries,
BIS construction limits, and regulatory environmental restrictions.
"""

from __future__ import annotations

from typing import Any

from agent.base import AgentResponse, BaseAgent
from backend.models import SafetyStatus, SafetyVerdict


class SafetyAuditorAgent(BaseAgent):
    """Auditor reviewing and enforcing geotechnical and regulatory safety vetoes."""

    def __init__(self) -> None:
        super().__init__(
            name="SafetyAuditorAgent",
            role="Geotechnical Safety Auditor",
            system_prompt=(
                "You are an uncompromising geotechnical and regulatory safety engineer reviewing "
                "proposed watershed construction sites in hilly tribal terrain. Your primary mandate "
                "is safety: you never compromise on geotechnical slope thresholds (>35°), active landslide "
                "hazard zones, or riparian flood corridors. Formulate strict, unambiguous verdicts."
            ),
        )

    def fallback_execute(self, context: dict[str, Any]) -> AgentResponse:
        verdict: SafetyVerdict = context.get("safety")  # type: ignore
        village_name = context.get("village_name", "Target Site")

        status = verdict.status if verdict else SafetyStatus.SAFE
        reasons = verdict.reasons if verdict else ["All safety rules cleared."]
        rules_triggered = verdict.rule_ids if verdict else []

        if status == SafetyStatus.REJECTED:
            summary = (
                f"VETO ISSUED: Civil construction at {village_name} is strictly REJECTED "
                f"due to geotechnical hazard rules: {', '.join(rules_triggered)}."
            )
            narrative = (
                f"Geotechnical Safety Audit for {village_name} — VERDICT: REJECTED\n"
                f"The site fails mandatory physical safety criteria. The following hazard rules were triggered:\n"
                + "\n".join(f"- {r}" for r in reasons)
                + "\n\nEngineering Directive: No earthen dams, check dams, or percolation tanks may be constructed "
                "at this location. Construction would present unacceptable risks of slope destabilization, "
                "landslide initiation, or flash flood destruction."
            )
            recs = [
                "Prohibit capital expenditure for heavy civil structures at this location.",
                "Redirect watershed funds to bio-engineering (afforestation, live fencing) rather than earthworks.",
                "Select alternative downstream sites conforming to maximum slope gradients under 20°.",
            ]

        elif status == SafetyStatus.CONDITIONAL:
            summary = (
                f"CONDITIONAL CLEARANCE: Construction at {village_name} requires modified "
                f"engineering designs to satisfy safety constraints ({', '.join(rules_triggered)})."
            )
            narrative = (
                f"Geotechnical Safety Audit for {village_name} — VERDICT: CONDITIONAL\n"
                f"The site may proceed to construction ONLY with specialized geotechnical reinforcements:\n"
                + "\n".join(f"- {r}" for r in reasons)
                + "\n\nEngineering Directive: Standard unreinforced designs are prohibited. Incorporate "
                "retaining berms, structural terracing, or seismic dampers as specified in the BIS guidelines."
            )
            recs = [
                "Mandate certified structural design review prior to site excavation.",
                "Incorporate stone masonry revetment and toe walls to prevent foundation slip.",
                "Budget a 25-40% cost contingency for geotechnical slope stabilization.",
            ]

        else:
            summary = f"SAFETY CLEARED: {village_name} satisfies all geotechnical stability and environmental buffer criteria."
            narrative = (
                f"Geotechnical Safety Audit for {village_name} — VERDICT: SAFE\n"
                "All safety checks passed successfully:\n"
                "- Terrain slope is within stable parameters for earthwork construction.\n"
                "- Outside designated high-hazard landslide susceptibility buffers.\n"
                "- Compliant with riparian flood offset and protected reserve boundaries.\n\n"
                "Engineering Directive: Site cleared for civil intervention planning."
            )
            recs = [
                "Proceed with standard civil works according to MGNREGA Schedule of Rates.",
                "Ensure standard compaction testing during earthen bund construction.",
            ]

        return AgentResponse(
            agent_name=self.name,
            role=self.role,
            summary=summary,
            details=verdict.model_dump() if verdict else {},
            narrative=narrative,
            recommendations=recs,
            mode="deterministic_fallback",
        )
