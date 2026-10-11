"""
Bhujal — FastAPI Application
=============================
Main production REST API application with full integration into
deterministic scoring modules, multi-agent orchestrator, and DynamoDB/S3.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from threading import RLock

UTC_TZ = timezone.utc  # noqa: UP017
from pathlib import Path

logger = logging.getLogger(__name__)

from fastapi import Body, FastAPI, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from mangum import Mangum
except ImportError:
    Mangum = None  # type: ignore

from agent.base import AgentResponse
from agent.dpr_generator import create_dpr_zip, generate_dpr_package
from agent.orchestrator import LeadPlannerOrchestratorAgent
from agent.participatory import ParticipatoryMonitoringAgent
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
    generate_adaptation_pathway,
    generate_pathway_comparison,
    generate_pathway_visualization_data,
    get_all_villages,
    get_site_recommendations,
    pathway_to_dict,
    run_site_scenario,
)

_backend_dir = Path(__file__).resolve().parent
CONFIG_DIR = (
    _backend_dir / "config"
    if (_backend_dir / "config").exists()
    else _backend_dir.parent / "config"
)
REPORTS_DIR = _backend_dir.parent / "data" / "reports"

app = FastAPI(
    title="Bhujal API",
    description="Decision-support tool for groundwater recharge planning in hilly tribal areas",
    version="0.2.0",
)


# ── Security Middleware ─────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# CORS — dev and prod origins
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for local development fallback (thread-safe)
_local_observations: list[Observation] = []
_local_observations_lock = RLock()
_orchestrator = LeadPlannerOrchestratorAgent()
_participatory_agent = ParticipatoryMonitoringAgent()


class AgentConsultRequest(BaseModel):
    """Request model for interactive agent consultation."""

    site_id: str = Field(..., description="Target settlement ID")
    query: str = Field(
        ..., min_length=2, max_length=1000, description="Planner question"
    )
    agent_type: str | None = Field(
        None, description="Optional specific agent role to consult"
    )


class AgentSynthesizeRequest(BaseModel):
    """Request model for multi-site plan synthesis."""

    site_ids: list[str] = Field(..., min_length=1, description="List of settlement IDs")


def _get_weights_hash() -> str:
    weights_path = CONFIG_DIR / "weights.yaml"
    if weights_path.exists():
        with open(weights_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    return "default_weights"


def _resolve_site(site_id: str) -> Site | None:
    """
    Resolve a site entity by either its unique system ID (e.g. 'site_001')
    or case-insensitive settlement name (e.g. 'laxmipur', 'mundaguda').
    """
    site = evaluate_site(site_id)
    if site:
        return site
    site_norm = site_id.strip().lower()
    for v in get_all_villages():
        vname = v.name.lower()
        vid = v.id.lower()
        if (
            vname == site_norm
            or vid == site_norm
            or vname.replace(" ", "_") == site_norm
            or vname.replace(" ", "") == site_norm
        ):
            return evaluate_site(v.id)
    return None


# ── Routes ─────────────────────────────────────

# Cache for /meta endpoint (valid for 5 minutes)
_meta_cache: dict | None = None
_meta_cache_time: float = 0
_meta_cache_ttl = 300  # 5 minutes


@app.get("/meta", response_model=MetaResponse)
async def get_meta() -> MetaResponse:
    """System metadata and AOI info (cached for 5 minutes)."""
    global _meta_cache, _meta_cache_time
    import time

    now = time.time()
    if _meta_cache and (now - _meta_cache_time) < _meta_cache_ttl:
        return MetaResponse(**_meta_cache)

    villages = get_all_villages()
    meta = MetaResponse(
        version="0.2.0",
        aoi_name="Priority Watersheds: Odisha, Madhya Pradesh, Jharkhand",
        aoi_state="Multi-State (Odisha, Madhya Pradesh, Jharkhand; Pan-India Extensible)",
        total_villages=len(villages),
        scoring_weights_hash=_get_weights_hash(),
        data_tags_in_use=[DataTag.REAL, DataTag.PROXY, DataTag.ILLUSTRATIVE],
        last_pipeline_run=datetime.now(UTC_TZ),
        supported_states=["Odisha", "Madhya Pradesh", "Jharkhand", "Pan-India"],
    )
    _meta_cache = meta.model_dump()
    _meta_cache_time = now
    return meta


@app.get("/villages", response_model=list[Village])
async def list_villages(
    state: str | None = Query(
        None,
        description="Filter settlements by state (e.g., 'Odisha', 'Madhya Pradesh', 'Jharkhand')",
    ),
) -> list[Village]:
    """List all villages in the demonstration Area of Interest, optionally filtered by state."""
    villages = get_all_villages()
    if state:
        state_norm = state.strip().lower()
        villages = [v for v in villages if v.state.strip().lower() == state_norm]
    return villages


@app.get("/sites/{site_id}", response_model=Site)
async def get_site(site_id: str) -> Site:
    """Full site detail with scores, safety verdict, and recommendations."""
    site = _resolve_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found")
    return site


@app.post("/scenario", response_model=ScenarioResult)
async def run_scenario(request: ScenarioRequest) -> ScenarioResult:
    """Run a what-if rainfall scenario for a site."""
    resolved_site = _resolve_site(request.site_id)
    resolved_id = resolved_site.village.id if resolved_site else request.site_id
    result = run_site_scenario(
        site_id=resolved_id,
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
    resolved_site = _resolve_site(site_id)
    resolved_id = resolved_site.village.id if resolved_site else site_id
    recs = get_site_recommendations(resolved_id)
    if recs is None:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found")
    return recs


@app.post("/observations", response_model=Observation, status_code=201)
async def create_observation(obs: ObservationCreate) -> Observation:
    """Submit a field observation."""
    obs_id = f"obs_{uuid.uuid4().hex[:12]}"
    now = datetime.now(UTC_TZ)

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
            from botocore.config import Config

            dynamodb = boto3.resource(
                "dynamodb",
                config=Config(retries={"max_attempts": 3, "mode": "adaptive"}),
            )
            table = dynamodb.Table(table_name)
            item = stored.model_dump()
            item["timestamp"] = item["timestamp"].isoformat()
            table.put_item(Item=item)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "DynamoDB put_item failed after retries: %s. Using local store.", exc
            )

    with _local_observations_lock:
        _local_observations.append(stored)
    return stored


@app.get("/observations", response_model=list[Observation])
async def list_observations(
    site_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    exclusive_start_key: str | None = Query(None),
) -> list[Observation]:
    """List observations, optionally filtered by site_id with pagination."""
    table_name = os.getenv("DYNAMODB_TABLE_OBSERVATIONS")
    if table_name:
        try:
            import boto3
            from boto3.dynamodb.conditions import Key
            from botocore.config import Config

            dynamodb = boto3.resource(
                "dynamodb",
                config=Config(retries={"max_attempts": 3, "mode": "adaptive"}),
            )
            table = dynamodb.Table(table_name)
            if site_id:
                query_kwargs = {
                    "IndexName": "site-index",
                    "KeyConditionExpression": Key("site_id").eq(site_id),
                    "Limit": limit,
                }
                if exclusive_start_key:
                    import json

                    query_kwargs["ExclusiveStartKey"] = json.loads(exclusive_start_key)
                resp = table.query(**query_kwargs)
            else:
                scan_kwargs = {"Limit": limit}
                if exclusive_start_key:
                    import json

                    scan_kwargs["ExclusiveStartKey"] = json.loads(exclusive_start_key)
                resp = table.scan(**scan_kwargs)

            items = resp.get("Items", [])
            return [Observation(**item) for item in items]
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "DynamoDB query failed after retries: %s. Using local store.", exc
            )

    with _local_observations_lock:
        if site_id:
            return [o for o in _local_observations if o.site_id == site_id][:limit]
        return list(_local_observations)[:limit]


# ── Phase 4 Derived Telemetry Routes ─────────────────────────────────


@app.get("/telemetry/{site_id}", response_model=dict)
async def get_site_telemetry(site_id: str) -> dict:
    """Retrieve lazy cached derived empirical telemetry mapping for a settlement."""
    from scoring.derived_loader import get_settlement_derived_data

    data = get_settlement_derived_data(site_id)
    if not data:
        raise HTTPException(
            status_code=404, detail=f"No derived telemetry for site '{site_id}'"
        )
    return data


@app.get("/telemetry/districts/{district}/groundwater", response_model=dict)
async def get_district_groundwater(district: str) -> dict:
    """Retrieve lazy cached derived groundwater statistics for a district."""
    from scoring.derived_loader import get_district_groundwater_summary

    data = get_district_groundwater_summary(district)
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"District '{district}' not found in derived groundwater",
        )
    return data


# ── Participatory Monitoring Routes ─────────────────────────────────


class ParticipatoryTextRequest:
    """Request model for text-based community observation."""

    def __init__(
        self,
        text: str = Form(...),
        observer_id: str = Form(...),
        observer_name: str = Form(""),
        language_code: str = Form("en-IN"),
    ):
        self.text = text
        self.observer_id = observer_id
        self.observer_name = observer_name
        self.language_code = language_code


@app.post("/participatory/observe/text", response_model=dict)
async def submit_text_observation(
    text: str = Form(...),
    observer_id: str = Form(...),
    observer_name: str = Form(""),
    language_code: str = Form("en-IN"),
) -> AgentResponse:
    """Submit a community observation via text (WhatsApp message)."""
    result = _participatory_agent.execute(
        {
            "text": text,
            "observer_id": observer_id,
            "observer_name": observer_name,
            "language_code": language_code,
        }
    )
    if result.details.get("error"):
        raise HTTPException(
            status_code=400, detail=result.details.get("error", "Processing failed")
        )
    return result


@app.post("/participatory/observe/voice", response_model=dict)
async def submit_voice_observation(
    audio: UploadFile,
    observer_id: str = Form(...),
    observer_name: str = Form(""),
    language_code: str = Form("en-IN"),
) -> AgentResponse:
    """Submit a community observation via voice note (WhatsApp voice message)."""
    # Upload audio to S3 using streaming to avoid memory issues
    bucket = os.getenv("S3_BUCKET_UPLOADS", "bhujal-uploads")
    region = os.getenv("AWS_REGION", "ap-south-1")
    audio_key = f"voice/{observer_id}/{uuid.uuid4().hex[:12]}.{(audio.filename or 'audio').split('.')[-1]}"

    try:
        import boto3
        from botocore.config import Config

        s3 = boto3.client(
            "s3",
            region_name=region,
            config=Config(retries={"max_attempts": 3, "mode": "adaptive"}),
        )

        # Stream upload in chunks to avoid loading entire file into memory
        chunk_size = 1024 * 1024  # 1MB chunks
        from boto3.s3.transfer import TransferConfig

        transfer_config = TransferConfig(
            multipart_threshold=chunk_size, multipart_chunksize=chunk_size
        )

        # Use upload_fileobj for streaming
        await audio.seek(0)
        s3.upload_fileobj(
            audio.file, Bucket=bucket, Key=audio_key, Config=transfer_config
        )
        audio_s3_uri = f"s3://{bucket}/{audio_key}"
    except Exception as exc:  # noqa: BLE001
        logger.warning("S3 upload failed, using local fallback: %s", exc)
        audio_s3_uri = f"local://{audio_key}"

    result = _participatory_agent.execute(
        {
            "audio_s3_uri": audio_s3_uri,
            "observer_id": observer_id,
            "observer_name": observer_name,
            "language_code": language_code,
        }
    )
    if result.details.get("error"):
        raise HTTPException(
            status_code=400, detail=result.details.get("error", "Processing failed")
        )
    return result


@app.post("/participatory/observe/whatsapp")
async def whatsapp_webhook(
    request: Request,
    Body: str | None = Form(None),
    From: str | None = Form(None),
    MediaUrl0: str = Form(""),
    MediaContentType0: str = Form(""),
    X_Twilio_Signature: str | None = None,
    X_Hub_Signature_256: str | None = None,
) -> Response:
    """
    WhatsApp Business API webhook endpoint.

    Receives incoming messages from WhatsApp (via Twilio or Meta Cloud API).
    Handles both text and voice messages, supporting both JSON and Form encodings.
    Verifies request signatures for security.
    """
    # Verify Twilio signature (for Twilio WhatsApp API)
    twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if twilio_auth_token and X_Twilio_Signature:
        form_data = await request.form()
        # Reconstruct the URL for validation
        url = str(request.url)
        # Validate signature
        from twilio.request_validator import RequestValidator

        validator = RequestValidator(twilio_auth_token)
        if not validator.validate(url, dict(form_data), X_Twilio_Signature):
            logger.warning(
                "Invalid Twilio signature from %s",
                request.client.host if request.client else "unknown",
            )
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    # Verify Meta Cloud API signature (X-Hub-Signature-256)
    meta_app_secret = os.getenv("META_APP_SECRET")
    if meta_app_secret and X_Hub_Signature_256:
        body_bytes = await request.body()
        import hashlib
        import hmac

        expected_sig = (
            "sha256="
            + hmac.new(meta_app_secret.encode(), body_bytes, hashlib.sha256).hexdigest()
        )
        if not hmac.compare_digest(expected_sig, X_Hub_Signature_256):
            logger.warning(
                "Invalid Meta signature from %s",
                request.client.host if request.client else "unknown",
            )
            raise HTTPException(status_code=403, detail="Invalid Meta signature")

    # Re-read form data if we consumed it for validation
    if "application/json" in request.headers.get("content-type", ""):
        try:
            json_body = await request.json()
            Body = json_body.get("Body", json_body.get("body", Body))
            From = json_body.get("From", json_body.get("from", From))
            MediaUrl0 = json_body.get("MediaUrl0", MediaUrl0)
            MediaContentType0 = json_body.get("MediaContentType0", MediaContentType0)
        except (ValueError, json.JSONDecodeError) as exc:
            logger.debug("Failed to parse WhatsApp JSON payload: %s", exc)
    else:
        # For form data, we need to re-parse since we may have consumed it
        form_data = await request.form()
        Body = form_data.get("Body", Body)
        From = form_data.get("From", From)
        MediaUrl0 = form_data.get("MediaUrl0", MediaUrl0)
        MediaContentType0 = form_data.get("MediaContentType0", MediaContentType0)

    from_val = From or "whatsapp:+919876543210"
    body_val = Body or ""
    observer_id = from_val.replace("whatsapp:", "")
    observer_name = ""

    # If media (voice) attached
    if MediaUrl0 and "audio" in MediaContentType0:
        text = f"[Voice message received] {body_val}"
    else:
        text = body_val

    result = _participatory_agent.execute(
        {
            "text": text,
            "observer_id": observer_id,
            "observer_name": observer_name,
            "language_code": "en-IN",
        }
    )

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Thank you! Your observation has been recorded. {result.narrative}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@app.get("/participatory/leaderboard", response_model=list[dict])
async def get_leaderboard(
    state: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
) -> list[dict]:
    """Get top community contributors leaderboard."""
    return _participatory_agent.get_leaderboard(state=state, limit=limit)


@app.get("/participatory/stats/{observer_id}", response_model=dict)
async def get_observer_stats(observer_id: str) -> dict:
    """Get statistics for a specific observer."""
    # In production, query observer stats from DynamoDB
    return {
        "observer_id": observer_id,
        "total_observations": 0,
        "by_type": {},
        "badges_earned": [],
        "rank": None,
    }


# ── Adaptation Pathways Routes ─────────────────────────────────


class PathwayRequest(BaseModel):
    """Request model for pathway generation."""

    site_id: str = Field(..., description="Target settlement ID")
    ssp_scenario: str = Field(
        "SSP2-4.5",
        description="SSP scenario (e.g., SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5)",
    )
    base_rainfall_fraction: float = Field(
        1.0, ge=0.5, le=2.0, description="Base rainfall fraction"
    )


@app.post("/pathways/generate", response_model=dict)
async def generate_pathway(request: PathwayRequest) -> dict:
    """Generate a single adaptation pathway for a site under an SSP scenario."""
    site_id = request.site_id
    ssp_scenario = request.ssp_scenario
    base_rainfall_fraction = request.base_rainfall_fraction

    resolved_site = _resolve_site(site_id)
    target_id = resolved_site.village.id if resolved_site else site_id
    ssp = ssp_scenario or "SSP2-4.5"
    rf = 1.0 if base_rainfall_fraction is None else float(base_rainfall_fraction)

    try:
        pathway = generate_adaptation_pathway(target_id, ssp, rf)
        return pathway_to_dict(pathway)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Pathway generation failed: {exc}")


class PathwayCompareRequest(BaseModel):
    """Request model for pathway comparison."""

    site_id: str = Field(..., description="Target settlement ID")
    scenarios: list[str] | str = Field(
        default=["SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"],
        description="List of SSP scenarios or comma-separated string",
    )
    base_rainfall_fraction: float = Field(1.0, ge=0.5, le=2.0)


@app.post("/pathways/compare", response_model=dict)
async def compare_pathways(request: PathwayCompareRequest) -> dict:
    """Generate and compare pathways across multiple SSP scenarios."""
    site_id = request.site_id

    if isinstance(request.scenarios, list):
        scenario_list = request.scenarios
    else:
        scenarios_str = request.scenarios or "SSP1-2.6,SSP2-4.5,SSP3-7.0,SSP5-8.5"
        scenario_list = [s.strip() for s in scenarios_str.split(",") if s.strip()]

    resolved_site = _resolve_site(site_id)
    target_id = resolved_site.village.id if resolved_site else site_id

    try:
        pathways = generate_pathway_comparison(target_id, scenario_list)
        return {ssp: pathway_to_dict(p) for ssp, p in pathways.items()}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Pathway comparison failed: {exc}")


@app.get("/pathways/visualize/{site_id}/{ssp_scenario}", response_model=dict)
async def get_pathway_visualization(
    site_id: str,
    ssp_scenario: str,
    base_rainfall_fraction: float = Query(1.0),
) -> dict:
    """Get pathway data optimized for frontend visualization (IPCC AR6 style)."""
    try:
        pathway = generate_adaptation_pathway(
            site_id, ssp_scenario, base_rainfall_fraction
        )
        return generate_pathway_visualization_data(pathway)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"Visualization data generation failed: {exc}"
        )


@app.get("/pathways/scenarios", response_model=list[dict])
async def list_ssp_scenarios() -> list[dict]:
    """List available SSP scenarios with descriptions."""
    from scoring.pathways import load_pathway_config

    config = load_pathway_config()
    return [
        {
            "id": ssp,
            "rainfall_trend_per_decade": v.get("rainfall_trend", 0),
            "temp_trend_per_decade": v.get("temp_trend", 0),
            "description": v.get("description", ""),
        }
        for ssp, v in config.ssp_scenarios.items()
    ]


# ── Report Routes ─────────────────────────────────


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


@app.get("/reports/{filename:path}", response_class=HTMLResponse)
def get_report_file(filename: str) -> HTMLResponse:
    """Serve a generated action dossier HTML document with path traversal protection."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid report filename")
    safe_filename = Path(filename).name
    filepath = (REPORTS_DIR / safe_filename).resolve()
    if not filepath.exists() or not filepath.is_relative_to(REPORTS_DIR.resolve()):
        raise HTTPException(status_code=404, detail="Report dossier not found")
    with open(filepath, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ── AI Domain Specialist & Lead Planner Agent Routes ─────────────────────


@app.get("/agent/briefing/{site_id}", response_model=dict)
async def get_agent_briefing(site_id: str) -> dict:
    """Retrieve comprehensive multi-agent briefing across all domain specialists for a settlement."""
    site = _resolve_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found")
    briefing = _orchestrator.assess_site(site)
    is_rejected = briefing.get("safety_status") == "REJECTED"
    briefing["lead_decision"] = {
        "verdict": "rejected" if is_rejected else "approved",
        "summary": briefing.get("executive_decision", ""),
    }
    agents_map = briefing.get("agent_briefings", {})
    briefing["agents"] = [
        agents_map.get("safety_audit", {}),
        agents_map.get("hydrogeology", {}),
        agents_map.get("heat_water_stress", {}),
        agents_map.get("springshed", {}),
        agents_map.get("civil_engineering", {}),
    ]
    return briefing


@app.post("/agent/consult", response_model=dict)
async def consult_agent(req: AgentConsultRequest) -> dict:
    """
    Interactive consultation with the Lead District Planner and domain specialist agents.
    Evaluates queries against deterministic safety vetoes, lithology, and state MGNREGA rates.
    """
    site = _resolve_site(req.site_id)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{req.site_id}' not found")
    res = _orchestrator.consult(site, req.query, req.agent_type)
    res["response_text"] = res.get("response", "")
    res["evidence_bullets"] = res.get("recommendations", [])
    return res


@app.post("/agent/synthesize", response_model=dict)
async def synthesize_sites(req: AgentSynthesizeRequest) -> dict:
    """Run multi-site executive action dossier synthesis across settlements."""
    sites: list[Site] = []
    for sid in req.site_ids:
        s = _resolve_site(sid)
        if s:
            sites.append(s)
    if not sites:
        raise HTTPException(
            status_code=404, detail="No matching sites found for synthesis"
        )
    res = _orchestrator.execute({"sites": sites})
    return res.model_dump()


# ── DPR Generator Routes ─────────────────────────────────


@app.post("/dpr/generate", response_model=dict)
async def generate_dpr(
    request: Request,
    site_ids: str | None = Form(None),
    project_name: str = Form(""),
    include_pdf: bool = Form(False),
) -> dict:
    """Generate a DPR package (DOCX, XLSX, KML) for the given sites."""
    if "application/json" in request.headers.get("content-type", ""):
        try:
            body = await request.json()
            raw_sids = body.get("site_ids")
            if isinstance(raw_sids, list):
                site_ids = ",".join(raw_sids)
            elif isinstance(raw_sids, str):
                site_ids = raw_sids
            project_name = body.get("project_name", project_name)
            include_pdf = body.get("include_pdf", include_pdf)
        except (ValueError, json.JSONDecodeError) as exc:
            logger.debug("Failed to parse DPR JSON payload: %s", exc)

    if not site_ids:
        raise HTTPException(status_code=400, detail="At least one site_id required")

    site_list_raw = [s.strip() for s in site_ids.split(",") if s.strip()]
    site_list = []
    for s in site_list_raw:
        resolved = _resolve_site(s)
        site_list.append(resolved.village.id if resolved else s)

    if not site_list:
        raise HTTPException(status_code=400, detail="At least one site_id required")

    try:
        dpr = generate_dpr_package(site_list, project_name or None, include_pdf)
        zip_bytes = create_dpr_zip(dpr)

        import base64
        import tempfile

        import boto3
        from botocore.config import Config

        zip_b64 = base64.b64encode(zip_bytes).decode()
        presigned_url = None

        bucket = os.getenv("S3_BUCKET_UPLOADS", "bhujal-uploads")
        zip_key = f"dpr/{dpr.project_id}.zip"
        tmp_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                tmp.write(zip_bytes)
                tmp_path = tmp.name

            s3_client = boto3.client(
                "s3", config=Config(retries={"max_attempts": 3, "mode": "adaptive"})
            )
            s3_client.upload_file(tmp_path, bucket, zip_key)
            presigned_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": zip_key},
                ExpiresIn=3600,
            )
        except Exception as s3_err:  # noqa: BLE001
            logger.warning("S3 DPR upload/presign skipped or failed: %s", s3_err)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        return {
            "project_id": dpr.project_id,
            "project_name": dpr.project_name,
            "site_count": dpr.manifest["site_count"],
            "total_cost_inr": dpr.manifest["total_cost_high_inr"],
            "total_budget_inr": dpr.manifest["total_cost_high_inr"],
            "total_labour_days": dpr.manifest["total_labour_days"],
            "download_url": f"/dpr/download?site_ids={','.join(site_list)}",
            "zip_base64": zip_b64,
            "presigned_url": presigned_url,
            "manifest": dpr.manifest,
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"DPR generation failed: {exc}")


