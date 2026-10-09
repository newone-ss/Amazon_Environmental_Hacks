# Bhujal API Contract

> **Base URL**: `https://<api-gateway-id>.execute-api.<region>.amazonaws.com/prod`
> **Content-Type**: `application/json`
> **Auth**: None (hackathon demo)

---

## Endpoints

### `GET /meta`
System metadata and AOI info.

**Response**: `MetaResponse`
```json
{
  "version": "0.1.0",
  "aoi_name": "Koraput District",
  "aoi_state": "Odisha",
  "total_villages": 5,
  "scoring_weights_hash": "a1b2c3...",
  "data_tags_in_use": ["illustrative"],
  "last_pipeline_run": "2026-10-09T12:00:00Z"
}
```

---

### `GET /villages`
List all villages in the AOI with basic metadata.

**Response**: `Village[]`
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
    "elevation_m": 580,
    "population": 1200,
    "has_spring": true,
    "data_tag": "illustrative"
  }
]
```

---

### `GET /sites/{site_id}`
Full site detail: scores, safety verdict, and recommendations.

**Path params**: `site_id` (string)

**Response**: `Site`
```json
{
  "village": { "id": "site_001", "name": "Laxmipur", "..." : "..." },
  "scores": [
    {
      "score_type": "recharge_score",
      "value": 62.5,
      "score_class": "good",
      "drivers": [
        { "factor": "slope", "weight": 0.25, "contribution": 18.75 },
        { "factor": "soil_permeability", "weight": 0.20, "contribution": 14.0 }
      ],
      "confidence": { "level": "medium", "numeric": 0.65 },
      "data_quality_note": "Soil data from SoilGrids 250m; slope from SRTM 30m",
      "data_tag": "illustrative"
    }
  ],
  "safety": {
    "status": "SAFE",
    "rule_ids": [],
    "reasons": [],
    "rules_evaluated": [
      { "rule_id": "SLOPE_STEEP", "triggered": false, "verdict": "SAFE", "reason": "" }
    ]
  },
  "recommendations": [
    {
      "intervention_id": "check_dam",
      "intervention_name": "Check Dam (Nala Bund)",
      "category": "recharge",
      "dimensions": { "length_m": 10, "height_m": 2, "width_m": 3 },
      "materials": ["stone masonry", "cement", "gabion wire"],
      "labour_days": 45,
      "cost_range_inr": { "low": 150000, "high": 500000 },
      "assumptions": ["Slope < 15°", "Stream order ≤ 3"],
      "suitability_score": 0.82
    }
  ]
}
```

---

### `POST /scenario`
Run a what-if rainfall scenario for a site.

**Request**: `ScenarioRequest`
```json
{
  "site_id": "site_001",
  "rainfall_fraction": 0.7,
  "include_intervention": "check_dam"
}
```

**Response**: `ScenarioResult`
```json
{
  "site_id": "site_001",
  "baseline_scores": [ "..." ],
  "adjusted_scores": [ "..." ],
  "rainfall_mm_baseline": 1400,
  "rainfall_mm_adjusted": 980,
  "intervention_applied": "check_dam",
  "notes": ["Linear sensitivity model applied", "Intervention uplift added"]
}
```

---

### `POST /recommendation`
Get recommended interventions for a site.

**Request**:
```json
{
  "site_id": "site_001"
}
```

**Response**: `Recommendation[]`

---

### `POST /observations`
Submit a field observation.

**Request**: `ObservationCreate`
```json
{
  "site_id": "site_001",
  "observer_name": "Ramesh",
  "observation_type": "spring_flow",
  "value": 2.5,
  "unit": "litres_per_second",
  "notes": "Flow measured at outlet pipe",
  "photo_filename": "spring_001.jpg"
}
```

**Response**: `Observation` (with generated `observation_id`, `timestamp`, `photo_url`)

---

### `GET /observations?site_id={site_id}`
List observations for a site.

**Query params**: `site_id` (optional — if omitted, returns all)

**Response**: `Observation[]`

---

### `POST /report`
Generate a planner-ready action report.

**Request**: `ReportRequest`
```json
{
  "site_ids": ["site_001", "site_002"],
  "include_scenario": true,
  "rainfall_fraction": 0.8
}
```

**Response**: `ReportResult`
```json
{
  "report_id": "rpt_20261009_001",
  "title": "Bhujal Action Report — Koraput District",
  "generated_at": "2026-10-09T15:30:00Z",
  "site_count": 2,
  "download_url": "https://bhujal-uploads.s3.amazonaws.com/reports/rpt_20261009_001.html?...",
  "format": "html",
  "summary": "2 sites assessed. 1 suitable for check dam, 1 rejected (steep slope)."
}
```

---

## Error Format

All errors return:
```json
{
  "detail": "Human-readable error message"
}
```

Standard HTTP status codes: `200`, `201`, `400`, `404`, `500`.

---

## Notes

- All models are defined in [`backend/models.py`](../backend/models.py)
- Scores follow the schema in Rule 4 of [`agent.md`](../agent.md)
- No authentication for the hackathon demo
- CORS is open to `http://localhost:5173` in dev and the CloudFront domain in prod
