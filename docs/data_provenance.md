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

---

## Settlement-to-Telemetry Empirical Mapping (Phase 4)

Each of the 13 demonstration settlements is mapped to its administrative district, nearest CGWB observation well, and nearest IMD 1.0° temperature grid centroid via geodesic distance calculation. All hydro-climatic inputs derived from these associations are formally tagged with provenance `derived`.

### Mapping Matrix

| Site ID | Settlement Name | District | State | Nearest CGWB Well (Dist) | Nearest IMD Temp Grid (Dist) | Mapped IMD Rain District | Provenance |
|:---|:---|:---|:---|:---|:---|:---|:---:|
| `site_001` | Laxmipur | Koraput | Odisha | Koraput-i (0.9 km) | (18.5°N, 82.5°E) (41.4 km) | KORAPUT | `derived` |
| `site_002` | Mundaguda | Koraput | Odisha | Panchada (7.5 km) | (18.5°N, 82.5°E) (64.4 km) | KORAPUT | `derived` |
| `site_003` | Parajam | Koraput | Odisha | Soguru (5.2 km) | (18.5°N, 82.5°E) (7.6 km) | KORAPUT | `derived` |
| `site_004` | Dukum | Koraput | Odisha | Kusumguda (7.9 km) | (19.5°N, 83.5°E) (72.8 km) | KORAPUT | `derived` |
| `site_005` | Kotpad Town | Koraput | Odisha | Miriguda (5.9 km) | (19.5°N, 82.5°E) (41.5 km) | KORAPUT | `derived` |
| `site_mp_001` | Bichhiya | Mandla | Madhya Pradesh | Bichhia1 (1.3 km) | (22.5°N, 80.5°E) (22.5 km) | MANDLA | `derived` |
| `site_mp_002` | Samnapur | Dindori | Madhya Pradesh | Bijhauri (5.0 km) | (22.5°N, 81.5°E) (44.1 km) | DINDORI | `derived` |
| `site_mp_003` | Meghnagar | Jhabua | Madhya Pradesh | Meghnagar New (1.2 km) | (22.5°N, 74.5°E) (44.1 km) | JHABUA | `derived` |
| `site_mp_004` | Bajag Scarp | Dindori | Madhya Pradesh | Gorakhpur (8.5 km) | (22.5°N, 81.5°E) (19.7 km) | DINDORI | `derived` |
| `site_jh_001` | Torpa | Khunti | Jharkhand | Dorma (7.3 km) | (22.5°N, 85.5°E) (63.3 km) | KHUNTI | `derived` |
| `site_jh_002` | Goilkera | West Singhbhum | Jharkhand | Sonua (20.3 km) | (22.5°N, 85.5°E) (12.5 km) | WEST SINGHBHUM | `derived` |
| `site_jh_003` | Chaibasa Plain | West Singhbhum | Jharkhand | Chaibasa (0.7 km) | (22.5°N, 85.5°E) (31.5 km) | WEST SINGHBHUM | `derived` |
| `site_jh_004` | Porahat Scarp | West Singhbhum | Jharkhand | Sonua (15.6 km) | (22.5°N, 85.5°E) (31.2 km) | WEST SINGHBHUM | `derived` |

### Methodological Assumptions

1. **Hydrogeological Proximity**: In fractured hard-rock crystalline and basaltic terrains, static water level measurements exhibit spatial correlation within an unconfined sub-watershed radius of 15–25 km. Where a direct village-level well exists (e.g. `Chaibasa`, `Koraput-i`, `Bichhia1`, `Meghnagar New`), station-level pre/post-monsoon levels are used directly; otherwise, the normalized district-level mean groundwater depth is applied.
2. **Thermal Grid Interpolation**: Surface air temperature gradients across plateau terrain follow synoptic airmass patterns. Settlement coordinates are associated with the nearest 1.0° regular grid centroid from the IMD dataset (spatial distance $<75\text{ km}$).
3. **Precipitation Homogeneity**: Daily precipitation departures and monsoon cumulative totals are sourced from district-level rain gauge networks reporting via IMD daily bulletins.
4. **Sign Convention Invariance**: Seasonal water table fluctuation is computed as $\text{Rise} = \text{Pre-monsoon Depth} - \text{Post-monsoon Depth}$. Because readings measure depth below ground surface (m bgl), a deeper water level in post-monsoon yields a negative value, denoting aquifer depletion.