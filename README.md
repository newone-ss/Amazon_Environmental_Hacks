# Bhujal

### Hydro-Climatic Decision Support System for Groundwater Recharge and Heat Resilience

Bhujal is an open-source, serverless spatial decision-support platform engineered for district magistrates, block development officers, and watershed planners in mountainous and tribal hard-rock terrains. The platform identifies optimal artificial recharge zones, diagnoses compound heat-water vulnerability, estimates springhead desiccation risks, enforces geotechnical safety vetoes, recommends context-appropriate engineering interventions, estimates indicative capital outlays, and quantifies data uncertainty.

Built for the **Amazon Environmental Hacks 2026 (Heat and Water Track)**.

---

## 1. Executive Summary and Problem Statement

Mountainous and plateau tribal watersheds across central and eastern India—specifically in **Odisha**, **Madhya Pradesh**, and **Jharkhand**—suffer from severe hydro-climatic paradoxes. Despite receiving moderate to heavy annual monsoon precipitation (1,100 mm to 1,600 mm), steep topographic gradients, low secondary porosity in hard-rock granitic, basaltic, and gneissic basements, and rapid surface runoff velocity result in accelerated drainage. Consequently, over 50% of the rural and indigenous population faces acute pre-monsoon drinking water insecurity, perched spring drying, and compounded summer heat distress (MODIS LST >40°C).

Traditional watershed development programs frequently suffer from two critical limitations:
1. **Locational Blindness**: Interventions (such as check dams or percolation tanks) are placed without quantitative verification of slope stability, stream order constraints, fracture permeability, or downstream flood hazards.
2. **False Precision and Unbounded Claims**: Planning software routinely conceals data sparsity or claims black-box "AI" infallibility without communicating hydrogeological confidence intervals.

**Bhujal addresses this gap directly**: *It determines not only where vulnerability exists, but what structure is safe to build, what capital outlay is required under state MGNREGA schedules, and what level of empirical confidence underpins the recommendation.* While prioritizing the critical agro-ecological zones of Madhya Pradesh, Odisha, and Jharkhand, Bhujal's spatial and algorithmic architecture is fully extensible nationwide across All-India watersheds.

---

## 2. Priority Geographic Focus and Areas of Interest (AOI)

Bhujal focuses primarily on three vulnerable agro-ecological zones, while maintaining an extensible architecture across Pan-India:

### 2.1. Odisha (Koraput District)
* **Physiography**: Eastern Ghats mobile belt; elevated plateaus (elevation 300 m to 1,300 m AMSL) dissected by seasonal river valleys.
* **Hydrogeology**: Hard-rock crystalline basement comprising khondalites, charnockites, and granitic gneisses. Groundwater occurs predominantly in weathered zones and fractured networks with limited transmissivity.
* **Demographics and Water Dynamics**: High Scheduled Tribe concentration; deep reliance on gravity-fed springs (*jhola/jharna*) facing seasonal baseflow cessation.

### 2.2. Madhya Pradesh (Mandla, Dindori, Jhabua Districts)
* **Physiography**: Upper Narmada catchment, Satpura-Maikal ranges, and Western Malwa tribal plateau.
* **Hydrogeology**: Deccan Traps layered basaltic lava flows and weathered granitic basements. Porosity and storage depend on vesicular horizons, columnar jointing, and weathered regolith.
* **Demographics and Water Dynamics**: Severe pre-monsoon heat stress (MODIS LST exceeding 42°C), groundwater over-extraction in agricultural belts, and steep scarp runoff.

### 2.3. Jharkhand (Khunti, West Singhbhum Districts)
* **Physiography**: Chota Nagpur plateau and Kolhan upland; undulating terrain with remnant residual hills.
* **Hydrogeology**: Precambrian metamorphic complexes (Singhbhum granite, mica schists, quartzites) with thin saprolite cover and tight fracture networks.
* **Demographics and Water Dynamics**: Significant forest loss in upper recharge zones, rapid post-monsoon water table decline, and extensive tribal rainfed cultivation.

