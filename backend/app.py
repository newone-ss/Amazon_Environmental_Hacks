"""
Bhujal — FastAPI Application
==============================
Main app with all route stubs. Each endpoint returns
placeholder responses until scoring/agent modules are wired in.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from backend.models import (
    DataTag,
    MetaResponse,
    Observation,
    ObservationCreate,
    Recommendation,
    ReportRequest,
    ReportResult,
    ScenarioRequest,
    ScenarioResult,
    Site,
    Village,
)

app = FastAPI(
    title="Bhujal API",
    description="Decision-support tool for groundwater recharge planning in hilly tribal areas",
    version="0.1.0",
)

# CORS — dev and prod origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],  # Tighten "*" before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ─────────────────────────────────────


@app.get("/meta", response_model=MetaResponse)
async def get_meta() -> MetaResponse:
    """System metadata and AOI info."""
    return MetaResponse(
        aoi_name="Koraput District",
        aoi_state="Odisha",
        total_villages=5,
        data_tags_in_use=[DataTag.ILLUSTRATIVE],
    )


@app.get("/villages", response_model=list[Village])
async def list_villages() -> list[Village]:
    """List all villages in the AOI."""
    # TODO: load from scored pipeline output or demo_sites.yaml
    return []


@app.get("/sites/{site_id}", response_model=Site)
async def get_site(site_id: str) -> Site:
    """Full site detail with scores, safety, and recommendations."""
    # TODO: wire scoring engine
    raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found")


@app.post("/scenario", response_model=ScenarioResult)
async def run_scenario(request: ScenarioRequest) -> ScenarioResult:
    """Run a what-if rainfall scenario."""
    # TODO: wire scenario simulator
    raise HTTPException(
        status_code=501, detail="Scenario simulator not yet implemented"
    )


@app.post("/recommendation", response_model=list[Recommendation])
async def get_recommendations(site_id: str) -> list[Recommendation]:
    """Get recommended interventions for a site."""
    # TODO: wire intervention composer
    return []


@app.post("/observations", response_model=Observation, status_code=201)
async def create_observation(obs: ObservationCreate) -> Observation:
    """Submit a field observation."""
    # TODO: wire DynamoDB
    raise HTTPException(
        status_code=501, detail="Observation storage not yet implemented"
    )


@app.get("/observations", response_model=list[Observation])
async def list_observations(site_id: str | None = Query(None)) -> list[Observation]:
    """List observations, optionally filtered by site_id."""
    # TODO: wire DynamoDB
    return []


@app.post("/report", response_model=ReportResult)
async def generate_report(request: ReportRequest) -> ReportResult:
    """Generate a planner-ready action report."""
    # TODO: wire agent / template report generator
    raise HTTPException(status_code=501, detail="Report generation not yet implemented")


# ── Lambda handler ─────────────────────────────
handler = Mangum(app)
