# Architectural & Design Decisions Log

## 2026-10-10 - Phase U0: Audit and Data Binding

### Context & Goals
The UI must be driven strictly by the backend API contract (`backend/models.py`, `backend/app.py`, OpenAPI spec). We performed an audit of all existing UI elements against the real contract and mapped out discrepancies and data gaps.

### Decisions Made
1. **Pure React.js (Zero TypeScript)**: Standard Vite + React 18 in `.jsx` / `.js`.
2. **Thin API Client**: `src/api/client.js` with `VITE_API_URL` and a 13-settlement offline mock database in `src/data/mockData.js`.
3. **Removed Unsupported Elements**: Geology, Land Use / Land Cover, Landslide Risk raster layers, Vegetation Health metric, notification bell, profile avatar, and fictional Himalayan spring SVG.
4. **Curated Settlements**: Replaced demo Uttarakhand settlements with 13 curated sites across Odisha, Madhya Pradesh, and Jharkhand. State dropdown has `All states`, `Odisha`, `Madhya Pradesh`, `Jharkhand`.

---

## 2026-10-10 - Phase U1: Rebuild Map to Match Site-Level Data

### Context & Goals
Rebuild the map using MapLibre GL to display site-level point data honestly, replacing the misleading continuous raster heatmap while strictly preserving the existing dark-navy visual design and layout.

### Decisions Made
1. **Basemap**:
   - Integrated Carto Dark Matter GL style (`https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json`), providing a muted dark vector basemap that keeps labels, halos, and markers crisp and legible.
   - MapLibre GL v5 Web Worker configured via Vite's `?url` loader (`maplibregl.setWorkerUrl`), eliminating all worker load failures and bundle delays.

2. **Site-Level Markers & Safety Rings**:
   - Each settlement is rendered as an interactive circle marker with a dark halo label (`text-halo-color: #07111b`, `text-halo-width: 2.5px`).
   - Fill colors dynamically update according to the active layer:
     - **Recharge Potential**: Sequential blues (`#bfdbfe` to `#1d4ed8`).
     - **Heat-Water Vulnerability**: Sequential yellow-orange-red (`#fef08a` to `#dc2626`).
     - **Spring Desiccation Risk**: Sequential amber-red (`#fed7aa` to `#991b1b`).
   - Outer status rings indicate safety:
     - **SAFE**: Green ring (`#22c55e`).
     - **CONDITIONAL**: Amber ring (`#f59e0b`).
     - **REJECTED**: High-contrast red ring (`#ef4444`).

3. **AOI Boundaries**:
   - Embedded `public/aoi.geojson` (derived from `config/aoi.geojson`) to render low-opacity subtle boundaries (`aoi-fill` and `aoi-lines`) for Koraput (Odisha), Mandla/Dindori (MP), and West Singhbhum/Khunti (Jharkhand).

4. **Floating Collapsible Controls & Dynamic Legend**:
   - Collapsible layer panel on top-left allows single-select scores and checkboxes for safety rings and mountain springs.
   - Dynamic legend on bottom-left updates its gradient bar and color ramps based on the active score, with symbol key tags for SAFE, CONDITIONAL, and REJECTED.

5. **State Bounds Fitting & Quick Demo Switcher**:
   - State selector triggers smooth camera animations fitting the map viewport to the selected state's bounding box.
   - Added a "Try demo sites" bar to allow instantaneous testing of SAFE (Laxmipur), CONDITIONAL (Dukum), and REJECTED (Mundaguda) sites.

---

## 2026-10-10 - Phase U2: Settlement Panel with Real Differentiators

### Context & Goals
Implement a comprehensive, modular settlement panel (`SettlementPanel.jsx`) displaying safety, evidence, and actionable plans across four distinct tabs (`Overview`, `Plan`, `Scenario`, `Evidence`).

### Decisions Made
1. **Header**:
   - Replaced illustrative hero photo with a clean, space-efficient header displaying settlement name, district, state, elevation, and priority badge.
   - Added persistent "Demo sites" bar for immediate switching between SAFE, CONDITIONAL, and REJECTED profiles.

