# Bhujal: Cloud and System Architecture Specification

> **Classification**: System Architecture Document (SAD)  
> **Target Cloud Environment**: Amazon Web Services (AWS)  
> **Deployment Model**: Fully Serverless, Event-Driven Architecture

---

## 1. Architectural Principles and Design Goals

The Bhujal system architecture balances high-throughput spatial indexing with sub-second decision support on a serverless cost envelope. The platform is designed around five core tenets:

1. **Strict Decoupling of Determinism and Generative AI**: Numerical hydrogeology, multi-criteria spatial scoring, and safety veto rules are computed exclusively by deterministic algorithms. Large Language Models (LLMs) operate strictly downstream as contextual narrative generators.
2. **Serverless Scalability**: Zero standing virtual machines or always-on database instances. All compute terminates after request fulfillment.
3. **Edge Optimization**: Global low-latency static delivery through CloudFront CDN with strict Origin Access Control (OAC).
4. **Transparent Provability**: All scoring parameters and cost matrices reside in declarative configuration files rather than hard-coded application binaries.
5. **Least-Privilege Security**: Minimal IAM scopes per resource, presigned URL authorization for object storage, and zero committed credentials.

---

## 2. Global Topology and Component Diagram

```
+---------------------------------------------------------------------------------------------------+
| CLIENT LAYER                                                                                      |
|                                                                                                   |
|   +-------------------------------------------------+                                             |
|   | Browser Single Page Application (SPA)           |                                             |
|   | - React 18 + TypeScript + MapLibre GL + Recharts|                                             |
|   +------------------------+------------------------+                                             |
+----------------------------|----------------------------------------------------------------------+
                             |
         Static Assets (GET) |                       REST / JSON Payloads
                             v                                |
+-------------------------------------------------------------|-------------------------------------+
| EDGE & INGRESS (AWS)                                        |                                     |
|                                                             v                                     |
|   +--------------------------+              +-------------------------------+                     |
|   | Amazon CloudFront (CDN)  |              | Amazon API Gateway (HTTP API) |                     |
|   | - TLS 1.3 Termination    |              | - CORS Handling               |                     |
|   | - Global Edge Caching    |              | - Automatic Stage Deployment  |                     |
|   +------------+-------------+              +---------------+---------------+                     |
+----------------|--------------------------------------------|-------------------------------------+
                 | (OAC Read)                                 |
                 v                                            v
+------------------------------------+        +-----------------------------------------------------+
| STORAGE: STATIC HOSTING            |        | COMPUTE RUNTIME: AWS LAMBDA                         |
|                                    |        |                                                     |
|   +----------------------------+   |        |   +---------------------------------------------+   |
|   | Amazon S3 (Frontend Bucket)|   |        |   | Lambda Function: bhujal-backend             |   |
|   | - Versioned Artifacts      |   |        |   | - Python 3.11 Runtime (512 MB, 30s timeout) |   |
|   | - OAC Bucket Policy        |   |        |   | - Mangum ASGI Adapter + FastAPI Router      |   |
|   +----------------------------+   |        |   +----------------------+----------------------+   |
+------------------------------------+        +--------------------------|--------------------------+
                                                                         |
                                    +------------------------------------+--------------------------+
                                    |                                    |                          |
                                    v                                    v                          v
+---------------------------------------+  +---------------------------------+  +-------------------+
| PERSISTENCE: OBSERVATIONS             |  | PERSISTENCE: MEDIA & REPORTS    |  | GENERATIVE AI     |
|                                       |  |                                 |  |                   |
|   +-------------------------------+   |  |   +-------------------------+   |  |   +-------------+ |
|   | Amazon DynamoDB               |   |  |   | Amazon S3 (Uploads)     |   |  |   | Amazon      | |
|   | - Table: bhujal-observations  |   |  |   | - Presigned Photo Ingest|   |  |   | Bedrock     | |
|   | - PK: observation_id (String) |   |  |   | - Action Dossier Storage|   |  |   | - Claude 3  | |
|   | - GSI: site_id (String)       |   |  |   | - 30-Day Lifecycle Exp. |   |  |   |   Sonnet    | |
|   | - On-Demand Capacity Mode     |   |  |   +-------------------------+   |  |   +-------------+ |
|   +-------------------------------+   |  +---------------------------------+  +-------------------+
+---------------------------------------+
```

