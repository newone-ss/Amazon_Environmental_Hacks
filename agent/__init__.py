"""
Bhujal — Multi-Agent Intelligence Layer
========================================
Hierarchical multi-agent collective built for hydro-climatic analysis,
safety auditing, civil intervention composition, and executive action dossiers.
"""

from agent.base import AgentResponse, BaseAgent
from agent.heat_stress import HeatWaterStressAgent
from agent.hydrogeology import HydrogeologyAgent
from agent.intervention_composer import InterventionComposerAgent
from agent.orchestrator import LeadPlannerOrchestratorAgent
from agent.report_generator import create_report, generate_action_dossier_html
from agent.safety_auditor import SafetyAuditorAgent
from agent.scenario_simulator import ScenarioSimulatorAgent
from agent.springshed import SpringshedAgent
from agent.telemetry import TelemetryQAAgent

__all__ = [
    "AgentResponse",
    "BaseAgent",
    "HeatWaterStressAgent",
    "HydrogeologyAgent",
    "InterventionComposerAgent",
    "LeadPlannerOrchestratorAgent",
    "SafetyAuditorAgent",
    "ScenarioSimulatorAgent",
    "SpringshedAgent",
    "TelemetryQAAgent",
    "create_report",
    "generate_action_dossier_html",
]