@app.api_route("/dpr/download", methods=["GET", "POST"], response_class=Response)
async def download_dpr_zip(
    request: Request,
    site_ids: str | None = Query(None),
    project_name: str = Query(""),
    include_pdf: bool = Query(False),
) -> Response:
    """Download DPR package as ZIP file directly."""
    if request.method == "POST":
        form_data = await request.form()
        form_sids = form_data.get("site_ids")
        if form_sids is not None:
            site_ids = str(form_sids)
        form_proj = form_data.get("project_name")
        if form_proj is not None:
            project_name = str(form_proj)
        form_pdf = form_data.get("include_pdf", include_pdf)
        include_pdf = str(form_pdf).lower() in ("true", "1")

    if not site_ids:
        raise HTTPException(status_code=400, detail="At least one site_id required")

    raw_list = [s.strip() for s in site_ids.split(",") if s.strip()]
    site_list = []
    for s in raw_list:
        resolved = _resolve_site(s)
        site_list.append(resolved.village.id if resolved else s)

    try:
        dpr = generate_dpr_package(site_list, project_name or None, include_pdf)
        zip_bytes = create_dpr_zip(dpr)

        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{dpr.project_id}.zip"'
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"DPR generation failed: {exc}")


@app.get("/dpr/schemes", response_model=dict)
async def list_scheme_mapping() -> dict:
    """Get scheme mapping for all intervention types."""
    from agent.dpr_generator import SCHEME_MAPPING, STATE_SCHEME_NUANCES

    return {
        "intervention_schemes": SCHEME_MAPPING,
        "state_nuances": STATE_SCHEME_NUANCES,
    }


