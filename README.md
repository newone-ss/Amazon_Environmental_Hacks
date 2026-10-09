# 💧 Bhujal

> **Not just where the problem is, but what is safe to build and how sure we are.**

Bhujal is a decision-support tool for block and district planners in hilly and tribal areas. It identifies where monsoon water can be recharged, which villages face heat-water stress, which springs risk drying, what intervention suits a site, whether it is safe to build there, an indicative cost, and a confidence level.

**Amazon Environmental Hacks 2026 — Heat and Water Track**

---

## 🎯 Demo Area

**Koraput District, Odisha** — Eastern Ghats, tribal population >50%, spring-fed villages, monsoon-dependent.

## 🏗️ Architecture

```
Frontend (S3+CloudFront) → API Gateway → Lambda (FastAPI) → Scoring Engine + Bedrock Agent
                                                          → DynamoDB (observations)
                                                          → S3 (photos, reports)
```

See [docs/architecture.md](docs/architecture.md) for details.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- AWS CLI configured
- AWS SAM CLI

### Setup
```bash
# Clone and enter
git clone <repo-url>
cd Amazon_Environmental_Hacks

# Python environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Edit .env with your AWS credentials and settings

# Run tests
make test

# Start dev servers
make dev
```

### Data Pipeline
```bash
# Download, preprocess, and extract features
make data

# Run scoring
make score
```

### Deploy
```bash
make deploy
```

## 📋 API

See [docs/api.md](docs/api.md) for the full API contract.

## 📁 Project Structure

```
config/          — AOI, weights, safety rules, interventions, costs, scenarios
pipeline/        — Data download, preprocessing, feature extraction
scoring/         — Deterministic scoring engine
backend/         — FastAPI + Mangum (Lambda-ready)
agent/           — Strands Agents SDK + Bedrock integration
frontend/        — Vite + React + TypeScript + MapLibre
infra/           — AWS SAM templates
data/            — Data manifest (no raw data committed)
tests/           — pytest test suite
docs/            — Decisions, assumptions, validation, architecture
```

## 📊 Scoring

Every score returns: **value** (0-100), **class**, **drivers[]** (factor, weight, contribution), **confidence** (level + numeric), and **data_quality_note**. See [agent.md](agent.md) Rule 4.

Scores are computed by deterministic code driven by config YAML. The LLM never decides scores — it only explains them.

## ⚖️ Honesty Policy

- Real data is labelled `real`
- Proxy data (e.g., interpolated groundwater depth) shows a `Proxy` badge
- Illustrative/synthetic data shows an `Illustrative` badge
- Weighted overlays are called "transparent scoring", not "AI"

## 📄 License

MIT

## 🙏 Acknowledgements

- ISRO Bhuvan, CGWB, IMD, GSI for Indian geospatial data
- NASA SRTM, CHIRPS, MODIS, Hansen GFC for global datasets
- ESRI Living Atlas for 10m land cover
- ISRIC SoilGrids for soil data