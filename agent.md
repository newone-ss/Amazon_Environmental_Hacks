# Bhujal: Autonomous Engineering Directives and Governance

> **Document Status**: Canonical Specification and Agent Instructions  
> **Target Audience**: Autonomous Software Engineers, Contributing Developers, and System Architects

---

## 1. Project Context and Evaluation Constraints

* **Initiative**: Amazon Environmental Hacks 2026 — Heat and Water Track
* **Operational Time Window**: 48-Hour Hackathon Delivery Lifecycle
* **Evaluation Criteria**: 
  1. **Impact and Hydrogeological Validity**: Measurable utility for district-level planning and resilience.
  2. **AWS Architecture Compliance**: Mandatory utilization of core AWS services.
  3. **Usability and Engineering Polish**: Intuitive spatial interaction with zero layout or runtime anomalies.
  4. **Execution Integrity**: Complete, hardened end-to-end functionality across core features.
  5. **Auditable Demonstration**: Structured 3-minute technical recording with deterministic replication steps.

---

## 2. Product Specification

Bhujal is a specialized decision-support platform designed for district magistrates, block development officers, and watershed engineers in mountainous tribal regions of India. The platform analyzes complex multi-spectral, morphometric, and climatic data to deliver eight core capabilities:

| Capability | Engineering Objective | Methodological Foundation |
|---|---|---|
| **Recharge Suitability** | Identify high-potential infiltration corridors | Multi-criteria weighted linear combination |
| **Heat-Water Stress** | Map compound thermal and moisture vulnerabilities | Thermal radiometric anomalies + precipitation deficit |
| **Springhead Vulnerability** | Index seasonal drying probabilities | Morphometric and hydrological catchment heuristics |
| **Intervention Composer** | Recommend site-matched civil structures | Rule-based matrix matching site constraints |
| **Safety Veto Engine** | Enforce geotechnical and regulatory safety boundaries | Deterministic boolean threshold evaluations |
| **Indicative Costing** | Project preliminary capital and labour requirements | MGNREGA Schedule of Rates (Odisha 2024 calibrated) |
| **Uncertainty Quantification** | Deliver transparency on underlying data resolution | Structured confidence scoring and provenance badging |
| **Action Dossier Generation** | Produce audit-ready briefing reports for planners | Grounded LLM narrative synthesis with deterministic fallback |

---

## 3. Mandatory Engineering Rules

### Rule 1: Area of Interest Isolation
The analytical pipeline must dynamically read spatial bounds from `config/aoi.geojson`. For the validation and hackathon submission scope, analytical execution and demonstrations are strictly bounded to **Koraput District, Odisha**.

### Rule 2: Absolute Separation of Scoring and Language Models
* All indices, ratings, safety clearances, and financial projections must be produced exclusively by deterministic Python algorithms reading `config/*.yaml`.
* The Large Language Model (LLM) must never calculate, adjust, or arbitrate numerical outputs, costs, or safety statuses.
* The LLM is restricted entirely to translating deterministic metrics into administrative narratives and contextual summaries.

### Rule 3: Empirical Honesty and Provenance Badging
* Synthetic or fabricated data masquerading as empirical observations is strictly prohibited.
* If a primary dataset cannot be retrieved, a documented proxy or synthetic stand-in must be used and recorded in `data/README.md`.
* Every response and interface element must display an appropriate provenance badge:
  * `real`: Validated empirical observation or direct satellite measurement.
  * `proxy`: Spatially interpolated or secondary derived index.
  * `illustrative`: Curated synthetic record for demonstration and stress testing.
* Multi-criteria overlays must be designated as *transparent deterministic scoring*, never as *artificial intelligence*.

### Rule 4: Mandatory Score Schema
Every score generated across the platform must conform to the unified contractual schema:

```json
{
  "score_type": "string",
  "value": 0.0,
  "score_class": "string",
  "drivers": [
    {
      "factor": "string",
      "weight": 0.0,
      "contribution": 0.0
    }
  ],
  "confidence": {
    "level": "low | medium | high",
    "numeric": 0.0
  },
  "data_quality_note": "string",
  "data_tag": "real | proxy | illustrative"
}
```

### Rule 5: Required AWS Services
The platform must utilize the following AWS serverless building blocks:

| Component | AWS Resource | Deployment Role |
|---|---|---|
| Static Client Delivery | Amazon S3 + Amazon CloudFront | Global edge distribution with Origin Access Control (OAC) |
| Application Ingress | Amazon API Gateway HTTP API | Low-latency RESTful API gateway |
| Compute Runtime | AWS Lambda (Python 3.11) via Mangum | Serverless execution of the FastAPI application |
| Field Data Storage | Amazon DynamoDB | On-demand table storage for ground-truth observations |
| Media / Document Store | Amazon S3 | Presigned URL uploads for field images and generated dossiers |
| Generative AI Layer | Amazon Bedrock (Anthropic Claude 3 Sonnet) | LLM narrative synthesis orchestrated via Strands Agents SDK |
| Infrastructure as Code | AWS Serverless Application Model (SAM) | Declarative cloud formation templates in `infra/template.yaml` |

### Rule 6: Strict Scope Enforcement
Any capability not enumerated in the minimum viable product (MVP) specification below must be documented in `docs/future.md` and excluded from current implementation:

1. Interactive geospatial map with layered scoring visualizers.
2. Groundwater recharge suitability calculation module.
3. Heat-water vulnerability scoring module.
4. Heuristic springhead desiccation risk index.
5. Deterministic safety veto evaluator.
6. Civil intervention composer with MGNREGA cost schedule.
7. Dynamic rainfall scenario slider with real-time score perturbation.
8. Ground-truth field observation capture with photo upload capability.
9. Downloadable planner action dossier (HTML/PDF format).
10. Scientific validation and calibration panel.

### Rule 7: Development and Committing Protocol
* Work sequentially according to the phased implementation plan.
* Commit code frequently using standardized conventional commit messages.
* When completing a phase, log structured status: `Completed / Pending / Risks / Next Phase`.
* Resolve blocking ambiguities by selecting the simplest viable architectural option, immediately documenting the rationale in `docs/DECISIONS.md`.

### Rule 8: Code Quality and Documentation Integrity
* Complete Python 3.11 static type annotations across all modules.
* Unit test coverage for scoring algorithms, safety veto rules, and simulation routines.
* Zero hard-coded operational thresholds; all variables must reside in `config/*.yaml`.
* Zero committed credentials or environment keys; maintain `.env.example` as the canonical reference.
* Maintain structured dataset attribution records in `data/README.md`.

### Rule 9: Time-Box Management
If any feature implementation exceeds 150% of its designated time window, immediately trim non-essential sub-features, record the modification in `docs/DECISIONS.md`, and advance to the next priority.

---

## 4. Technology Stack Specification

* **Geospatial Pipeline**: Python 3.11, `numpy`, `geopandas`, `rasterio`, `rioxarray`, `shapely`, `pyproj`, `pysheds`.
* **Backend Application**: FastAPI, Mangum, Pydantic v2, Boto3, PyYAML.
* **Testing and Tooling**: Pytest, Ruff (linter and formatter), Mypy.
* **Client Interface**: React 18, TypeScript, Vite, MapLibre GL, Recharts.
* **Infrastructure**: AWS SAM CLI, CloudFormation.
* **Prohibited Technologies**: Next.js, PostGIS / relational database servers, user authentication layers (unnecessary overhead for 48-hour submission).

---

## 5. Phased Delivery Roadmap

### Phase 0: System Scaffolding and Interface Contracts (Completed)
* Establish repository directory layout and configuration schemas.
* Define Pydantic models in `backend/models.py`.
* Draft AWS SAM infrastructure template in `infra/template.yaml`.
* Implement initial contract validation tests in `tests/test_models.py`.
* Configure automated GitHub Actions CI pipeline.

### Phase 1: Data Pipeline and Scoring Engine (Current)
* Implement morphometric, hydrological, and climatic scoring modules in `scoring/`.
* Implement the deterministic safety rule evaluation engine in `scoring/safety.py`.
* Build intervention selection and cost modeling logic in `scoring/interventions.py`.
* Build scenario simulator routines in `scoring/simulator.py`.
* Achieve comprehensive unit test coverage across all scoring components.

### Phase 2: Application API and Generative Layer
* Wire scoring modules into FastAPI routes in `backend/app.py`.
* Implement DynamoDB persistence for field observations.
* Implement S3 presigned URL generation for field photos and reports.
* Integrate Amazon Bedrock narrative generation with deterministic template fallback.
* Verify local API contract conformance.

### Phase 3: Client Interface Development
* Initialize React + TypeScript application in `frontend/`.
* Integrate MapLibre GL for raster overlay and village point visualization.
* Build interactive inspection panels for scores, safety verdicts, and cost breakdowns.
* Integrate dynamic rainfall simulation controls and observation capture forms.
* Implement client-side export for action reports.

### Phase 4: Cloud Deployment and Final Validation
* Build and deploy AWS SAM stack across API Gateway, Lambda, DynamoDB, S3, and CloudFront.
* Conduct end-to-end operational verification against deployed HTTPS endpoints.
* Finalize comprehensive reproduction instructions and record the 3-minute demonstration video.