---

## 3. Subsystem Specifications

### 3.1. Edge Delivery Subsystem
* **Amazon CloudFront Distribution**: Serves the compiled single-page application from edge points of presence.
* **Origin Access Control (OAC)**: Enforces cryptographic verification between CloudFront and the origin bucket (`FrontendBucket`), completely eliminating public S3 read permissions.
* **Custom Error Responses**: Reroutes `403 Forbidden` and `404 Not Found` responses to `/index.html` with HTTP 200 to enable client-side React Router navigation.

### 3.2. Application Ingress Subsystem
* **Amazon API Gateway (HTTP API v2)**: Provides managed, low-latency entry for all dynamic routes.
* **Payload Proxying**: Proxies all incoming requests under the `/{proxy+}` route directly to the AWS Lambda function.
* **CORS Configuration**: Handles pre-flight `OPTIONS` requests at the API Gateway layer, whitelisting local development (`http://localhost:5173`) and the canonical CloudFront distribution domain.

### 3.3. Serverless Compute Subsystem
* **AWS Lambda Function (`BhujalFunction`)**:
  * **Runtime**: Python 3.11.
  * **Adapter**: `mangum` translating API Gateway v2 payloads into ASGI events.
  * **Memory Configuration**: 512 MB, providing a balanced cost-to-performance profile and sufficient CPU allocation for fast raster feature array manipulation.
  * **Execution Timeout**: 30 seconds.
  * **Environment Isolation**: Parameterized via CloudFormation template variables (`DYNAMODB_TABLE_OBSERVATIONS`, `S3_BUCKET_UPLOADS`, `BEDROCK_MODEL_ID`).

### 3.4. State and Media Persistence Subsystems
* **Amazon DynamoDB (`ObservationsTable`)**:
  * Manages crowd-sourced ground-truth observations and telemetry logs.
  * **Partition Key**: `observation_id` (UUIDv4).
  * **Global Secondary Index (GSI)**: `site-index` partitioned by `site_id`, enabling constant-time queries for village-specific observation histories.
  * **Capacity Management**: Pay-Per-Request (on-demand billing) ensuring zero base idle costs.
* **Amazon S3 (`UploadsBucket`)**:
  * S3 bucket designated for user-uploaded site photographs and generated HTML/PDF action dossiers.
  * Uploads utilize short-lived (15-minute) AWS SigV4 presigned PUT URLs generated by Lambda, isolating binary ingest from API compute.

### 3.5. Multi-Agent Intelligence and Contextual Synthesis Subsystem
The AI layer is architected as an autonomous multi-agent collective consisting of seven specialized domain agents coordinated by an administrative lead orchestrator:

* **Agent 1: Hydrogeological Recharge Analyst (`HydrogeologyAgent`)**: Analyzes multi-spectral slope, soil permeability, rainfall intensity, and fracture lineaments to diagnose spatial infiltration corridors.
* **Agent 2: Heat-Water Vulnerability Diagnostician (`HeatWaterStressAgent`)**: Evaluates compound pre-monsoon Land Surface Temperature (MODIS LST) anomalies, vegetation defoliation (NDVI), and hydrological access constraints.
* **Agent 3: Springhead Catchment Sentry (`SpringshedAgent`)**: Evaluates perched spring vulnerability, upslope deforestation in Hansen GFC layers, and baseflow recession risks.
* **Agent 4: Geotechnical Safety Auditor (`SafetyAuditorAgent`)**: Enforces deterministic slope stability (>35°), GSI landslide zones, riparian flood buffers, and BIS hill construction codes.
* **Agent 5: Civil Engineering & Costing Specialist (`InterventionComposerAgent`)**: Matches site constraints to civil structures (Check Dams, Percolation Tanks, Contour Trenches, Springshed Management) and estimates MGNREGA labour person-days and cost bounds.
* **Agent 6: Climate Sensitivity & Scenario Simulator (`ScenarioSimulatorAgent`)**: Simulates rainfall perturbations (0.5x drought to 1.5x flood) and quantifies the protective resilience uplift provided by proposed interventions.
* **Agent 7: Field Telemetry & Ground-Truth QA Agent (`TelemetryQAAgent`)**: Inspects field hydrometric measurements, validates telemetry units, detects physical anomalies, and updates longitudinal records.
* **Lead Orchestrator: District Planning Cell Orchestrator (`LeadPlannerOrchestratorAgent`)**: Synthesizes specialist briefings, reconciles safety vetoes with investment priorities, and generates publication-grade planning dossiers.

