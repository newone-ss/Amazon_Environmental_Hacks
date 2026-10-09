"""
Bhujal — FastAPI Application
==============================
Main production REST API application with full integration into
deterministic scoring modules, multi-agent orchestrator, and DynamoDB/S3.
"""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

try:
    from mangum import Mangum
except ImportError:
    Mangum = None  # type: ignore

from agent.orchestrator import LeadPlannerOrchestratorAgent
from agent.report_generator import create_report
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
from scoring import (
    evaluate_site,
    get_all_villages,
    get_site_recommendations,
    run_site_scenario,
)

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "data" / "reports"

app = FastAPI(
    title="Bhujal API",
    description="Decision-support tool for groundwater recharge planning in hilly tribal areas",
    version="0.1.0",
)

# CORS — dev and prod origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for local development fallback
_local_observations: list[Observation] = []
_orchestrator = LeadPlannerOrchestratorAgent()


def _get_weights_hash() -> str:
    weights_path = CONFIG_DIR / "weights.yaml"
    if weights_path.exists():
        with open(weights_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    return "default_weights"


# ── Routes ─────────────────────────────────────


@app.get("/meta", response_model=MetaResponse)
async def get_meta() -> MetaResponse:
    """System metadata and AOI info."""
    villages = get_all_villages()
    return MetaResponse(
        version="0.1.0",
        aoi_name="Koraput District",
        aoi_state="Odisha",
        total_villages=len(villages),
        scoring_weights_hash=_get_weights_hash(),
        data_tags_in_use=[DataTag.REAL, DataTag.PROXY, DataTag.ILLUSTRATIVE],
        last_pipeline_run=datetime.now(timezone.utc),
    )


@app.get("/villages", response_model=list[Village])
async def list_villages() -> list[Village]:
    """List all villages in the demonstration Area of Interest."""
    return get_all_villages()


@app.get("/sites/{site_id}", response_model=Site)
async def get_site(site_id: str) -> Site:
    """Full site detail with scores, safety verdict, and recommendations."""
    site = evaluate_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found")
    return site


@app.post("/scenario", response_model=ScenarioResult)
async def run_scenario(request: ScenarioRequest) -> ScenarioResult:
    """Run a what-if rainfall scenario for a site."""
    result = run_site_scenario(
        site_id=request.site_id,
        rainfall_fraction=request.rainfall_fraction,
        include_intervention=request.include_intervention,
    )
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Site '{request.site_id}' not found for simulation"
        )
    return result


@app.post("/recommendation", response_model=list[Recommendation])
async def get_recommendations(
    site_id: str = Body(..., embed=True),
) -> list[Recommendation]:
    """Get recommended interventions for a site."""
    recs = get_site_recommendations(site_id)
    if recs is None:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found")
    return recs


@app.post("/observations", response_model=Observation, status_code=201)
async def create_observation(obs: ObservationCreate) -> Observation:
    """Submit a field observation."""
    obs_id = f"obs_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)

    # Generate photo URL if filename provided
    photo_url = None
    if obs.photo_filename:
        bucket = os.getenv("S3_BUCKET_UPLOADS", "bhujal-uploads")
        region = os.getenv("AWS_REGION", "ap-south-1")
        photo_url = f"https://{bucket}.s3.{region}.amazonaws.com/photos/{obs_id}_{obs.photo_filename}"

    stored = Observation(
        observation_id=obs_id,
        site_id=obs.site_id,
        observer_name=obs.observer_name,
        observation_type=obs.observation_type,
        value=obs.value,
        unit=obs.unit,
        notes=obs.notes,
        photo_filename=obs.photo_filename,
        timestamp=now,
        photo_url=photo_url,
    )

    # Persist to DynamoDB if configured
    table_name = os.getenv("DYNAMODB_TABLE_OBSERVATIONS")
    if table_name:
        try:
            import boto3

            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(table_name)
            item = stored.model_dump()
            item["timestamp"] = item["timestamp"].isoformat()
            table.put_item(Item=item)
        except Exception as exc:  # noqa: BLE001
            logger.debug("DynamoDB put_item bypassed (%s). Using local store.", exc)

    _local_observations.append(stored)
    return stored


@app.get("/observations", response_model=list[Observation])
async def list_observations(site_id: str | None = Query(None)) -> list[Observation]:
    """List observations, optionally filtered by site_id."""
    table_name = os.getenv("DYNAMODB_TABLE_OBSERVATIONS")
    if table_name:
        try:
            import boto3
            from boto3.dynamodb.conditions import Key

            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(table_name)
            if site_id:
                resp = table.query(
                    IndexName="site-index",
                    KeyConditionExpression=Key("site_id").eq(site_id),
                )
                items = resp.get("Items", [])
            else:
                resp = table.scan(Limit=50)
                items = resp.get("Items", [])

            return [Observation(**item) for item in items]
        except Exception as exc:  # noqa: BLE001
            logger.debug("DynamoDB query bypassed (%s). Using local store.", exc)

    if site_id:
        return [o for o in _local_observations if o.site_id == site_id]
    return list(_local_observations)


@app.post("/report", response_model=ReportResult)
async def generate_report(request: ReportRequest) -> ReportResult:
    """Generate a planner-ready action report across selected sites."""
    sites: list[Site] = []
    for sid in request.site_ids:
        s = evaluate_site(sid)
        if s:
            sites.append(s)

    if not sites:
        raise HTTPException(
            status_code=404, detail="None of the specified site IDs could be found"
        )

    # Execute multi-agent collective synthesis
    agent_res = _orchestrator.execute({"sites": sites})

    scenario_info = None
    if request.include_scenario:
        scenario_info = {
            "rainfall_fraction": request.rainfall_fraction,
            "notes": [
                f"Simulated {request.rainfall_fraction:.2f}x monsoon rainfall scaling."
            ],
        }

    return create_report(
        sites=sites,
        orchestrator_summary=agent_res.summary,
        orchestrator_narrative=agent_res.narrative,
        scenario_info=scenario_info,
    )


@app.get("/reports/{filename}", response_class=HTMLResponse)
def get_report_file(filename: str) -> HTMLResponse:
    """Serve a generated action dossier HTML document."""
    filepath = REPORTS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Report dossier not found")
    with open(filepath, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ── Lambda handler ─────────────────────────────
handler = Mangum(app) if Mangum is not None else None
