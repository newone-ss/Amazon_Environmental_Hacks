# Architecture

> System architecture for Bhujal.

---

## High-Level Overview

```
┌──────────────┐     ┌───────────────┐     ┌──────────────────┐
│   Frontend   │────▶│   API Gateway  │────▶│  Lambda (FastAPI) │
│  (S3 + CF)   │     │               │     │    via Mangum     │
│  React/TS    │     └───────────────┘     └────────┬─────────┘
│  MapLibre    │                                     │
└──────────────┘                           ┌────────┴─────────┐
                                           │                   │
                                    ┌──────▼──────┐    ┌──────▼──────┐
                                    │  Scoring     │    │  Agent      │
                                    │  Engine      │    │  (Strands + │
                                    │  (Python)    │    │   Bedrock)  │
                                    └──────┬──────┘    └──────┬──────┘
                                           │                   │
                                    ┌──────▼──────┐    ┌──────▼──────┐
                                    │ Config YAML  │    │  DynamoDB   │
                                    │ (weights,    │    │  (obs.)     │
                                    │  safety,     │    │             │
                                    │  costs)      │    │  S3         │
                                    └─────────────┘    │  (photos,   │
                                                       │   reports)  │
                                                       └─────────────┘
```

## Data Flow

1. **Pipeline** (offline): Downloads rasters → preprocesses → extracts features → writes scored GeoJSON
2. **Backend** (online): Reads scored GeoJSON, applies safety rules, composes interventions, runs scenarios
3. **Agent** (online): Takes score outputs → generates natural-language explanations and reports via Bedrock
4. **Frontend** (browser): Fetches from API → renders map, panels, charts, forms

## Key Design Principles

- **Determinism**: All scores computed by code + config. LLM never decides scores.
- **Transparency**: Every score shows its drivers, weights, and confidence.
- **Honesty**: Proxy/illustrative data is always badged.
- **Config-driven**: Thresholds, weights, costs in YAML — changeable without code changes.