### 2.4. Pan-India Extensibility
* **Unified Geographic Boundary**: Extensible bounding envelope defined in `config/aoi.geojson`.
* **State-Calibrated Parameters**: MGNREGA wage benchmarks (Odisha: INR 350, MP: INR 243, Jharkhand: INR 255, All-India: INR 300) dynamically sourced from `config/costs.yaml`.
* **Lithological Agility**: Scoring engine dynamically handles granites, charnockites, weathered basalts, schists, and alluvial deposits.

---

## 3. System Architecture

Bhujal decouples deterministic spatial hydrogeology from generative contextual synthesis. All calculations, safety verdicts, and cost schedules are computed by verified mathematical models and auditable configuration matrices. Machine learning and generative models are strictly confined to contextual summarization and narrative reporting.

```
                  +---------------------------------------------------+
                  |                 Web Client Layer                  |
                  |     (Vite + React + TypeScript + MapLibre GL)     |
                  +-------------------------+-------------------------+
                                            |
                                            | HTTPS / REST
                                            v
                  +---------------------------------------------------+
                  |            API Gateway (AWS HTTP API)             |
                  +-------------------------+-------------------------+
                                            |
                                            v
                  +---------------------------------------------------+
                  |           Compute Layer: AWS Lambda               |
                  |          FastAPI + Mangum (Python 3.11)           |
                  +-------+-------------------+-------------------+---+
                          |                   |                   |
                          v                   v                   v
     +--------------------------+  +--------------------+  +--------------------+
     | Deterministic Engine     |  | AI Narrative Layer |  | Persistence Layer  |
     | - Recharge Suitability   |  | - Strands SDK      |  | - AWS DynamoDB     |
     | - Heat-Water Stress      |  | - Amazon Bedrock   |  |   (Field Records)  |
     | - Spring Desiccation     |  |   (Claude 3 Sonnet)|  | - AWS S3           |
     | - Geotechnical Veto      |  | - Fallback Engine  |  |   (Photos/Reports) |
     | - Costing and Scenarios  |  +--------------------+  +--------------------+
     +--------------------------+
                  ^
                  |
     +------------+-------------+
     | Configuration Matrices   |
     | (YAML/GeoJSON Contracts) |
     +--------------------------+
```

### Architectural Components

* **Frontend Delivery**: Static web application hosted on Amazon S3 and distributed globally through Amazon CloudFront with Origin Access Control (OAC).
* **Application Ingress**: Amazon API Gateway HTTP API providing low-latency, managed routing with configurable CORS.
* **Serverless Execution**: AWS Lambda container running FastAPI using the Mangum ASGI adapter, configured for 512 MB memory and 30-second execution envelopes.
* **Field Observation Ledger**: Amazon DynamoDB running in on-demand capacity mode (`bhujal-observations`) with single-table indexing on `observation_id` and global secondary indexing on `site_id`.
* **Binary and Report Storage**: Amazon S3 (`bhujal-uploads-<account-id>`) configured with presigned URL upload workflows for field imagery and static report artifacts.
* **Multi-Agent AI Collective**: Seven specialized autonomous domain agents coordinated by an administrative lead orchestrator, backed by Amazon Bedrock (Anthropic Claude 3 Sonnet) and a high-performance deterministic fallback engine:
  1. `HydrogeologyAgent`: Evaluates terrain slope, soil permeability, and fracture lineaments.
  2. `HeatWaterStressAgent`: Diagnoses thermal radiometric anomalies and dry-season water distress.
  3. `SpringshedAgent`: Monitors mountain spring drying hazards and catchment deforestation.
  4. `SafetyAuditorAgent`: Enforces geotechnical slope stability (>35°), landslide, and flood buffer vetoes.
  5. `InterventionComposerAgent`: Tailors civil structures (Check Dams, Percolation Tanks, etc.) with MGNREGA cost ranges.
  6. `ScenarioSimulatorAgent`: Simulates rainfall variations (0.5x to 1.5x) and intervention resilience deltas.
  7. `TelemetryQAAgent`: Inspects field measurements, validates units, and flags physical anomalies.
  * `LeadPlannerOrchestratorAgent`: Chief administrative orchestrator synthesizing specialist briefings into planning action dossiers.

---

