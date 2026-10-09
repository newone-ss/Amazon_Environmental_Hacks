# Engineering and Scientific Assumptions Register

> **Document Status**: Active Technical Baseline  
> **Governance Role**: Formal register of engineering approximations, hydrological proxies, and econometric assumptions embedded in the platform configuration matrices.

---

## 1. Governance and Calibration Framework

In accordance with empirical transparency standards, all subjective or uncalibrated constants in the platform are tagged within configuration files using `# ASSUMPTION:` comments. This register consolidates and analyzes each assumption, establishing the technical rationale, potential error envelope, and long-term empirical validation pathway.

---

## 2. Comprehensive Assumptions Inventory

### 2.1. Multi-Criteria Hydrogeological Scoring

| Identifier | Domain Parameter | Assigned Value / Rule | Baseline Rationale | Empirical Limitation | Planned Field Validation |
|---|---|---|---|---|---|
| **ASM-HYD-01** | Recharge Factor Weight: Slope | Weight = 0.25 | Steep slopes accelerate runoff and limit infiltration opportunity time. | Ignores micro-terracing and localized depression storage. | Field infiltration ring tests across slope classes (2° to 30°). |
| **ASM-HYD-02** | Soil Permeability Proxy | Weight = 0.20 | Textural class from SoilGrids 250m indicates coarse vs. fine drainage. | Model does not account for subterranean hardpans or compaction. | Double-ring infiltrometer surveys in Koraput block catchments. |
| **ASM-HYD-03** | Fracture Flow from Lineaments | Weight = 0.10 | Surface lineament density proxies subsurface fracture permeability. | Not all surface lineaments are open, transmissive fracture zones. | Pumping tests and 2D electrical resistivity tomography (ERT). |
| **ASM-HYD-04** | Drainage Density Inversion | Weight = 0.10 | Low drainage density correlates with higher relative infiltration. | May be confounded by lithological resistance rather than permeability. | Hydrograph separation analysis on seasonal stream gauges. |
| **ASM-HYD-05** | Quartile Classification Thresholds | [0–25, 25–50, 50–75, 75–100] | Linear quartile partition across normalized score spectrum. | Uniform intervals may not reflect non-linear recharge response. | Receiver Operating Characteristic (ROC) curve calibration against well yields. |

### 2.2. Geotechnical and Safety Veto Bounds

| Identifier | Safety Parameter | Assigned Value / Rule | Baseline Rationale | Empirical Limitation | Governing Standard |
|---|---|---|---|---|---|
| **ASM-SAF-01** | Slope Stability Cutoff | $\theta > 35^\circ \implies \text{REJECTED}$ | General civil boundary for safe unreinforced earthen excavation. | Localized rock anchors or stable bedrock could permit construction. | Bureau of Indian Standards (BIS) Hill Construction Code. |
| **ASM-SAF-02** | Moderate Slope Advisory | $20^\circ < \theta \le 35^\circ \implies \text{CONDITIONAL}$ | Requires retaining walls, berm terracing, and drainage channels. | Increases civil cost by 30% to 60%. | CGWB Artificial Recharge Manual. |
| **ASM-SAF-03** | Riparian Inundation Buffer | Distance $< 200\text{ m}$ AND Elevation $< 5\text{ m}$ | Protects civil structures from high-stage monsoon scour. | Topographic DEM may smooth subtle natural levees and channel incising. | Central Water Commission (CWC) flood recurrence mapping. |
| **ASM-SAF-04** | Expansive Clay Interception | Soil type in `['expansive_clay', 'peat']` | Montmorillonite clays swell and destabilize earthen bund foundations. | Soil map resolution (250m) may miss micro-scale sandy lenses. | IS 2720 Soil Geotechnical Testing Standards. |

### 2.3. Civil Econometrics and Costing Schedules

| Identifier | Cost Parameter | Assigned Value / Range | Baseline Rationale | Empirical Limitation | Governing Baseline |
|---|---|---|---|---|---|
| **ASM-CST-01** | Unskilled Labour Wage | INR 350 / person-day | Calibrated to 2024–2025 Odisha notified MGNREGA wage rates. | Market rates for skilled masons are significantly higher (INR 600–800). | Odisha MGNREGA Schedule of Rates (SoR). |
| **ASM-CST-02** | Civil Cost Variance | Range low = base, high = $+200\%$ to $+300\%$ | Remote tribal terrain incurs substantial haulage premiums. | Does not model road accessibility or distance to stone quarries. | District Schedule of Rates (Koraput DSR). |
| **ASM-CST-03** | Engineering Contingency | 10% Contingency + 5% Supervision | Standard government administrative and engineering overhead. | Geological surprises during excavation may exceed 10%. | Central Public Works Department (CPWD) Manual. |

### 2.4. Climate Sensitivity and Scenario Perturbation

| Identifier | Simulation Parameter | Value / Formula | Baseline Rationale | Empirical Limitation | Scientific Reference |
|---|---|---|---|---|---|
| **ASM-SCN-01** | Recharge Rainfall Sensitivity | $\Delta S_{recharge} = 40 \times (F - 1.0)$ | First-order linear sensitivity to seasonal precipitation anomalies. | True hydrological recharge exhibits non-linear saturation thresholds. | Thornthwaite-Mather water balance approximations. |
| **ASM-SCN-02** | Thermal Stress Sensitivity | $\Delta S_{stress} = -30 \times (F - 1.0)$ | Higher rainfall mitigates soil moisture deficits and surface heat. | Ignores humidity-driven wet-bulb temperature escalation. | Compound climate extreme indices. |
| **ASM-SCN-03** | Independent Civil Uplift | Additive points (e.g., $+12$ for check dam) | Reflects incremental infiltration enhancement from new storage. | Multiple proximate structures exhibit diminishing marginal returns. | Watershed impact evaluations (IWMP/PMKSY). |
