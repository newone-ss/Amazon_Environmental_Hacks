# Data Provenance Audit for Demo Sites

Each field in the demo sites is classified as:
- **derived**: data obtained from CGWB or IMD datasets
- **curated**: hand-entered values based on knowledge of the site (not from CGWB or IMD)
- **assumed**: values inferred from typical values, rules, or other datasets not CGWB or IMD

## Field Provenance Classification

| Field | Provenance | Justification |
|-------|------------|---------------|
| block | curated | Hand-entered based on site location |
| catchment_area_ha | assumed | Derived from DEM flow accumulation; assumed for demo sites |
| data_tag | curated | Hand-entered as "illustrative" for demo sites |
| distance_to_perennial_water_m | assumed | Estimated from site to nearest perennial water |
| district | curated | Hand-entered based on site location |
| drainage_density | assumed | Derived from stream network; assumed for demo sites |
| elevation_above_river_m | assumed | Calculated from site elevation and river elevation; assumed |
| elevation_m | curated | Hand-entered from known site elevation (e.g., from SRTM or GPS) |
| forest_loss_pct | assumed | From Hansen Global Forest Change dataset; assumed for demo |
| geology | curated | Hand-entered from known site geology (GSI maps) |
| groundwater_depth_m | derived | From Central Ground Water Board (CGWB) monitoring wells |
| has_spring | curated | Hand-entered based on site knowledge |
| landslide_susceptibility | assumed | From GSI landslide susceptibility zonation; assumed |
| lat | curated | Hand-entered from known site coordinates |
| lineament_density | assumed | From ISRO Bhuvan lineament dataset; assumed |
| lon | curated | Hand-entered from known site coordinates |
| lst_summer_max_c | derived | From India Meteorological Department (IMD) temperature data |
| lulc_class | curated | Hand-entered from known site land use/land cover (ISRO Bhuvan) |
| lulc_perviousness | assumed | Derived from lulc class via lookup table |
| name | curated | Hand-entered site name |
| ndvi_summer | assumed | From NASA/USGS MODIS NDVI dataset; assumed |
| notes | curated | Hand-entered descriptive notes |
| population | curated | Hand-entered based on site knowledge or census data |
| population_density_per_km2 | assumed | Calculated from population and area; assumed |
| protected_area_type | curated | Hand-entered from knowledge of protected area status |
| rainfall_deficit_pct | derived | From India Meteorological Department (IMD) rainfall data |
| rainfall_intensity | derived | From India Meteorological Department (IMD) rainfall data |
| rainfall_trend_pct | derived | From India Meteorological Department (IMD) rainfall data |
| seismic_zone | assumed | From seismic zonation maps; assumed |
| settlement | curated | Hand-entered based on whether site is a settlement |
| stream_bed_material | assumed | Inferred from local geology; assumed |
| slope_degrees | assumed | From SRTM 30m DEM; assumed for demo sites |
| soil_permeability | assumed | Derived from soil type via lookup table (ISRIC SoilGrids) |
| soil_type | curated | Hand-entered from known site soil type (ISRIC SoilGrids or field knowledge) |
| state | curated | Hand-entered based on site location |
| stream_order | assumed | Derived from DEM flow accumulation; assumed |

## Application to Confidence and Data Quality Note

The provenance tags are used to adjust the confidence level and data quality note in the scoring engine:
- Each field's provenance contributes to an overall confidence score.
- Curated and assumed inputs lower the confidence numeric value.
- The data quality note includes a summary of field provenances to inform users of data limitations.

For example, a score with many curated or assumed fields will have lower confidence and a note indicating reliance on hand-entered or inferred data.