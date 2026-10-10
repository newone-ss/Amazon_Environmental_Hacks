# Bhujal REST API Specification

> **Protocol**: HTTPS / REST  
> **Data Interchange**: `application/json`  
> **Schema Standard**: OpenAPI 3.1 / Pydantic v2  
> **Reference Models**: [`backend/models.py`](../backend/models.py)

---

## 1. Global Conventions

### 1.1. Base URLs
* **Production**: `https://<api-gateway-id>.execute-api.ap-south-1.amazonaws.com/prod`
* **Local Development**: `http://localhost:8000`

### 1.2. Authentication & Authorization
In accordance with hackathon demonstration parameters, public read and write access is enabled without an authorization header. Production implementations should introduce Amazon Cognito or IAM authorization.

### 1.3. Standard Error Envelope
All error responses adhere to the standard RFC 7807 structured format:

```json
{
  "detail": "Descriptive human-readable error explanation.",
  "error_code": "RESOURCE_NOT_FOUND",
  "timestamp": "2026-10-09T17:45:00Z"
}
```

Standard HTTP status codes utilized:
* `200 OK`: Request succeeded.
* `201 Created`: Resource successfully persisted.
* `400 Bad Request`: Input payload validation failure.
* `404 Not Found`: Target entity identifier does not exist.
* `422 Unprocessable Entity`: Request body violates Pydantic constraints.
* `500 Internal Server Error`: Unhandled application exception.
* `501 Not Implemented`: Planned endpoint awaiting downstream module integration.

---

## 2. API Endpoints

### 2.1. System Metadata

#### `GET /meta`
Retrieves runtime system metadata, area of interest boundaries, and verification hashes for active scoring models.

* **Method**: `GET`
* **Authentication**: None
* **Request Headers**: `Accept: application/json`

**Response (`200 OK`)**:
```json
{
  "version": "0.1.0",
  "aoi_name": "Priority Watersheds: Odisha, Madhya Pradesh, Jharkhand",
  "aoi_state": "Multi-State (Odisha, Madhya Pradesh, Jharkhand; Pan-India Extensible)",
  "total_villages": 13,
  "scoring_weights_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "data_tags_in_use": [
    "real",
    "proxy",
    "illustrative"
  ],
  "last_pipeline_run": "2026-10-09T12:00:00Z",
  "supported_states": [
    "Odisha",
    "Madhya Pradesh",
    "Jharkhand",
    "Pan-India"
  ]
}
```

---

### 2.2. Villages and Spatial Entities

#### `GET /villages`
Enumerates all tracked settlements and hamlets within the active Area of Interest, optionally filtered by state.

* **Method**: `GET`
* **Query Parameters**:
  * `state` (*string, optional*): Filter settlements by state (e.g., `Odisha`, `Madhya Pradesh`, `Jharkhand`). Case-insensitive.

**Response (`200 OK`)**:
```json
[
  {
    "id": "site_001",
    "name": "Laxmipur",
    "block": "Koraput",
    "district": "Koraput",
    "state": "Odisha",
    "lat": 18.8124,
    "lon": 82.7133,
    "elevation_m": 580.0,
    "population": 1200,
    "has_spring": true,
    "data_tag": "illustrative"
  },
  {
    "id": "site_002",
    "name": "Mundaguda",
    "block": "Semiliguda",
    "district": "Koraput",
    "state": "Odisha",
    "lat": 18.9456,
    "lon": 82.8910,
    "elevation_m": 720.0,
    "population": 800,
    "has_spring": false,
    "data_tag": "illustrative"
  }
]
```

---

### 2.3. Site Evaluation and Comprehensive Assessment

#### `GET /sites/{site_id}`
Returns complete hydro-climatic analysis, safety veto evaluations, and matched civil recommendations for a specific settlement.

* **Method**: `GET`
* **Path Parameters**:
  * `site_id` (string, required): Unique identifier of the village (e.g., `site_001`).

