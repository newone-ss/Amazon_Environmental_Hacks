# Data Provenance and Geospatial Manifest

> **Policy Directive**: In compliance with empirical honesty protocols, raw binary raster data is excluded from version control. This document serves as the formal register of data assets, specifying acquisition channels, licensing, pre-processing workflows, spatial resolutions, and analytical limitations.

---

## 1. Summary of Spatial and Hydro-Climatic Datasets

| Dataset Identifier | Domain | Spatial Resolution | Temporal Coverage | Custodian / Source | Provenance Status | License |
|---|---|---|---|---|---|---|
| **SRTM-DEM-30** | Topography & Hydro-morphology | 30 m (1 arc-sec) | Feb 2000 (Static v3) | NASA / USGS | Empirical | Public Domain |
| **CHIRPS-PRECIP** | Precipitation Climatology | 0.05° (~5.5 km) | 1981–Present (Daily) | UCSB Climate Hazards Center | Empirical | Public Domain |
| **ESRI-LULC-10** | Land Cover & Surface Permeability | 10 m | 2023 Composite | ESRI / Impact Observatory | Empirical | CC-BY-4.0 |
| **SOILGRIDS-250** | Pedology & Soil Texture | 250 m | 2021 Release (v2.0) | ISRIC World Soil Info | Empirical | CC-BY-4.0 |
| **MODIS-LST-1K** | Radiometric Surface Temperature | 1,000 m | 2020–2024 (Mar–Jun) | NASA LP DAAC (MOD11A2) | Empirical | Public Domain |
| **MODIS-NDVI-1K** | Normalized Difference Vegetation | 1,000 m | 2020–2024 (Summer) | NASA LP DAAC (MOD13A2) | Empirical | Public Domain |
| **HANSEN-GFC-30** | Forest Canopy Disturbance | 30 m | 2010–2023 Loss | Hansen / UMD / Google | Empirical | CC-BY-4.0 |
| **CGWB-GWL-CLEANED** | Monitored Groundwater Level (34,141 pts) | Station Coordinates | 2021–2025 | Central Ground Water Board (CGWB) | Empirical | Open Data (GoI) |
| **IMD-TEMP-CLEANED** | Daily Maximum Temperature (109,575 pts) | Gridded Coordinates | 2021–2024 | India Meteorological Dept (IMD) | Empirical | Open Data (GoI) |
| **IMD-RAIN-CLEANED** | Daily Rainfall & Departure (5,512 pts) | District Aggregates | 2021–2026 | India Meteorological Dept (IMD) | Empirical | Open Data (GoI) |
| **BHUJAL-SITES-13** | Curated Settlement Benchmarks (13 sites) | Point Geometries | Demonstrator Baseline | Curated Multi-State Baseline | Illustrative | CC0-1.0 |

---

## 2. Dataset Technical Specifications

### 2.1. Digital Elevation Model (DEM): SRTM 30m
* **Provider**: NASA Shuttle Radar Topography Mission (SRTMGL1 v003) via USGS EarthExplorer / Google Earth Engine (`USGS/SRTMGL1_003`).
* **Coordinate System**: WGS 84 (EPSG:4326); reprojected to UTM Zone 45N (EPSG:32645) for planar metric analysis.
* **Derived Hydrological Features**:
  * Slope gradient in degrees ($\theta$) and percentage.
  * Aspect (solar radiation and moisture exposure orientation).
  * Topographic Wetness Index ($\text{TWI} = \ln(a / \tan \beta)$).
  * D8 / D-Infinity flow accumulation surfaces and drainage network density ($D_d = \sum L / A$).
* **Limitations and Calibration Notes**: Represents a digital surface model (DSM) rather than a bare-earth digital terrain model (DTM); canopy-top height may introduce vertical variance of $\pm 16\text{ m}$ in heavily forested ridge complexes of the Eastern Ghats.

### 2.2. Precipitation Climatology: CHIRPS v2.0
* **Provider**: Climate Hazards Center, University of California, Santa Barbara (`UCSB-CHG/CHIRPS/DAILY`).
* **Temporal Scope**: 30-year baseline normals (1991–2020) and recent monsoon aggregations (June–September).
* **Derived Hydrological Features**:
  * Mean cumulative monsoon precipitation ($P_{monsoon}$).
  * High-intensity precipitation recurrence ($I_{monsoon}$).
  * Long-term precipitation departure / deficit ratio ($D_P$).
  * Non-parametric Mann-Kendall trend statistics ($\tau$) for baseflow stability.
* **Limitations and Calibration Notes**: Blends satellite infrared cold cloud duration with sparse surface gauge records; localized orographic convective bursts in high-elevation tribal pockets may exhibit micro-climatic attenuation.

### 2.3. Land Use and Land Cover (LULC): ESRI 10m
* **Provider**: Impact Observatory and ESRI Living Atlas (Sentinel-2 deep learning classification).
* **Spatial Resolution**: 10 meters ground sampling distance.
* **Classification Remapping for Hydrology**:
  * Forest and dense vegetation: Hydraulic permeability factor 0.90–1.00.
  * Grasslands and scrub: Permeability factor 0.70–0.80.
  * Rainfed croplands: Permeability factor 0.60–0.70.
  * Built-up settlements: Permeability factor 0.10–0.25 (impervious surface boundary).
* **Limitations and Calibration Notes**: Global semantic classification model; localized shifting cultivation patches (*podu chasa*) may be seasonally classified as scrub rather than fallow agriculture.