## 4. Methodological Framework and Scoring Models

Every score returned by Bhujal satisfies a mandatory schema requiring five parameters: normalized value ($0 \le S \le 100$), classification tier, factor-level weight and contribution breakdown, confidence metadata (level and scalar), and explicit provenance notes.

### 4.1. Groundwater Recharge Suitability ($S_{recharge}$)
Calculated via a multi-criteria weighted linear combination across six surface and subsurface parameters:

$$S_{recharge} = \sum_{i=1}^{n} \left( w_i \cdot x_i \right) \times 100$$

* **Slope Gradient (25%)**: Extracted from SRTM 30m DEM. Flatter slopes receive maximal scores to account for prolonged hydrological residence times.
* **Soil Permeability (20%)**: Derived from ISRIC SoilGrids textural fractions. Coarse, well-draining loams and sandy loams are weighted over dense clay horizons.
* **Monsoon Rainfall Intensity (20%)**: CHIRPS satellite-gauge blended precipitative depth. Moderate intensities favor infiltration over overland sheet wash.
* **LULC Perviousness (15%)**: Reclassified ESRI 10m land cover; closed forests, plantations, and grasslands receive higher weights than compact settlements.
* **Lineament Density (10%)**: Structural fracture traces from ISRO Bhuvan representing secondary porosity conduits.
* **Drainage Density (10%)**: Stream network density derived via D8 flow direction; lower drainage densities denote higher relative infiltration potential.

### 4.2. Heat-Water Vulnerability Score ($S_{stress}$)
A compound metric indexing surface thermal stress, hydrological deficit, and physical access constraints:
* **Land Surface Temperature (25%)**: Summer peak surface radiometric temperature anomalies from MODIS LST (MOD11A2).
* **Summer NDVI (15%)**: Defoliation and moisture deficit signal from MODIS (MOD13A2).
* **Precipitation Deficit (20%)**: Departure from 30-year rainfall normals using CHIRPS precipitation time series.
* **Groundwater Depth (20%)**: Interpolated pre-monsoon static water level surfaces.
* **Distance to Perennial Surface Water (10%)**: Euclidean proximity to verified perennial drainage lines.
* **Population Concentration (10%)**: Demographic demand pressure per square kilometer.

### 4.3. Springhead Desiccation Risk Index ($S_{spring}$)
A specialized morphometric heuristic quantifying the probability of dry-season baseflow cessation:
* **Catchment Area (20%)**: Flow accumulation upstream of the spring discharge orifice.
* **Forest Canopy Loss (20%)**: Hansen Global Forest Change deforestation indices within the contributing recharge area.
* **Mean Upslope Gradient (15%)**: Runoff velocity proxy.
* **Geological Lithology (15%)**: Lithological porosity and fracture matrix ratings from Geological Survey of India (GSI) maps.
* **Monsoon Trend (15%)**: 30-year Mann-Kendall trend of monsoon volume.
* **Springhead Elevation (15%)**: Hypsometric exposure relative to the regional groundwater table.

### 4.4. Geotechnical and Regulatory Safety Engine
Before any civil intervention is approved, the site is evaluated against deterministic veto rules defined in `config/safety_rules.yaml`:
* **Slope Stability Ceiling**: Terrains with gradient $>35^\circ$ immediately trigger `REJECTED` status to avoid structural failure and slope destabilization.
* **Landslide Hazard Buffering**: Sites located in High or Very High GSI susceptibility zones trigger `REJECTED` status.
* **Riparian Flood Hazard**: Locations within 200 m horizontal or 5 m vertical offset of active river channels trigger `REJECTED` status for storage bunding.
* **Ecological Protection**: Protected wildlife zones and biosphere reserves strictly trigger `REJECTED` status.
* **Seismic and Soil Precautions**: High seismic zonation (Zone IV/V) or expansive vertisols issue `CONDITIONAL` clearances demanding modified structural reinforcement.

---

## 5. Repository Layout