* **Amazon Bedrock Integration**:
  * **Model ID**: `anthropic.claude-3-sonnet-20240229-v1:0`.
  * **Policy**: Scoped strictly to `bedrock:InvokeModel`.
  * **Deterministic Fallback Engine**: If AWS credentials are absent or Bedrock encounters network timeouts, agents automatically degrade to deterministic template synthesizers, ensuring 100% operational availability.

---

## 4. End-to-End Execution Workflows

### 4.1. Spatial Evaluation Sequence (`GET /sites/{site_id}`)
1. Client requests site analysis from API Gateway.
2. Lambda retrieves village geographic metadata from `config/demo_sites.yaml` or scored GeoJSON.
3. Scoring Engine loads active weights from `config/weights.yaml` and executes multi-criteria linear combinations.
4. Safety Engine evaluates geotechnical conditions against `config/safety_rules.yaml`. If any `REJECTED` rule triggers, status is vetoed immediately.
5. Intervention Composer matches topographic, soil, and catchment parameters against `config/interventions.yaml`, associating state-calibrated MGNREGA cost ranges from `config/costs.yaml` based on settlement state (Odisha, Madhya Pradesh, Jharkhand, or Pan-India baseline).
6. Aggregated Pydantic `Site` model is serialized to JSON and returned to the client.

### 4.2. Field Observation Ingestion (`POST /observations`)
1. Enumerator captures telemetry or photographs at a field location.
2. Client sends metadata to `POST /observations`.
3. Lambda writes record to DynamoDB with a unique `observation_id` and timestamp.
4. If a photograph filename is specified, Lambda signs an S3 presigned PUT URL and returns it in the response payload.
5. Client uploads binary photograph directly to S3 via the presigned URL.

### 4.3. Action Dossier Generation (`POST /report`)
1. Planner submits portfolio of site IDs (covering single or multiple districts/states).
2. Lead Planner Orchestrator Agent assesses each site, invoking domain specialists (`HydrogeologyAgent`, `HeatWaterStressAgent`, `SpringshedAgent`, `SafetyAuditorAgent`, `InterventionComposerAgent`).
3. If Bedrock credentials are unavailable, high-performance deterministic fallback templates synthesize the administrative briefing.
4. Publication-grade HTML action dossier is generated, saved to `data/reports/`, and served via `/reports/{filename}` or presigned S3 URL.

---

## 5. Security and Compliance Controls

* **Zero Committed Secrets**: Sensitive identifiers, access keys, and account IDs are read dynamically from runtime IAM instance profiles or `.env`.
* **IAM Least Privilege**:
  * `DynamoDBCrudPolicy` scoped strictly to `ObservationsTable`.
  * `S3CrudPolicy` scoped strictly to `UploadsBucket`.
  * Scoped Bedrock model invocation permissions.
* **Network Segregation**: Pure serverless constructs eliminate the need for VPC peering, NAT Gateways, or bastion hosts for MVP operations, drastically reducing vulnerability surface area and deployment latency.

---

## 6. Deployed API URL

After deploying the backend via AWS SAM, the API Gateway endpoint URL can be found in the CloudFormation stack outputs or recorded here:

API_URL: https://<api-id>.execute-api.<region>.amazonaws.com/<stage>

This URL is used for testing with the smoke script and for frontend configuration.
