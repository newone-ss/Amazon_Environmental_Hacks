# UI Gap Analysis vs Backend API Contract

| UI Element | Backend Support | Action |
| :--- | :--- | :--- |
| **Brand Lockup** (Logo & Title) | Yes | Keep. |
| **Settlement Search** | Yes | Keep; bind directly to `/villages` by name, block, district. |
| **State / Region Selector** (Uttarakhand, etc.) | Partial | Rename; replace with `All states`, `Odisha`, `Madhya Pradesh`, `Jharkhand`. |
| **Notification Bell** | No | Remove; backend has no asynchronous user notification system. |
| **User Profile Avatar** | No | Remove; backend does not support user accounts or profile storage. |
| **Sidebar: Map** | Yes | Keep. |
| **Sidebar: Interventions** | Yes | Keep; bind to settlement recommendations. |
| **Sidebar: Field Data** | Yes | Keep; bind to `/observations`. |
| **Sidebar: Reports** | Yes | Keep; bind to `/report` and `/dpr/generate`. |
| **Sidebar: Help** | Yes | Keep; static decision guidance for planners. |
| **Sidebar: Settings** | No | Remove; no user settings stored on backend. |
| **Map Layer: Recharge Potential** | Yes | Keep; drives `recharge_score` filtering. |
| **Map Layer: Heat Vulnerability** | Yes | Keep; drives `heat_water_stress` filtering. |
| **Map Layer: Water Stress / Springs** | Yes | Keep; reflects `spring_drying_index` and `has_spring`. |
| **Map Layer: Geology** | No | Remove; backend has no spatial geology layer. |
| **Map Layer: Land Use / Land Cover** | No | Remove; backend has no LULC raster/vector layer. |
| **Map Layer: Landslide Risk** | No | Remove; backend provides site safety rule checks (`SLOPE_STEEP`, `LANDSLIDE_ZONE`) rather than spatial landslide map layer. |
| **Safety Verdict Badge & Rationale** | Yes | Add immediately to top of Settlement Panel (SAFE / CONDITIONAL / REJECTED) with rule IDs and clear human reasons. |
| **Score: Recharge Potential** | Yes | Keep; bind to `recharge_score` (`value`, `score_class`, `drivers`, `confidence`). |
| **Score: Heat Vulnerability** | Yes | Keep; bind to `heat_water_stress` (`value`, `score_class`, `drivers`, `confidence`). |
| **Score: Spring Desiccation Risk** | Yes | Rename from Water Stress to Spring Desiccation Risk (`spring_drying_index`). |
| **Score: Vegetation Health** | No | Remove; not computed by scoring engine. |
| **Confidence Indicator** | Yes | Add 3-segment bar (Low / Medium / High) with numeric value tooltip. |
| **Provenance Tags** | Yes | Add provenance tags (`real`, `proxy`, `illustrative`). |
| **Intervention Card** | Yes | Keep; bind to `Recommendation` (MGNREGA cost range, labor days, dimensions, materials, assumptions). |
| **Trends Tab (Fictional Spring SVG)** | No | Remove static Himalayan discharge curve. Replace with Rainfall Scenario Simulator (`/scenario`). |
| **Notifications Modal** | No | Remove. |
| **Profile Modal** | No | Remove. |
| **DPR / Site Work Plan Modal** | Yes | Keep; bind to real structure specs and `/dpr/generate` ZIP download. |
| **Settlement Locations** (Sarmoli, Joshimath, etc.) | No | Replace with 13 curated settlements in Odisha, MP, and Jharkhand. |