2. **Overview Tab Architecture**:
   - **Safety Banner (Full Width)**: Displays status (`SAFE`, `CONDITIONAL`, `REJECTED`), icon, rule IDs, and plain-language justification. For `REJECTED` sites, rendered with hatched red styling stating clearly that no structure is recommended.
   - **Three Score Cards**: Recharge Suitability, Heat-Water Stress, and Spring Desiccation Risk. Unified layout featuring score `/100`, classification chip, confidence indicator (Low/Medium/High + numeric percentage), and provenance tags.
   - **'Why?' Driver Decomposition**: Renders contribution bars for the top 3 drivers per score, expandable to all drivers.
   - **Recommendation Summary**: Shows structure name, category, and MGNREGA cost range with primary CTA (`View Detailed Work Plan`). Strictly hidden when the site is `REJECTED`.
   - **Synthesized Key Insight**: Shows template/AI provenance tag and quotes the exact score numbers in pills alongside the narrative text.

3. **Plan Tab**:
   - Technical justification, physical dimensions grid, and state-calibrated MGNREGA cost table using authentic wage benchmarks (Odisha ₹350/day, MP ₹243/day, Jharkhand ₹255/day).
   - "Generate DPR (ZIP)" button calling `/dpr/generate` with progress feedback.
   - "Open Action Report" with bilingual English/Hindi language options.
   - For `REJECTED` sites, displays an explicit locked state preventing unauthorized sanctions.

4. **Scenario Simulator Tab**:
   - Interactive monsoon rainfall sensitivity slider (`0.50x` to `1.50x` baseline).
   - Checkbox toggle to simulate inclusion of the recommended recharge structure.
   - Interactive Recharts bar chart showing simulated monthly water balance across the calendar year.
   - Summer deficit readout and collapsible modeling assumptions disclaimer.

5. **Evidence Tab**:
   - Real observational telemetry statistics from CGWB monitoring stations (64 stations, 734 readings in Koraput) and IMD gridded summer temperature trends.
   - Data source provenance table documenting agency sources (CGWB, IMD, Landsat, NRSC).
   - Methodological limitations box.

---

## 2026-10-10 - Phase U3: Navigation, Mobile, Language, and Accessibility

### Context & Goals
Implement a clean multi-view navigation system, comprehensive mobile responsiveness down to 390×844 viewport, bilingual English/Hindi localization, field participatory observation reporting, and strict accessibility compliance (Lighthouse/axe score ≥ 90, zero dead controls).