```
.
|-- .github/workflows/
|   `-- ci.yml                  # GitHub Actions continuous integration workflow
|-- agent/                      # Autonomous Multi-Agent Collective (Bedrock & Fallback)
|   |-- base.py                 # Abstract base agent and Bedrock runtime wrapper
|   |-- hydrogeology.py         # HydrogeologyAgent (Recharge Analyst)
|   |-- heat_stress.py          # HeatWaterStressAgent (Vulnerability Diagnostician)
|   |-- springshed.py           # SpringshedAgent (Catchment Sentry)
|   |-- safety_auditor.py       # SafetyAuditorAgent (Geotechnical Safety Auditor)
|   |-- intervention_composer.py# InterventionComposerAgent (Civil Structure & Costing Specialist)
|   |-- scenario_simulator.py   # ScenarioSimulatorAgent (Climate Sensitivity Simulator)
|   |-- telemetry.py            # TelemetryQAAgent (Field Telemetry QA Analyst)
|   |-- orchestrator.py         # LeadPlannerOrchestratorAgent (Administrative Orchestrator)
|   `-- report_generator.py     # Administrative Action Dossier HTML Generator
|-- backend/
|   |-- app.py                  # FastAPI application with Mangum AWS Lambda adapter
|   `-- models.py               # Pydantic v2 domain schemas and data contracts
|-- config/
|   |-- aoi.geojson             # Multi-State Area of Interest boundaries (MP, Odisha, Jharkhand, Pan-India)
|   |-- costs.yaml              # State-specific MGNREGA rates (Odisha, MP, Jharkhand) and civil material bounds
|   |-- demo_sites.yaml         # 13 curated settlements across MP, Odisha, and Jharkhand
|   |-- interventions.yaml      # Engineering intervention suitability matrix
|   |-- safety_rules.yaml       # Deterministic geotechnical and regulatory veto logic
|   |-- scenario.yaml           # Rainfall perturbation factors and intervention uplifts
|   `-- weights.yaml            # Analytical scoring factor weights and classification tiers
|-- data/
|   |-- groundwater_level_cleaned_odisha_jharkhand_mp_2021_2025.csv # CGWB empirical telemetry (34,141 rows)
|   |-- imd_max_temperature_odisha_jharkhand_mp_2021_2024.csv       # IMD gridded maximum temperature (109,575 rows)
|   |-- rainfall_cleaned_odisha_jharkhand_mp.csv                    # IMD daily rainfall & departures (5,512 rows)
|   `-- README.md               # Data manifest, licensing records, and provenance ledger
|-- docs/
|   |-- api.md                  # Comprehensive REST API specifications and contract documentation
|   |-- architecture.md         # Detailed AWS infrastructure and component flow specifications
|   |-- assumptions.md          # Scientific and engineering assumptions registry
|   |-- DECISIONS.md            # Formal architectural decision records (ADR)
|   |-- future.md               # Post-MVP enhancement roadmap
|   `-- validation.md           # Verification, testing, and validation methodology
|-- infra/
|   `-- template.yaml           # AWS Serverless Application Model (SAM) CloudFormation template
|-- pipeline/                   # Offline geospatial acquisition, reprojection, and feature extraction
|   |-- download/               # Raster and vector dataset retrieval modules
|   |-- preprocess/             # Alignment, clipping, and coordinate transformation routines
|   `-- features/               # Morphometric and hydro-climatic feature generators
|-- scoring/                    # Deterministic spatial hydrogeology and safety veto engine
|   |-- recharge.py             # Multi-criteria infiltration suitability overlay
|   |-- stress.py               # Compound heat-water vulnerability calculator
|   |-- springs.py              # Springhead desiccation risk index
|   |-- safety.py               # Deterministic geotechnical veto engine
|   |-- interventions.py        # Civil structure matching & state-calibrated costing
|   |-- simulator.py            # Rainfall perturbation & intervention uplift simulator
|   |-- engine.py               # Unified spatial evaluation engine
|   `-- run.py                  # Standalone batch site evaluation runner
|-- tests/
|   |-- test_models.py          # Pytest verification suite for API and data contracts
|   |-- test_scoring.py         # Pytest suite for scoring, safety veto, and simulation
|   |-- test_agents.py          # Pytest suite for autonomous multi-agent collective
|   `-- test_api.py             # Pytest suite for FastAPI REST endpoints and state filters
|-- main.py                     # Unified Command-Line Interface (list, evaluate, simulate, report, server)
|-- Makefile                    # Standardized automation interface
|-- requirements.txt            # Python dependencies with pinned semver constraints
`-- agent.md                    # Core operational directives and constraints
```

---

## 6. Getting Started

### Prerequisites

* Python 3.11 or later
* Node.js 18 or later
* AWS CLI v2 configured with appropriate IAM permissions
* AWS SAM CLI (v1.100+)

### Local Environment Setup

1. Clone the repository and enter the workspace:
   ```bash
   git clone https://github.com/newone-ss/Amazon_Environmental_Hacks.git
   cd Amazon_Environmental_Hacks
   ```

2. Establish and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Configure local environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your target AWS Region and account identifiers
   ```

