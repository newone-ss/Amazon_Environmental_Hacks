# Validation Methodology

> How we verify that Bhujal's scores are meaningful.

---

## Approach

### 1. Sanity Checks
- Scores for known "easy" sites (flat, permeable, near river) should be high for recharge.
- Scores for known "hard" sites (steep, rocky, far from water) should be low.
- Safety veto should reject sites on >35° slopes or in landslide zones.

### 2. Sensitivity Analysis
- Vary each input factor ±20% and check that the score moves in the expected direction.
- The scenario simulator provides a built-in sensitivity tool.

### 3. Cross-Validation with Literature
- Compare recharge suitability zones with published CGWB aquifer maps.
- Compare heat stress patterns with IMD heat-wave frequency data.

### 4. Field Validation (Future)
- The observation form enables collection of ground-truth data.
- Compare predicted recharge zones with actual well yield data.
- Compare spring drying index with measured spring discharge time series.

## Current Status
- **Phase 0**: Models and contract defined. No scores computed yet.
- **Phase 1**: Sanity checks will be added as unit tests.