### Decisions Made
1. **Navigation Structure**:
   - Navigation items: **Map**, **Field Data**, **Reports**, **About and Data**, and **Help** (First-Run Decision Guide modal).
   - Removed obsolete Settings, notifications bell, and user profile avatar.
   - **Help** triggers [FirstRunGuideModal.jsx](file:///c:/Users/piyus/OneDrive/Desktop/project/bhujal-frontend/bhujal-frontend/src/components/FirstRunGuideModal.jsx), an interactive 3-step decision workflow walkthrough with Escape key and focus support.
   - Removed the duplicate Interventions item and integrated a **State-wise Recommended Works & Total Cost Table** into the Reports view.

2. **Header & Bilingual Localization**:
   - BrandMark with logo and tagline ("Bhujal", "Heat & Water Resilience").
   - Search with autocomplete suggestions and keyboard/clear button.
   - State filter (`All states`, `Odisha`, `Madhya Pradesh`, `Jharkhand`).
   - Visible **Demo Data Badge** (`demo-data-badge`) with animated pulse indicator.
   - Language toggle button (`EN / हिं`) backed by [src/data/translations.js](file:///c:/Users/piyus/OneDrive/Desktop/project/bhujal-frontend/bhujal-frontend/src/data/translations.js). UI strings and narratives translate seamlessly while numbers, coordinates, and rule IDs (`SLOPE_STEEP`, etc.) remain untranslated.

3. **Field Data Screen ([FieldDataView.jsx](file:///c:/Users/piyus/OneDrive/Desktop/project/bhujal-frontend/bhujal-frontend/src/components/FieldDataView.jsx))**:
   - Structured observation form supporting spring flow, well depth, and structure condition.
   - Optional photo upload integrated with backend presigned URL (`api.getUploadUrl()`), featuring image preview, S3 key confirmation, and clear controls.
   - **Geolocation Map Pinning**: "Pin from GPS" button leverages `navigator.geolocation.getCurrentPosition()` with graceful fallback to settlement baseline coordinates.
   - Community contribution leaderboard and verified observation history list.
   - Kept WhatsApp and voice clutter completely out of the UI.

4. **Mobile Responsiveness (< 768px & 390×844 Viewport)**:
   - Sidebar transforms into a persistent bottom navigation tab bar (`.mobile-bottom-bar`) with touch targets ≥ 44px.
   - Header compacts into two balanced rows (Branding + Badges on row 1; Search + State filter on row 2).
   - Layer choices on the map transform into horizontal scrolling chips (`.mobile-layer-chips-container`) positioned above the map view.
   - Settlement detail panel transforms into an animated bottom sheet (`.settlement-panel-wrapper`) with three distinct height states:
     - `peek` (~96px): header, handle bar, and safety chip visible.
     - `half` (~52vh): core scores and safety banner in view.
     - `full` (~86vh): full scrollable content.
   - Draggable/clickable handle bar (`.sheet-handle-bar`) with touch support to cycle sheet height states.

5. **Accessibility & Quality Pass**:
   - Proper semantic HTML roles (`role="tablist"`, `role="tab"`, `role="dialog"`, `role="radiogroup"`), explicit form label bindings (`htmlFor`), and `aria-label` tags across all buttons, inputs, and SVG icons.
   - Focus management: `panelRef` and `tabIndex={-1}` automatically shift focus when a settlement is selected.
   - Keyboard operation for all tabs and controls; Escape key listener closes modals.
   - Text contrast ratios verified ≥ 4.5:1 against dark backgrounds (`#07111b`, `#0c1823`).
   - Touch targets meet minimum 44×44px standards.
   - Respects `prefers-reduced-motion: reduce` by disabling animations and smooth transitions.
   - Zero dead controls: every button, slider, filter, and tab is actively wired to application logic.

---

## 2026-10-10 - Phase U4: Quality Assurance, Automated Smoke Tests & Evidence

### Context & Goals
Execute end-to-end automated smoke testing with Playwright across desktop and mobile (390×844) viewports, verify cold-start AWS Lambda server waking states, capture clean UI evidence screenshots, and eliminate all console errors.

### Decisions Made
1. **Playwright E2E Smoke Test Suite (`tests/smoke.spec.js`)**:
   - Integrated `@playwright/test` running in headless Chromium across both Desktop (`1280×720`) and Mobile (`390×844`) viewports.
   - Asserted deterministic safety override: selecting `Mundaguda` immediately renders the red hatched safety banner above the fold and conceals all build recommendations.
   - Asserted DPR package compilation for safe sites (`Laxmipur`) including MGNREGA cost breakdown.
   - Asserted dynamic hydrological recalculation when moving the monsoon rainfall slider from `1.00x` to `0.60x` (deficit readout shifts from baseline to `-23.2 mm`).
   - Asserted complete Hindi bilingual UI translation while ensuring numbers and rule IDs remain untranslated.
   - Asserted multi-view navigation without any unhandled exceptions or console errors.
   - **Result**: 10 out of 10 tests passing in < 10 seconds.

2. **Server Cold-Start Notification (`SettlementPanel.jsx`)**:
   - Added a timer-driven status readout for first requests after idle. If API responses exceed 2.5 seconds, the UI explicitly notifies the user:
     `Waking up the server... (AWS Lambda cold start after idle, initial response takes ~5–8s)`.

3. **Curated Screenshot Evidence Gallery (`docs/screenshots/`)**:
   - Automated screenshot generation script (`scripts/capture_screenshots.js`) capturing 10 high-resolution PNGs covering all core user journeys:
     - Safe site overview & priority badge
     - Engineering plan specifications & state MGNREGA wage schedule
     - REJECTED safety override callout
     - Monsoon scenario simulator with Recharts water balance
     - Participatory field data observation form & community leaderboard
     - Multi-site reports & state-wise cost comparison table
     - Bilingual Hindi localization
     - First-run 3-step decision workflow guide modal
     - Mobile 390×844 bottom sheet and layer chips
     - Mobile 390×844 participatory field data form
   - Embedded screenshots into the top-level `README.md`.
