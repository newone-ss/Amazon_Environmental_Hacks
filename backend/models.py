"""
Bhujal — Pydantic Models (API Contract)
========================================
These models define the data contract between frontend, backend,
and scoring engine. All scores follow Rule 4 of agent.md.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

# ── Enums ──────────────────────────────────────


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SafetyStatus(str, Enum):
    SAFE = "SAFE"
    CONDITIONAL = "CONDITIONAL"
    REJECTED = "REJECTED"


class ScoreClass(str, Enum):
    """Generic classification bucket."""

    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    LOW = "low"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"


class DataTag(str, Enum):
    """Badge shown in UI to indicate data provenance."""

    REAL = "real"
    PROXY = "proxy"
    ILLUSTRATIVE = "illustrative"


# ── Score Components ───────────────────────────


class Driver(BaseModel):
    """A single factor contributing to a score."""

    factor: str = Field(..., description="Name of the factor (e.g., 'slope')")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight in scoring formula")
    contribution: float = Field(
        ..., description="Weighted contribution to the final score (0-100 scale)"
    )


class Confidence(BaseModel):
    """Confidence metadata for a score."""

    level: ConfidenceLevel
    numeric: float = Field(
        ..., ge=0.0, le=1.0, description="Numeric confidence (0.0 to 1.0)"
    )


class ScoreResult(BaseModel):
    """
    Standard score output — Rule 4 of agent.md.
    Every scoring function MUST return this shape.
    """

    score_type: str = Field(
        ..., description="E.g., 'recharge_score', 'heat_water_stress'"
    )
    value: float = Field(..., ge=0.0, le=100.0, description="Score on 0-100 scale")
    score_class: ScoreClass = Field(..., description="Classification bucket")
    drivers: list[Driver] = Field(
        default_factory=list, description="Breakdown of contributing factors"
    )
    confidence: Confidence
    data_quality_note: str = Field(
        "", description="Note about data provenance or limitations"
    )
    data_tag: DataTag = Field(
        DataTag.REAL, description="Badge: real / proxy / illustrative"
    )


# ── Safety ─────────────────────────────────────


class SafetyRuleResult(BaseModel):
    """Result of a single safety rule evaluation."""

    rule_id: str
    triggered: bool
    verdict: SafetyStatus
    reason: str = ""


class SafetyVerdict(BaseModel):
    """Aggregated safety verdict for a site."""

    status: SafetyStatus
    rule_ids: list[str] = Field(
        default_factory=list, description="IDs of triggered rules"
    )
    reasons: list[str] = Field(
        default_factory=list, description="Human-readable reasons"
    )
    rules_evaluated: list[SafetyRuleResult] = Field(default_factory=list)


# ── Village / Site ─────────────────────────────


class Village(BaseModel):
    """A village or hamlet with its location and basic metadata."""

    id: str
    name: str
    block: str
    district: str
    state: str
    lat: float
    lon: float
    elevation_m: float | None = None
    population: int | None = None
    has_spring: bool = False
    data_tag: DataTag = DataTag.ILLUSTRATIVE


class Site(BaseModel):
    """A village with all computed scores, safety, and recommendations."""

    village: Village
    scores: list[ScoreResult] = Field(default_factory=list)
    safety: SafetyVerdict | None = None
    recommendations: list[Recommendation] = Field(default_factory=list)


# ── Recommendation ─────────────────────────────


class Recommendation(BaseModel):
    """A recommended intervention for a site."""

    intervention_id: str
    intervention_name: str
    category: str
    dimensions: dict[str, float] = Field(
        default_factory=dict, description="E.g., {'length_m': 10, 'height_m': 2}"
    )
    materials: list[str] = Field(default_factory=list)
    labour_days: int = 0
    cost_range_inr: dict[str, int] = Field(
        default_factory=dict, description="{'low': 150000, 'high': 500000}"
    )
    assumptions: list[str] = Field(
        default_factory=list, description="Assumptions behind this recommendation"
    )
    suitability_score: float = Field(
        0.0, ge=0.0, le=1.0, description="How well this intervention fits the site"
    )


# ── Scenario ───────────────────────────────────


class ScenarioRequest(BaseModel):
    """Input to the scenario simulator."""

    site_id: str
    rainfall_fraction: float = Field(
        1.0,
        ge=0.5,
        le=1.5,
        description="Fraction of baseline monsoon rainfall (0.5 = -50%, 1.5 = +50%)",
    )
    include_intervention: str | None = Field(
        None, description="Intervention ID to include in scenario"
    )


class ScenarioResult(BaseModel):
    """Output from the scenario simulator."""

    site_id: str
    baseline_scores: list[ScoreResult]
    adjusted_scores: list[ScoreResult]
    rainfall_mm_baseline: float
    rainfall_mm_adjusted: float
    intervention_applied: str | None = None
    notes: list[str] = Field(default_factory=list)


# ── Observations ───────────────────────────────


class ObservationCreate(BaseModel):
    """Field observation submitted by a user."""

    site_id: str
    observer_name: str = ""
    observation_type: str = Field(
        ..., description="E.g., 'spring_flow', 'well_depth', 'general'"
    )
    value: float | None = None
    unit: str | None = None
    notes: str = ""
    photo_filename: str | None = None


class Observation(ObservationCreate):
    """Stored observation with server-generated fields."""

    observation_id: str
    timestamp: datetime
    photo_url: str | None = None


# ── Report ─────────────────────────────────────


class ReportRequest(BaseModel):
    """Request to generate a planner-ready action report."""

    site_ids: list[str] = Field(
        ..., min_length=1, description="One or more site IDs to include"
    )
    include_scenario: bool = Field(
        False, description="Include scenario analysis in report"
    )
    rainfall_fraction: float = Field(1.0, ge=0.5, le=1.5)


class ReportResult(BaseModel):
    """Generated report metadata."""

    report_id: str
    title: str
    generated_at: datetime
    site_count: int
    download_url: str = Field(..., description="Presigned S3 URL or inline content")
    format: str = Field("html", description="'html' or 'pdf'")
    summary: str = Field("", description="Short narrative summary of the report")


# ── Meta ───────────────────────────────────────


class MetaResponse(BaseModel):
    """Response for GET /meta — system metadata."""

    version: str = "0.1.0"
    aoi_name: str
    aoi_state: str
    total_villages: int
    scoring_weights_hash: str = Field(
        "", description="Hash of weights.yaml for reproducibility"
    )
    data_tags_in_use: list[DataTag] = Field(default_factory=list)
    last_pipeline_run: datetime | None = None
    supported_states: list[str] = Field(default_factory=list)


# Forward reference update (Site references Recommendation which is defined after)
Site.model_rebuild()
