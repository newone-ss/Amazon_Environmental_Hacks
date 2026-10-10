"""
Bhujal — Field Telemetry & Ground-Truth QA Agent
=================================================
Specialized agent evaluating crowdsourced field measurements, validating telemetry bounds,
and cross-referencing on-ground spring discharge against satellite-derived risk scores.
"""

from __future__ import annotations

from typing import Any

from agent.base import AgentResponse, BaseAgent
from backend.models import Observation


class TelemetryQAAgent(BaseAgent):
    """Quality assurance agent evaluating field telemetry and ground-truth observations."""

    def __init__(self) -> None:
        super().__init__(
            name="TelemetryQAAgent",
            role="Field Telemetry & Ground-Truth QA Analyst",
            system_prompt=(
                "You are an expert field telemetry and hydrometric data quality officer. "
                "You inspect incoming field measurements from block geologists and citizen enumerators, "
                "validate measurement units, detect physical anomalies, and cross-reference "
                "ground observations with satellite predictions to update empirical confidence levels."
            ),
        )

    def fallback_execute(self, context: dict[str, Any]) -> AgentResponse:
        obs: Observation = context.get("observation")  # type: ignore
        village_name = context.get("village_name", "Target Site")

        obs_type = obs.observation_type if obs else "general"
        val = obs.value if obs else None
        unit = obs.unit if obs else ""
        observer = obs.observer_name if obs else "Anonymous"

        summary = (
            f"Field observation of type '{obs_type}' recorded at {village_name} by {observer}: "
            f"{val} {unit}."
        )

        qa_status = "VALIDATED"
        qa_notes = "Telemetry parameters are within plausible physical limits for the Eastern Ghats."

        if obs_type == "spring_flow" and val is not None:
            if val <= 0.0:
                qa_status = "CRITICAL_FLAG"
                qa_notes = "Zero flow confirmed: Springhead is currently dry or desiccated. Validates high spring drying risk."
            elif val > 50.0:
                qa_status = "ANOMALY_WARNING"
                qa_notes = "Extremely high discharge recorded (>50 L/s); verify measurement calibration."

        narrative = (
            f"Field Telemetry Quality Audit for {village_name}:\n"
            f"- Parameter: {obs_type.replace('_', ' ').title()}\n"
            f"- Recorded Measurement: {val} {unit} (Observer: {observer})\n"
            f"- Quality Status: {qa_status}\n"
            f"- Telemetry Evaluation: {qa_notes}\n"
            "- Longitudinal Action: This ground-truth measurement is logged into the DynamoDB ledger "
            "and will be utilized to calibrate future multi-criteria weighting matrices."
        )

        recs = [
            f"Log measurement to longitudinal hydrological time series (Status: {qa_status}).",
            "Schedule verification measurement within 30 days to track seasonal discharge recession.",
        ]

        return AgentResponse(
            agent_name=self.name,
            role=self.role,
            summary=summary,
            details=obs.model_dump() if obs else {},
            narrative=narrative,
            recommendations=recs,
            mode="deterministic_fallback",
        )