4. Execute static code quality and validation tests:
   ```bash
   ruff check .
   ruff format --check .
   pytest tests/ -v --tb=short
   ```

5. Command-Line Interface (CLI):
   ```bash
   # Enumerate settlements across all states, or filter by specific priority state
   python main.py list
   python main.py list --state "Madhya Pradesh"
   python main.py list --state "Jharkhand"
   python main.py list --state "Odisha"

   # Perform comprehensive multi-criteria hydro-climatic analysis
   python main.py evaluate site_001        # Odisha: Laxmipur (Safe, cleared for civil works)
   python main.py evaluate site_mp_001     # Madhya Pradesh: Bichhiya (Safe, basaltic/alluvial recharge)
   python main.py evaluate site_jh_004     # Jharkhand: Porahat Scarp (Vetoed: slope >35° and landslide hazard)

   # Execute climate scenario simulation (-20% rainfall with check dam)
   python main.py simulate site_001 --rainfall 0.8 --intervention check_dam

   # Generate multi-state administrative action dossier across settlements
   python main.py report --sites site_001,site_mp_001,site_jh_001
   ```

6. Launch local API server:
   ```bash
   python main.py server --port 8000
   ```

---

## 7. Data Provenance and Integrity Standards

Bhujal maintains a strict empirical honesty policy:
* **No Fabricated Information**: All baseline data is retrieved from verified institutional sources or clearly tagged.
* **Provenance Badging**:
  * `real`: Measured, verified ground-truth data or high-resolution instrument observations (e.g. CGWB 2021–2025 water levels, IMD 2021–2024 temperatures, IMD daily rainfall).
  * `proxy`: Spatially interpolated or indirect variables (e.g., IDW-interpolated well surfaces).
  * `illustrative`: Curated synthetic profiles demonstrating platform behavior during evaluation across edge cases.
* **Transparent Terminology**: The platform describes multi-criteria overlays as *transparent deterministic scoring*, reserving AI terminology exclusively for natural language synthesis through Amazon Bedrock.

---

## 8. Acknowledgements and Data Sources

* **Central Ground Water Board (CGWB)**: National hydrogeological frameworks and 34,141 validated observation well telemetry records (2021–2025) across Odisha, Jharkhand, and Madhya Pradesh.
* **India Meteorological Department (IMD)**: Gridded daily maximum surface temperatures (109,575 records, 2021–2024), 5,512 daily rainfall departure observations, and long-term precipitation normals.
* **Geological Survey of India (GSI)**: Regional lithological units (Eastern Ghats crystalline complex, Deccan Traps basalts, Chota Nagpur metamorphic belt) and national landslide susceptibility zonation.
* **ISRO Bhuvan**: National Land Use / Land Cover (LULC) and structural lineament spatial databases.
* **NASA / USGS**: Shuttle Radar Topography Mission (SRTM 30m) DEM and MODIS radiometric observations (LST MOD11A2, NDVI MOD13A2).
* **UC Santa Barbara Climate Hazards Center**: CHIRPS precipitation climatology time series.
* **ISRIC World Soil Information**: SoilGrids 250m global soil physical properties.
* **World Resources Institute / Hansen**: Global Forest Change tree canopy disturbance datasets.

---

## 9. License

This project is licensed under the MIT License. See `LICENSE` for details.