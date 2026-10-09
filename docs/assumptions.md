# Assumptions

> All assumptions are tagged in config files with `# ASSUMPTION:` comments.
> This document consolidates them for review.

---

## Scoring Weights
- All weights are initial estimates. They should be calibrated against field data or expert review.
- Classification thresholds (excellent/good/moderate/poor) are arbitrary quartile-style breaks.

## Safety Rules
- Slope threshold of 35° for REJECT is based on general BIS guidance, not site-specific geotechnical analysis.
- Flood buffer of 200m horizontal / 5m vertical is a conservative default.
- Landslide susceptibility zones are from GSI national-scale maps (1:50,000); local conditions may differ.

## Costs
- All costs are based on MGNREGA schedule of rates and state SOR, adjusted for Odisha 2024.
- Actual costs will vary by ±30-50% depending on site access, material availability, and terrain.

## Data
- Soil permeability is derived from texture class (proxy), not measured hydraulic conductivity.
- Spring locations are illustrative; real spring inventory would come from CGWB or state groundwater department.
- Lineament density is a proxy for fracture permeability; actual permeability requires hydrogeological survey.

## Scenario Simulator
- Linear sensitivity coefficients are crude first-order approximations.
- Intervention uplifts are assumed additive and independent — real interactions are non-linear.
