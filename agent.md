# Bhujal — AI Agent Instructions

> **Purpose**: This file is the single source of truth for any AI agent working on this codebase. Read it fully before writing any code.

---

## 1. Context

- **Event**: Amazon Environmental Hacks 2026 — Heat and Water track
- **Time constraint**: 48-hour hackathon build
- **Judging criteria**: Idea & Impact, Built on AWS (mandatory for any prize), Design & Usability, Execution (one working feature beats five half-working ones), 3-minute recorded demo video (no live demo)

---

## 2. Product — Bhujal

Bhujal is a **decision-support tool for block and district planners in hilly and tribal areas**.

For one demonstration area (**Odisha / Jharkhand / Madhya Pradesh**) it shows:

| Capability | Description |
|---|---|
| Recharge suitability | Where monsoon water can be recharged |
| Heat-water stress | Which villages face heat-water stress |
| Spring-drying risk | Which springs risk drying (heuristic index) |
| Intervention composer | Which intervention suits a site |
| Safety veto | Whether it is safe to build there |
| Indicative cost | An approximate cost for the intervention |
| Confidence level | How sure we are about each score |
| Action report | A planner-ready downloadable report |

### One-line pitch

> Not just where the problem is, but what is safe to build and how sure we are.

---

## 3. Non-Negotiable Rules

### Rule 1 — One Area Only
The pipeline reads the area of interest from `config/aoi.geojson` so other areas can be loaded later, but we **demo and validate one area only**.

### Rule 2 — Determinism and Safety
- Scores, safety verdicts, and costs are computed by **deterministic code** driven by `config/*.yaml`.
- The LLM **never decides** scores, safety verdicts, or costs.
- The LLM **only explains and writes narratives** from numbers returned by tools.

### Rule 3 — Honesty
- **Never fabricate data.**
- If a real dataset is unavailable, use a clearly labelled **proxy or synthetic stand-in**.
- Tag it in the data manifest.
- Show an **"Illustrative"** or **"Proxy"** badge in the UI and report.
- Do not call weighted overlays "AI"; call them **transparent scoring**.
- Spring-drying risk is a **heuristic index** unless real discharge time series exist.

### Rule 4 — Score Schema
Every score **must** return:

```json
{
  "value": 0-100,
  "class": "string",
  "drivers": [
    { "factor": "string", "weight": 0.0, "contribution": 0.0 }
  ],
  "confidence": {
    "level": "low | medium | high",
    "numeric": 0.0
  },
  "data_quality_note": "string"
}
```

### Rule 5 — AWS is Required

| Component | AWS Service |
|---|---|
| Frontend hosting | S3 + CloudFront |
| API | Lambda behind API Gateway (or Lambda function URL) |
| Field observations | DynamoDB |
| Photo uploads | S3 via presigned URLs |
| AI explanations & reports | Strands Agents SDK + Amazon Bedrock |
| Infrastructure as Code | AWS SAM |
| Region | Verify Bedrock model access before deploying |

### Rule 6 — Scope Guard
Anything outside the MVP list goes to `docs/future.md`, **not into code**.

**MVP features (exhaustive list):**
1. Map with layers
2. Recharge score
3. Heat-water stress score
4. Spring drying index
5. Safety veto
6. Intervention composer with indicative cost
7. Scenario simulator (rainfall slider)
8. Field observation form
9. Action report (downloadable)
10. Validation panel

### Rule 7 — Process
- Work **phase by phase**.
- Small commits with clear messages.
- At the end of each phase print: `done / not done / risks / next`.
- Ask a question **only when truly blocked**; otherwise choose the simplest option and log it in `docs/DECISIONS.md`.

### Rule 8 — Quality
- Python **type hints** everywhere.
- **Unit tests** for scoring, safety rules, and the simulator.
- Thresholds and weights in **config files**, not hard-coded.
- **No secrets in the repo.** Use `.env.example`.
- Data licences and sources in `data/README.md` using the dataset record template:

```yaml
- name: "Dataset Name"
  source: "URL or provider"
  version: "v1.0"
  resolution: "30m / 1km / etc."
  licence: "CC-BY-4.0 / etc."
  download_method: "GEE export / direct download / API"
  preprocessing: "Steps applied"
  features: "What it provides"
  limitations: "Known issues"
```

### Rule 9 — Time-boxing
If a task exceeds its time box by **50%**, cut scope, record it in `docs/DECISIONS.md`, and move on.

---

## 4. Fixed Tech Choices

### Pipeline
- Python 3.11
- `rasterio`, `rioxarray`, `geopandas`, `numpy`
- `pysheds` or `whitebox` for flow accumulation
- Google Earth Engine allowed for climate and vegetation rasters if faster → export results to COG

### Backend
- **FastAPI** on Lambda via **Mangum**
- **AWS SAM** template
- **pytest** for testing