**Response (`200 OK`)**:
```json
{
  "village": {
    "id": "site_001",
    "name": "Laxmipur",
    "block": "Koraput",
    "district": "Koraput",
    "state": "Odisha",
    "lat": 18.8124,
    "lon": 82.7133,
    "elevation_m": 580.0,
    "population": 1200,
    "has_spring": true,
    "data_tag": "illustrative"
  },
  "scores": [
    {
      "score_type": "recharge_score",
      "value": 62.5,
      "score_class": "good",
      "drivers": [
        {
          "factor": "slope",
          "weight": 0.25,
          "contribution": 18.75
        },
        {
          "factor": "soil_permeability",
          "weight": 0.20,
          "contribution": 14.0
        },
        {
          "factor": "rainfall_intensity",
          "weight": 0.20,
          "contribution": 13.5
        },
        {
          "factor": "lulc_perviousness",
          "weight": 0.15,
          "contribution": 9.75
        },
        {
          "factor": "lineament_density",
          "weight": 0.10,
          "contribution": 3.5
        },
        {
          "factor": "drainage_density",
          "weight": 0.10,
          "contribution": 3.0
        }
      ],
      "confidence": {
        "level": "medium",
        "numeric": 0.65
      },
      "data_quality_note": "Soil derived from SoilGrids 250m; slope from SRTM 30m DSM.",
      "data_tag": "illustrative"
    },
    {
      "score_type": "heat_water_stress",
      "value": 48.0,
      "score_class": "moderate",
      "drivers": [
        {
          "factor": "lst_summer_max",
          "weight": 0.25,
          "contribution": 15.0
        },
        {
          "factor": "rainfall_deficit",
          "weight": 0.20,
          "contribution": 12.0
        }
      ],
      "confidence": {
        "level": "medium",
        "numeric": 0.70
      },
      "data_quality_note": "MODIS LST 1km composite + CHIRPS precipitation anomaly.",
      "data_tag": "illustrative"
    }
  ],
  "safety": {
    "status": "SAFE",
    "rule_ids": [],
    "reasons": [],
    "rules_evaluated": [
      {
        "rule_id": "SLOPE_STEEP",
        "triggered": false,
        "verdict": "SAFE",
        "reason": "Mean slope (8.4°) is below 35° geotechnical limit."
      },
      {
        "rule_id": "LANDSLIDE_ZONE",
        "triggered": false,
        "verdict": "SAFE",
        "reason": "Outside high-susceptibility landslide buffer."
      }
    ]
  },
  "recommendations": [
    {
      "intervention_id": "check_dam",
      "intervention_name": "Check Dam (Nala Bund)",
      "category": "recharge",
      "dimensions": {
        "length_m": 10.0,
        "height_m": 2.0,
        "width_m": 3.0
      },
      "materials": [
        "stone masonry",
        "cement",
        "gabion wire"
      ],
      "labour_days": 45,
      "cost_range_inr": {
        "low": 150000,
        "high": 500000
      },
      "assumptions": [
        "Slope between 2° and 15°",
        "Stream order <= 3",
        "Permeable stream bed substrate"
      ],
      "suitability_score": 0.82
    }
  ]
}
```

---

### 2.4. Climate Sensitivity and Scenario Simulation

#### `POST /scenario`
Executes first-order sensitivity perturbation simulations by scaling baseline precipitation and modeling expected intervention uplifts.

* **Method**: `POST`
* **Request Headers**: `Content-Type: application/json`

**Request Body (`ScenarioRequest`)**:
```json
{
  "site_id": "site_001",
  "rainfall_fraction": 0.75,
  "include_intervention": "check_dam"
}
```

*Constraints*:
* `rainfall_fraction`: Float between `0.5` (-50% drought anomaly) and `1.5` (+50% excess monsoon).
* `include_intervention`: Optional identifier matching an approved intervention catalog entry.

