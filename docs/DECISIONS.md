# Architectural Decision Records (ADR)

> **Standard**: Modified Nygard ADR Format  
> **Status**: Active Project Architecture Log  
> **Repository Context**: Bhujal Spatial Decision Support Platform

---

## ADR Index

* [ADR-001: Selection of Koraput District, Odisha as Demonstration Area](#adr-001-selection-of-koraput-district-odisha-as-demonstration-area)
* [ADR-002: Enforcement of Five-Field Scoring Schema at Type Level](#adr-002-enforcement-of-five-field-scoring-schema-at-type-level)
* [ADR-003: Externalized Declarative Configuration for Safety and Weights](#adr-003-externalized-declarative-configuration-for-safety-and-weights)
* [ADR-004: Indicative Cost Range Modeling with Explicit Assumptions](#adr-004-indicative-cost-range-modeling-with-explicit-assumptions)
* [ADR-005: Empirical Honesty Protocols and Explicit Provenance Badging](#adr-005-empirical-honesty-protocols-and-explicit-provenance-badging)
* [ADR-006: Serverless Architecture Over Relational and PostGIS Infrastructure](#adr-006-serverless-architecture-over-relational-and-postgis-infrastructure)
* [ADR-007: Complete Isolation of Quantitative Scoring from Generative AI](#adr-007-complete-isolation-of-quantitative-scoring-from-generative-ai)
* [ADR-008: Expansion to Multi-State Focus (Odisha, Madhya Pradesh, Jharkhand) with Pan-India Extensibility](#adr-008-expansion-to-multi-state-focus-odisha-madhya-pradesh-jharkhand-with-pan-india-extensibility)

---

### ADR-001: Selection of Koraput District, Odisha as Demonstration Area
* **Date**: 2026-10-09
* **Status**: Accepted
* **Context**: The hackathon evaluation demands a focused, high-impact demonstration rather than a broad, shallow multi-state prototype. The target landscape required complex topography, vulnerable indigenous demographics, acute dry-season water stress, and active perched springs.
* **Decision**: Confine all demonstration pipelines, validations, and interactive visualizations to Koraput District in southern Odisha (bounding envelope: 82.05°E–83.40°E, 18.25°N–19.30°N).
* **Consequences**:
  * Positive: Enables deep hydrogeological modeling and high-fidelity contextual calibration against Eastern Ghats hard-rock geomorphology.
  * Negative: The bounding envelope simplifies the political district boundary; multi-district scalability is deferred to post-MVP.

---

### ADR-002: Enforcement of Five-Field Scoring Schema at Type Level
* **Date**: 2026-10-09
* **Status**: Accepted
* **Context**: Watershed planners require complete visibility into why a particular score was assigned and how much confidence can be placed in it. Opaque scalar outputs risk misallocating public capital.
* **Decision**: Mandate that all scoring functions emit a unified `ScoreResult` schema featuring five compulsory properties: `value`, `score_class`, `drivers` (factor, weight, contribution), `confidence` (level, numeric), and `data_quality_note`. Enforce this contract at the compile/type layer via Pydantic v2.
* **Consequences**:
  * Positive: Guarantees full auditability and explanatory transparency across all frontend views and report dossiers.
  * Negative: Minor serialization overhead compared to raw floating-point scalar responses.

---

### ADR-003: Externalized Declarative Configuration for Safety and Weights
* **Date**: 2026-10-09
* **Status**: Accepted
* **Context**: Civil safety limits (e.g., maximum buildable slope gradients) and hydrological weighting matrices must be reviewed and modified by geotechnical and watershed specialists without touching Python source code.
* **Decision**: Externalize all factor weights, safety rules, intervention constraints, and costing schedules into structured YAML files within `config/`.
* **Consequences**:
  * Positive: Zero code modification required for domain parameter calibration; easily audited by external review panels.
  * Negative: Requires robust schema validation on startup to prevent malformed YAML runtime exceptions.

---

### ADR-004: Indicative Cost Range Modeling with Explicit Assumptions
* **Date**: 2026-10-09
* **Status**: Accepted
* **Context**: Topographical heterogeneity and variable haulage distances in remote hilly terrain make tender-grade bill-of-quantities (BOQ) calculations impossible without detailed on-site topographical surveys.
* **Decision**: Represent financial projections strictly as indicative ranges (low–high in INR) accompanied by person-day labour allocations, required material categories, and explicit engineering assumptions calibrated to Odisha MGNREGA schedules of rates.
* **Consequences**:
  * Positive: Sets realistic expectations for administrative planners; transparently communicates pricing bounds.
  * Negative: Requires explicit UI disclaimers that values are preliminary estimates rather than binding contracts.

---

### ADR-005: Empirical Honesty Protocols and Explicit Provenance Badging
* **Date**: 2026-10-09
* **Status**: Accepted
* **Context**: Hackathon projects frequently synthesize ungrounded data and present it as empirical measurement, compromising scientific credibility.
* **Decision**: Classify and visibly badge every data asset and model output as `real`, `proxy`, or `illustrative`. Prohibit the use of "AI" marketing terminology for standard multi-criteria weighted linear combinations.
* **Consequences**:
  * Positive: Establishes uncompromising scientific integrity and operational credibility with technical judges.
  * Negative: Precludes marketing simplifications.

---

### ADR-006: Serverless Architecture Over Relational and PostGIS Infrastructure
* **Date**: 2026-10-09
* **Status**: Accepted
* **Context**: Deploying, provisioning, and maintaining a relational database server with PostGIS extensions introduces substantial infrastructure complexity, idle costs, and deployment latency within a rapid development envelope.
* **Decision**: Use an event-driven serverless topology combining AWS Lambda (FastAPI/Mangum), Amazon API Gateway, Amazon DynamoDB (on-demand observations ledger), and static S3/GeoJSON spatial datasets.
* **Consequences**:
  * Positive: Zero base idle costs, sub-second deployment cycles via AWS SAM, and infinite elastic scale.
  * Negative: Complex ad-hoc spatial SQL queries are not supported; vector operations must be performed in-memory via Shapely/GeoPandas or pre-computed offline.

---

### ADR-007: Complete Isolation of Quantitative Scoring from Generative AI
* **Date**: 2026-10-09
* **Status**: Accepted
* **Context**: Large Language Models are prone to stochastic hallucinations, making them unsafe for geotechnical safety vetoes or structural engineering clearances.
* **Decision**: Confine all numerical evaluations, safety verdicts, and cost schedules strictly to deterministic algorithms. Deploy Amazon Bedrock (Claude 3 Sonnet) strictly downstream to compile deterministic outputs into human-readable planning briefs and administrative dossiers.
* **Consequences**:
  * Positive: Absolute mathematical reproducibility, zero hallucination of safety hazards, and auditable governance.
  * Negative: Limits the generative model's scope to summarization and translation tasks.

---

### ADR-008: Expansion to Multi-State Focus (Odisha, Madhya Pradesh, Jharkhand) with Pan-India Extensibility
* **Date**: 2026-10-10
* **Status**: Accepted (Expands and operationalizes the single-district prototype of ADR-001)
* **Context**: While Koraput District provided a rigorous testing ground for steep-relief granitic and charnockitic hard-rock terrains, indigenous water insecurity across India spans multiple distinct hydrogeological formations. In particular, the Deccan Traps weathered basalts in Madhya Pradesh (Mandla, Dindori, Jhabua) and the Chota Nagpur Precambrian crystalline metamorphic basement in Jharkhand (Khunti, West Singhbhum) present urgent, distinct hydrological dynamics. Administrative planners require an engine capable of handling variable state MGNREGA labour schedules and multi-regional lithological permeability matrices.
* **Decision**:
  1. Expand the primary operational Area of Interest to encompass representative priority watersheds across **Madhya Pradesh**, **Odisha**, and **Jharkhand**.
  2. Maintain a Pan-India bounding envelope in `config/aoi.geojson` and design all spatial evaluation and safety routines to be extensible nationwide across all 700+ districts of India.
  3. Externalize state-specific MGNREGA wage benchmarks into `config/costs.yaml` (Odisha: INR 350, MP: INR 243, Jharkhand: INR 255, All-India: INR 300) and support state filtering in REST endpoints (`GET /villages?state=<State>`).
  4. Ingest 13 curated settlements across the three focus states into `config/demo_sites.yaml` covering all safety, lithological, and scoring branches.
* **Consequences**:
  * Positive: Delivers direct planning utility across three high-priority tribal states while demonstrating nationwide scalability for central government ministries (Jal Shakti, MoRD, MoTA).
  * Negative: Requires maintenance of multi-state lithological matrices and state-specific labour wage tables.