### Frontend
- **Vite + React + TypeScript**
- **MapLibre GL** for maps
- **GeoJSON or PMTiles** for vector tiles
- **Recharts** for charts
- ❌ No Next.js
- ❌ No PostGIS
- ❌ No auth

### AI Layer
- **Strands Agents SDK + Amazon Bedrock**
- Template fallback if Bedrock is unavailable

---

## 5. Repository Layout

```
/
├── config/
│   ├── aoi.geojson          # Area of interest (one area for demo)
│   ├── weights.yaml          # Scoring weights
│   ├── safety_rules.yaml     # Safety veto rules
│   ├── interventions.yaml    # Intervention types and logic
│   ├── costs.yaml            # Indicative cost tables
│   ├── scenario.yaml         # Scenario simulator parameters
│   └── demo_sites.yaml       # Pre-selected demo villages/sites
│
├── pipeline/
│   ├── download/             # Data acquisition scripts
│   ├── preprocess/           # Cleaning, reprojection, alignment
│   └── features/             # Feature extraction (slope, TWI, etc.)
│
├── scoring/                  # Deterministic scoring modules
│
├── backend/                  # FastAPI + Mangum
│
├── agent/                    # Strands Agents SDK integration
│
├── frontend/                 # Vite + React + TypeScript
│
├── infra/                    # AWS SAM templates
│
├── data/
│   └── README.md             # Data manifest (no raw data committed)
│
├── tests/                    # pytest test suite
│
├── docs/
│   ├── DECISIONS.md          # Design decisions log
│   ├── assumptions.md        # Assumptions made
│   ├── validation.md         # Validation methodology
│   ├── future.md             # Out-of-scope ideas
│   └── architecture.md       # System architecture
│
├── .env.example              # Environment variable template
├── agent.md                  # ← THIS FILE
└── README.md                 # Project overview and reproduction steps
```

---

## 6. Phased Build Plan

### Phase 0 — Scaffold & Config
- Create the full repo layout (all directories and stub files).
- Write all config YAMLs with realistic defaults for the demo AOI.
- Create `.env.example` and all docs stubs.
- **Exit criteria**: Everything imports, nothing runs yet.

### Phase 1 — Data Pipeline & Scoring
- Build the raster/vector pipeline: DEM, rainfall, LULC, soil, slope, lineaments for the demo AOI.
- Implement deterministic scoring modules:
  - Recharge score
  - Heat-water stress score
  - Spring-drying index
  - Safety veto
- All scores return the schema from Rule 4.
- Unit tests for all scoring functions.
- **Exit criteria**: `pytest` passes, scores are computed for the demo AOI.

### Phase 2 — Backend & Agent
- FastAPI app with Mangum adapter.
- Endpoints: `/scores`, `/interventions`, `/simulate`, `/observations`, `/report`.
- DynamoDB integration for field observations.
- S3 presigned URL generation for photo uploads.
- Strands Agents SDK + Bedrock integration for narrative generation (with template fallback).
- **Exit criteria**: All endpoints return valid responses locally.

### Phase 3 — Frontend
- Vite + React + TypeScript project.
- MapLibre GL map with scored layers.
- Click-a-village detail panel (scores, drivers, confidence).
- Intervention composer with indicative cost display.
- Rainfall scenario slider → summer water change visualization.
- Field observation form (text + photo upload).
- Downloadable action report (PDF or HTML).
- Proxy/Illustrative badges on synthetic data.
- Validation panel.
- **Exit criteria**: Full user flow works against backend.

### Phase 4 — Deploy & Demo
- SAM deploy: S3 + CloudFront, Lambda, API Gateway, DynamoDB.
- End-to-end smoke test on deployed URL.
- Record 3-minute demo video.
- Finalize README with reproduction steps.
- **Exit criteria**: A stranger can open the URL and complete the full flow.

---

## 7. Definition of Done

> A stranger opens the deployed URL, clicks a village, sees scores with reasons and confidence, sees a hazardous site rejected with the rule that rejected it, moves a rainfall slider and watches summer water change, submits a field observation, and downloads a report. The README explains how to reproduce the data pipeline.

---

## 8. Key Reminders for the Agent

1. **Never hallucinate data.** Use proxy data with badges if real data is unavailable.
2. **Never let the LLM compute scores.** Scores are deterministic Python code + config YAML.
3. **Always return the full score schema** (value, class, drivers, confidence, data_quality_note).
4. **Log every non-trivial decision** in `docs/DECISIONS.md`.
5. **Stay within MVP scope.** Extras go to `docs/future.md`.
6. **AWS services are mandatory** for any prize eligibility.
7. **One working feature beats five half-working ones.** Prioritize depth over breadth.
8. **Cut scope at 150% time-box**, document why, and move on.
