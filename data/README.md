# Data Manifest

> **No raw data is committed to this repo.** This document records every dataset used, its source, licence, and how to reproduce it.

---

## Dataset Records

### DEM — SRTM 30m
- **Source**: NASA Shuttle Radar Topography Mission via [USGS EarthExplorer](https://earthexplorer.usgs.gov/) or Google Earth Engine
- **Version**: SRTM v3 (2014)
- **Resolution**: 30m (1 arc-second)
- **Licence**: Public domain (US Government)
- **Download method**: GEE `USGS/SRTMGL1_003` or USGS EarthExplorer
- **Preprocessing**: Clip to AOI, fill voids, reproject to EPSG:32645 (UTM 45N)
- **Features**: Elevation → slope, aspect, TWI, drainage density, flow accumulation
- **Limitations**: Canopy-top surface in forested areas; ~16m vertical accuracy

### Rainfall — CHIRPS
- **Source**: [Climate Hazards Group](https://www.chc.ucsb.edu/data/chirps)
- **Version**: CHIRPS v2.0 (daily, 1981–present)
- **Resolution**: 0.05° (~5km)
- **Licence**: Public domain
- **Download method**: GEE `UCSB-CHG/CHIRPS/DAILY` or direct FTP
- **Preprocessing**: Monthly and annual aggregation, clip to AOI, compute 30-year normals and trends
- **Features**: Monsoon rainfall total, intensity, deficit, Mann-Kendall trend
- **Limitations**: Satellite-gauge blend; sparse gauge network in tribal areas

### Land Use Land Cover — ESRI 10m
- **Source**: [ESRI 2023 Land Cover](https://livingatlas.arcgis.com/landcover/)
- **Version**: 2023
- **Resolution**: 10m
- **Licence**: CC-BY-4.0
- **Download method**: Direct download or GEE
- **Preprocessing**: Clip to AOI, reclassify to perviousness classes
- **Features**: LULC class, pervious fraction, forest cover
- **Limitations**: Global model; local accuracy ~75-85%

### Soil — SoilGrids 250m
- **Source**: [ISRIC SoilGrids](https://soilgrids.org/)
- **Version**: SoilGrids 2.0 (2021)
- **Resolution**: 250m
- **Licence**: CC-BY-4.0
- **Download method**: WCS API or GEE
- **Preprocessing**: Extract texture class, compute permeability proxy
- **Features**: Sand/silt/clay fractions → texture class → permeability class
- **Limitations**: Modelled at 250m; no local calibration for Indian soils

### Land Surface Temperature — MODIS
- **Source**: NASA MODIS via GEE `MODIS/061/MOD11A2`
- **Version**: Collection 6.1
- **Resolution**: 1km
- **Licence**: Public domain
- **Download method**: GEE export
- **Preprocessing**: Summer (Mar-Jun) maximum composite, clip to AOI
- **Features**: Peak LST for heat stress scoring
- **Limitations**: Cloud contamination; 1km resolution misses urban heat islands

### NDVI — MODIS
- **Source**: NASA MODIS via GEE `MODIS/061/MOD13A2`
- **Version**: Collection 6.1
- **Resolution**: 1km (16-day composite)
- **Licence**: Public domain
- **Download method**: GEE export
- **Preprocessing**: Summer minimum composite
- **Features**: Vegetation greenness as heat-stress modifier
- **Limitations**: 1km resolution; cloud-affected periods

### Forest Change — Hansen
- **Source**: [Hansen Global Forest Change](https://glad.earthengine.app/view/global-forest-change)
- **Version**: v1.11 (2023)
- **Resolution**: 30m
- **Licence**: CC-BY-4.0
- **Download method**: GEE `UMD/hansen/global_forest_change_2023_v1_11`
- **Preprocessing**: Compute forest loss in spring catchments (2010-2023)
- **Features**: Forest loss year, tree cover 2000
- **Limitations**: Only detects stand-replacement disturbances

### Groundwater — CGWB (Illustrative)
- **Source**: Central Ground Water Board observation wells
- **Version**: Pre-monsoon 2023 (if available)
- **Resolution**: Point data (interpolated)
- **Licence**: Government of India open data
- **Download method**: data.gov.in or CGWB reports
- **Preprocessing**: IDW interpolation to raster
- **Features**: Pre-monsoon groundwater depth
- **Limitations**: Sparse well network; significant interpolation uncertainty
- **⚠️ DATA TAG**: `proxy` — using interpolated depth, not direct measurements

### Spring Locations (Illustrative)
- **Source**: Synthetic / demo_sites.yaml
- **Version**: N/A
- **Resolution**: Point locations
- **Licence**: N/A
- **Download method**: Manually created for demo
- **Preprocessing**: None
- **Features**: Spring outlet location, elevation
- **Limitations**: Not real spring locations
- **⚠️ DATA TAG**: `illustrative` — entirely synthetic for demo purposes
