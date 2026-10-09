# Technical Roadmap and Post-MVP Engineering Horizon

> **Document Status**: Strategic Architecture Baseline  
> **Governance Role**: Formal boundary for post-MVP enhancements in compliance with Rule 6 (Scope Enforcement).

---

## 1. Scope Management Philosophy

To achieve production-grade stability, sub-second query latency, and zero runtime failures during evaluation, the Bhujal MVP is strictly constrained to a single demonstration Area of Interest (Koraput District) with deterministic scoring and serverless ingestion. 

This document defines the structured evolution of the platform beyond the 48-hour submission window across three planned development horizons.

---

## 2. Strategic Development Horizons

```
+---------------------------------------------------------------------------------------+
| HORIZON 1: NEAR-TERM (Months 1–3)                                                      |
| High-Fidelity Boundaries, Cloud-Optimized Geotiff (COG) Streaming, and Localization   |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| HORIZON 2: MEDIUM-TERM (Months 4–6)                                                    |
| In-Situ Sensor Telemetry, Calibrated Machine Learning, and Multi-District AOI          |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| HORIZON 3: INSTITUTIONAL MATURITY (Months 7–12)                                        |
| National Portal Integration (Jal Jeevan Mission / PMKSY), Edge Mobile Sync, & Offline |
+---------------------------------------------------------------------------------------+
```

---

## 3. Subsystem Roadmap

### 3.1. Geospatial Data Ingestion and Processing Pipeline
* **High-Precision Administrative Boundaries**: Replace the rectangular bounding envelope with the official Survey of India vectorized district polygon, complete with sub-district (tehsil) and block shapefile boundaries.
* **Cloud-Optimized GeoTIFF (COG) Streaming**: Transition raster assets to S3-hosted COGs queried via HTTP range requests, eliminating local raster downsampling.
* **Automated Earth Engine Sync**: Establish scheduled AWS EventBridge triggers executing serverless Google Earth Engine batch exports of daily precipitation and 8-day MODIS thermal layers.
* **SAR Soil Moisture Telemetry**: Ingest European Space Agency Sentinel-1 C-band synthetic aperture radar (SAR) interferometry to derive high-resolution (10m) volumetric root-zone soil moisture.

### 3.2. Hydrogeological and Analytical Modeling
* **Machine Learning Recharge Calibration**: Train an XGBoost / Random Forest surrogate model on historical Central Ground Water Board observation well hydrographs to refine empirical factor weightings.
* **Full Hydrological Water Balance Modeling**: Transition from first-order linear rainfall sensitivity to a continuous semi-distributed hydrological model (e.g., modified Thornthwaite-Mather or SWAT-Lite).
* **Spring Catchment 3D Ray-Tracing**: Integrate flow-direction algorithms capable of modeling subterranean structural dip and strike in folded Eastern Ghats lithologies.
* **Dynamic Uncertainty Intervals**: Compute formal Bayesian credible intervals for all composite scores rather than discrete three-tier confidence classifications.

### 3.3. Enterprise Backend and Security
* **Authentication and Access Governance**: Integrate Amazon Cognito user pools with Role-Based Access Control (RBAC), establishing distinct permission tiers for District Collectors, Block Development Officers, Field Enumerators, and Public Citizens.
* **Offline-First Field Sync**: Implement AWS AppSync (GraphQL) with local SQLite device cache for offline field telemetry synchronization in remote tribal pockets lacking cellular connectivity.
* **Asynchronous Batch Reporting Engine**: Build an Amazon SQS and AWS Step Functions workflow to execute multi-site district-wide batch assessments and export bundled geospatial archives (Shapefile / GeoPackage / GeoTIFF).

### 3.4. User Interface and Spatial Analytics
* **3D Digital Terrain Modeling**: Incorporate MapLibre GL 3D terrain rendering with client-side hillshading and vertical exaggeration to visualize ridge-to-valley springheads.
* **Multi-Language Regionalization**: Implement complete internationalization (i18n) supporting Odia, Hindi, and English.
* **Side-by-Side Scenario Workbench**: Enable dual-map split-pane comparisons allowing planners to visualize baseline versus drought or post-intervention landscapes simultaneously.
* **Government Scheme Integration**: Map identified intervention sites directly to national fund allocation codes (e.g., MGNREGA Master Circular, Pradhan Mantri Krishi Sinchayee Yojana, and Jal Shakti Abhiyan).
