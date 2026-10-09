# Verification and Validation (V&V) Protocol

> **Standard**: Scientific and Software Quality Assurance Protocol  
> **Application**: Verification of Data Contracts, Physical Plausibility, and Geotechnical Invariants

---

## 1. Quality Assurance Framework

The Bhujal verification and validation framework ensures mathematical correctness, physical plausibility, and software contract integrity across four systematic tiers:

```
+-----------------------------------------------------------------------------------+
| TIER 1: SOFTWARE CONTRACT VERIFICATION (Automated Unit & Contract Tests)         |
| Schema bounds, serialization invariants, type enforcement, and nullability checks  |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| TIER 2: HYDROGEOLOGICAL SANITY CHECKS (Boundary Condition Verification)           |
| Extreme physical value testing, monotonicity assertions, and veto invariance      |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| TIER 3: SENSITIVITY AND STABILITY ANALYSIS (Perturbation Testing)                 |
| Factor step responses, rainfall scaling invariants, and numerical convergence     |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| TIER 4: EXTERNAL SCIENTIFIC BENCHMARKING (Empirical Validation)                   |
| Cross-referencing against CGWB observation well hydrographs and IMD heat records  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Verification Tiers

### 2.1. Tier 1: Software Contract Verification
* **Scope**: Automated execution of the pytest test suite against all Pydantic schemas in [`backend/models.py`](../backend/models.py).
* **Test Criteria**:
  * **Score Bounds Invariance**: Any composite score $< 0.0$ or $> 100.0$ must raise a validation error.
  * **Contract Completeness**: Every score must serialize all five required fields (`value`, `score_class`, `drivers`, `confidence`, `data_quality_note`).
  * **Serialization Round-Trip**: Models must serialize to and deserialize from JSON without loss of numeric precision or enum values.
  * **Input Constraint Enforcement**: Bounds such as `rainfall_fraction` ($0.5 \le F \le 1.5$) must reject out-of-range payloads with HTTP 422.

### 2.2. Tier 2: Hydrogeological and Geotechnical Sanity Invariants
* **Scope**: Evaluation of physical logic against synthetic edge cases.
* **Invariant Assertions**:
  * **Slope Invariance for Civil Construction**: Any site with gradient $\theta > 35^\circ$ must strictly emit a `REJECTED` safety verdict regardless of how favorable the recharge score is.
  * **Monotonicity with Soil Permeability**: Ceteris paribus, a site with coarse sand substrate must yield a higher recharge score than a site with dense clay substrate.
  * **Thermal Inversion Check**: High land surface temperature combined with negative NDVI must produce a high or critical heat-water stress score.
  * **Riparian Buffer Invariance**: Earthen bund recommendations must be rejected for sites located within 200 m horizontal distance and 5 m vertical elevation of active river channels.

### 2.3. Tier 3: Sensitivity and Perturbation Analysis
* **Scope**: Validating stability under continuous input variations via the scenario simulator.
* **Test Protocols**:
  * **Rainfall Perturbation Monotonicity**: Increasing the rainfall fraction from $0.5$ to $1.5$ must monotonically increase the recharge score and monotonically decrease the heat-water stress and spring-drying scores.
  * **Civil Intervention Uplift Boundary**: Applying an approved intervention (e.g., check dam) must produce a positive recharge delta without exceeding the global ceiling of 100.0.
  * **Weight Sum Normalization**: The sum of weights across all factors within any score definition in `config/weights.yaml` must equal exactly $1.00 \pm 10^{-6}$.

### 2.4. Tier 4: External Empirical Benchmarking
* **Scope**: Comparative evaluation against published government hydrogeological and climatic datasets ingested into the repository.
* **Benchmark Sources**:
  * **CGWB Groundwater Telemetry (`data/groundwater_level_cleaned_odisha_jharkhand_mp_2021_2025.csv`)**: 34,141 empirical well observations across Odisha, Jharkhand, and Madhya Pradesh validate pre-monsoon static water level surfaces and post-monsoon recharge yield models.
  * **IMD Gridded Temperature Climatology (`data/imd_max_temperature_odisha_jharkhand_mp_2021_2024.csv`)**: 109,575 station and gridded temperature records calibrate thermal anomaly severity thresholds across central and eastern India.
  * **IMD Daily Rainfall Network (`data/rainfall_cleaned_odisha_jharkhand_mp.csv`)**: 5,512 daily observation points calibrate baseline precipitation normals and scenario stress bounds.
  * **Curated 13-Settlement Portfolio (`config/demo_sites.yaml`)**: Exhaustively exercises all decision branches across Odisha (5), Madhya Pradesh (4), and Jharkhand (4), including geotechnical safety vetoes (`SLOPE_STEEP`, `LANDSLIDE_ZONE`) and civil structure suitability compositions.

---

## 3. Test Execution and Continuous Integration

All 44 automated tests across Tier 1, Tier 2, Tier 3, and Tier 4 are executed automatically upon every code commit and pull request via the GitHub Actions CI pipeline (`.github/workflows/ci.yml`):
* `tests/test_models.py`: Pydantic v2 data contract integrity and serialization bounds.
* `tests/test_scoring.py`: Deterministic spatial scoring, safety veto invariants, and climate simulation.
* `tests/test_agents.py`: Domain specialist agents, Bedrock LLM synthesis, and administrative orchestrator.
* `tests/test_api.py`: FastAPI REST endpoint operations, multi-state filtering, and HTML dossier generation.

Pull requests failing any test or linter constraint (`ruff check`, `ruff format`) are strictly blocked from merging.