**Response (`200 OK`)**:
```json
{
  "site_id": "site_001",
  "baseline_scores": [
    {
      "score_type": "recharge_score",
      "value": 62.5,
      "score_class": "good",
      "drivers": [],
      "confidence": { "level": "medium", "numeric": 0.65 },
      "data_quality_note": "Baseline reference",
      "data_tag": "illustrative"
    }
  ],
  "adjusted_scores": [
    {
      "score_type": "recharge_score",
      "value": 64.5,
      "score_class": "good",
      "drivers": [],
      "confidence": { "level": "medium", "numeric": 0.65 },
      "data_quality_note": "Scenario modified: -25% rainfall with +12pt check dam uplift",
      "data_tag": "illustrative"
    }
  ],
  "rainfall_mm_baseline": 1400.0,
  "rainfall_mm_adjusted": 1050.0,
  "intervention_applied": "check_dam",
  "notes": [
    "Rainfall reduced by 25% (deficit scenario).",
    "Applied linear sensitivity coefficient: +40 pts / 100% precipitation change.",
    "Applied civil intervention uplift: +12 pts for check dam installation."
  ]
}
```

---

### 2.5. Field Observations and Telemetry Ledger

#### `POST /observations`
Registers a ground-truth field measurement submitted by an enumerator or local planner.

* **Method**: `POST`
* **Request Headers**: `Content-Type: application/json`

**Request Body (`ObservationCreate`)**:
```json
{
  "site_id": "site_001",
  "observer_name": "R. C. Majhi (Block Geologist)",
  "observation_type": "spring_flow",
  "value": 3.2,
  "unit": "litres_per_second",
  "notes": "Post-monsoon baseflow measured at masonry collection chamber.",
  "photo_filename": "laxmipur_spring_oct2026.jpg"
}
```

**Response (`201 Created`)**:
```json
{
  "observation_id": "obs_9c41bf62-b91c-4384-82a1-faec6402e88a",
  "site_id": "site_001",
  "observer_name": "R. C. Majhi (Block Geologist)",
  "observation_type": "spring_flow",
  "value": 3.2,
  "unit": "litres_per_second",
  "notes": "Post-monsoon baseflow measured at masonry collection chamber.",
  "photo_filename": "laxmipur_spring_oct2026.jpg",
  "timestamp": "2026-10-09T18:02:14.281903Z",
  "photo_url": "https://bhujal-uploads-123456789012.s3.ap-south-1.amazonaws.com/photos/obs_9c41bf62.jpg?X-Amz-Signature=..."
}
```

#### `GET /observations`
Retrieves stored telemetry observations, optionally filtered by village identifier.

* **Method**: `GET`
* **Query Parameters**:
  * `site_id` (string, optional): Target village identifier. If omitted, returns all recent observations across the AOI.

---

### 2.6. Action Dossier and Planning Reports

#### `POST /report`
Compiles an administrative action dossier containing hydrogeological summaries, safety clearances, and indicative bills of quantities.

* **Method**: `POST`
* **Request Headers**: `Content-Type: application/json`

**Request Body (`ReportRequest`)**:
```json
{
  "site_ids": [
    "site_001",
    "site_002"
  ],
  "include_scenario": true,
  "rainfall_fraction": 0.8
}
```

**Response (`200 OK`)**:
```json
{
  "report_id": "rpt_koraput_20261009_001",
  "title": "Bhujal Comprehensive Watershed Planning Dossier",
  "generated_at": "2026-10-09T18:15:00Z",
  "site_count": 2,
  "download_url": "https://bhujal-uploads-123456789012.s3.ap-south-1.amazonaws.com/reports/rpt_koraput_20261009_001.html?...",
  "format": "html",
  "summary": "Assessed 2 settlements in Koraput District. Laxmipur (site_001) cleared for Check Dam construction (estimated outlay INR 1.5L - 5.0L). Mundaguda (site_002) vetoed due to slope instability (42° gradient exceeds geotechnical threshold)."
}
```