# ── Static Files & SPA Frontend Serving ─────────────────────


def _resolve_frontend_dist() -> Path | None:
    """Resolve frontend dist directory with validated paths."""
    candidates = [
        Path(__file__).resolve().parent.parent / "frontend" / "dist",
        Path(os.getenv("FRONTEND_DIST", "")).resolve()
        if os.getenv("FRONTEND_DIST")
        else None,
    ]
    for candidate in candidates:
        if candidate and candidate.exists() and candidate.is_dir():
            return candidate
    return None


FRONTEND_DIST = _resolve_frontend_dist()

if FRONTEND_DIST:
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/aoi.geojson")
    async def get_aoi_geojson():
        geo_file = FRONTEND_DIST / "aoi.geojson"
        if geo_file.exists():
            return FileResponse(geo_file, media_type="application/geo+json")
        cfg_geo = CONFIG_DIR / "aoi.geojson"
        if cfg_geo.exists():
            return FileResponse(cfg_geo, media_type="application/geo+json")
        raise HTTPException(status_code=404, detail="AOI geojson not found")

    @app.get("/favicon.ico")
    async def get_favicon():
        fav = FRONTEND_DIST / "favicon.ico"
        if fav.exists():
            return FileResponse(fav)
        return Response(status_code=204)

    SPA_ROUTES = {
        "",
        "map",
        "field-data",
        "reports",
        "about",
        "about-data",
        "agents",
        "overview",
    }

    @app.get("/{full_path:path}")
    async def serve_spa_frontend(full_path: str):
        full_path_clean = full_path.strip("/")
        if ".." in full_path_clean or full_path_clean.startswith("."):
            raise HTTPException(status_code=400, detail="Invalid path")

        # Explicit API route prefixes - must match before SPA fallback
        api_prefixes = (
            "meta",
            "villages",
            "sites",
            "scenario",
            "recommendation",
            "observations",
            "telemetry",
            "participatory",
            "pathways",
            "report",
            "reports",
            "dpr",
            "agent",
            "docs",
            "openapi.json",
            "redoc",
            "aoi.geojson",
            "favicon.ico",
            "assets",
            "health",
            "ready",
        )
        if any(
            full_path_clean == p or full_path_clean.startswith(f"{p}/")
            for p in api_prefixes
        ):
            raise HTTPException(status_code=404, detail="API route not found")

        # Serve static files if they exist
        file_candidate = FRONTEND_DIST / full_path_clean
        if full_path_clean and file_candidate.is_file():
            # Prevent directory traversal
            try:
                file_candidate.resolve().relative_to(FRONTEND_DIST.resolve())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid path")
            return FileResponse(file_candidate)

        # SPA fallback for known routes
        if full_path_clean in SPA_ROUTES or full_path_clean == "":
            index_html = FRONTEND_DIST / "index.html"
            if index_html.exists():
                return FileResponse(index_html)

        raise HTTPException(status_code=404, detail="Not found")


# ── Lambda handler ─────────────────────────────
handler = Mangum(app) if Mangum is not None else None
