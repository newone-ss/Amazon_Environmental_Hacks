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
| **CGWB-GWL-PTS** | Pre-Monsoon Water Table Depth | Point Interpolated | 2023 Pre-Monsoon | Central Ground Water Board | Proxy | Open Data (GoI) |
| **BHUJAL-SPRINGS** | Springhead Locations & Outflow | Point Geometries | Demonstration Baseline | Curated Demo Baseline | Illustrative | CC0-1.0 |

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

### 2.7. Groundwater Levels: CGWB Monitoring Wells
* **Provider**: Central Ground Water Board (Government of India) National Water Informatics Centre.
* **Data Status**: `proxy`
* **Methodology**: Spatial inverse distance weighted (IDW) interpolation across regional observation wells to generate continuous pre-monsoon depth-to-water surfaces.
* **Limitations and Calibration Notes**: Monitoring wells are predominantly sited in alluvial valley corridors and urban blocks, resulting in higher interpolation uncertainty in elevated crystalline tribal plateaus.

### 2.8. Demo Village and Spring Inventory
* **Source**: `config/demo_sites.yaml`
* **Data Status**: `illustrative`
* **Methodology**: Synthetically attributed profiles based on typical micro-watershed characteristics of Koraput District to exercise and validate all decision branches of the scoring engine, safety veto system, and civil intervention composer.

---

## 3. Data Governance and Provenance Classification

All API responses and user interface indicators enforce strict taxonomic classification:

* **Empirical (`real`)**: Primary data acquired from peer-reviewed, satellite, or institutional telemetry with documented sensor calibration.
* **Proxy (`proxy`)**: Geostatistically interpolated, downscaled, or indirect physical variables where direct telemetry is geographically sparse.
* **Illustrative (`illustrative`)**: Synthesized representative records engineered to stress-test platform algorithms and demonstrate edge-case behaviors (e.g., active hazard rejections).