### 2.4. Pedological Soil Properties: ISRIC SoilGrids 2.0
* **Provider**: International Soil Reference and Information Centre (ISRIC), Wageningen.
* **Spatial Resolution**: 250 meters at 6 standard depth intervals (0–200 cm).
* **Derived Hydrological Features**:
  * Sand, silt, and clay percentage fractions (USDA particle-size distribution).
  * Inferred hydraulic conductivity ($K_{sat}$) and infiltration capacity proxy.
* **Limitations and Calibration Notes**: Globally modeled machine-learning product without fine-scale Eastern Ghats lateritic horizon calibration.

### 2.5. Land Surface Temperature (LST): MODIS Aqua/Terra
* **Provider**: NASA Land Processes Distributed Active Archive Center (MOD11A2 Collection 6.1).
* **Derived Metric**: Maximum 8-day composite surface radiometric temperature during pre-monsoon heat window (March 1 to June 15).
* **Application**: Primary thermal indicator for heat vulnerability scoring.
* **Limitations and Calibration Notes**: Moderate 1,000-meter resolution averages thermal extremes across narrow valley bottoms; filtered for high cloud contamination.

### 2.6. Forest Canopy Disturbance: Hansen Global Forest Change
* **Provider**: Department of Geographical Sciences, University of Maryland (v1.11).
* **Temporal Window**: Cumulative tree canopy loss (2010–2023).
* **Application**: Catchment degradation coefficient in springhead desiccation risk estimation.
* **Limitations and Calibration Notes**: Quantifies stand-replacement disturbance; understory degradation without canopy opening is not captured.

### 2.7. Monitored Groundwater Levels: CGWB Observation Network
* **File Path**: `data/groundwater_level_cleaned_odisha_jharkhand_mp_2021_2025.csv`
* **Provider**: Central Ground Water Board (CGWB), Government of India (National Water Informatics Centre).
* **Record Count**: 34,141 validated hydrograph readings (January 2021 to December 2025).
* **Geographic Scope**: Extensive telemetry network covering Odisha, Jharkhand, and Madhya Pradesh.
* **Schema**: `station`, `agency`, `state_lgd_code`, `state`, `district_lgd_code`, `district`, `tehsil`, `block`, `village`, `river`, `basin`, `tributary`, `latitude`, `longitude`, `elevation_msl_m`, `measurement_datetime`, `groundwater_level_m`.
* **Application**: Serves as the empirical ground-truth benchmark for static water level (SWL) surfaces, validating simulated post-monsoon drawdowns and identifying chronic over-extraction blocks.
* **Data Status**: `real`

### 2.8. Surface Thermal Observations: IMD Maximum Temperature Climatology
* **File Path**: `data/imd_max_temperature_odisha_jharkhand_mp_2021_2024.csv`
* **Provider**: India Meteorological Department (IMD), Ministry of Earth Sciences.
* **Record Count**: 109,575 daily maximum temperature records (January 2021 to December 2024).
* **Geographic Scope**: Gridded points and synoptic stations across Odisha, Jharkhand, and Madhya Pradesh.
* **Schema**: `date`, `latitude`, `longitude`, `maximum_temperature_c`.
* **Application**: Calibrates summer thermal anomaly thresholds, validating satellite-derived MODIS LST radiometric anomalies against ground-station air maximums.
* **Data Status**: `real`

### 2.9. Daily Rainfall and Precipitation Departures: IMD Station Network
* **File Path**: `data/rainfall_cleaned_odisha_jharkhand_mp.csv`
* **Provider**: India Meteorological Department (IMD).
* **Record Count**: 5,512 daily observation entries across monitoring seasons (2021–2026).
* **Geographic Scope**: District aggregations across Odisha, Jharkhand, and Madhya Pradesh.
* **Schema**: `state`, `district`, `date`, `daily_rainfall_mm`, `daily_normal_mm`, `daily_departure_percent`, `daily_rainfall_category`.
* **Application**: Informs the baseline precipitation normal inputs in `config/scenario.yaml` and grounds drought sensitivity stress tests (-50% to +50% perturbations).
* **Data Status**: `real`

### 2.10. Curated Demonstration Settlements and Spring Inventory
* **Source**: `config/demo_sites.yaml`
* **Count**: 13 curated settlements across priority agro-ecological zones:
  * **Odisha (5)**: Laxmipur, Mundaguda, Parajam, Dukum, Kotpad Town (Koraput District).
  * **Madhya Pradesh (4)**: Bichhiya (Mandla), Samnapur (Dindori), Meghnagar (Jhabua), Bajag Scarp (Dindori).
  * **Jharkhand (4)**: Torpa (Khunti), Goilkera (West Singhbhum), Chaibasa Plain (West Singhbhum), Porahat Scarp (West Singhbhum).
* **Data Status**: `illustrative`
* **Methodology**: Curated representative profiles reflecting real regional physiography, soil textures, basaltic/granitic lithologies, and hazard zones, explicitly structured to exercise all deterministic scoring paths, geotechnical safety vetoes, and civil intervention matchers.

---

## 3. Data Governance and Provenance Classification

All API responses and user interface indicators enforce strict taxonomic classification:

* **Empirical (`real`)**: Primary data acquired from peer-reviewed, satellite, or institutional telemetry with documented sensor calibration.
* **Proxy (`proxy`)**: Geostatistically interpolated, downscaled, or indirect physical variables where direct telemetry is geographically sparse.
* **Illustrative (`illustrative`)**: Synthesized representative records engineered to stress-test platform algorithms and demonstrate edge-case behaviors (e.g., active hazard rejections).
