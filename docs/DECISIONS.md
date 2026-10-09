# Decisions Log

> Every non-trivial design decision is recorded here with date, context, and rationale.

---

## 2026-10-09 — Phase 0

### D001: Demo AOI — Koraput District, Odisha
**Context**: Need one area for demo. Must be hilly, tribal, with springs and heat-water stress.
**Decision**: Koraput District, Odisha (bounding box: 82.05–83.40°E, 18.25–19.30°N).
**Rationale**: Eastern Ghats, tribal population (>50%), known spring-fed villages, monsoon-dependent, IMD rainfall data available. Fits all demo requirements.
**Risk**: Bounding box is simplified; actual district boundary is more complex.

### D002: Score Schema — Five Mandatory Fields
**Context**: Rule 4 requires every score to return value, class, drivers, confidence, data_quality_note.
**Decision**: Pydantic `ScoreResult` model enforces this at the type level.
**Rationale**: Compile-time safety > runtime checks. Any scoring function that doesn't return this shape will fail type checking and tests.

### D003: Safety Rules — Config-Driven, Not Hard-Coded
**Context**: Safety thresholds (slope, seismic zone, flood buffer) could be constants in code or in config.
**Decision**: All thresholds in `config/safety_rules.yaml`.
**Rationale**: Domain experts can adjust thresholds without touching Python code. Easier to validate and audit.

### D004: Cost Estimates — Order-of-Magnitude Only
**Context**: Intervention costs vary hugely by site. We can't produce BOQ-level estimates.
**Decision**: Show cost as a range (low–high) in INR with explicit assumptions list and confidence level.
**Rationale**: Honest presentation. UI will show "Indicative" badge.

### D005: Illustrative Data Tag for Demo
**Context**: We don't have real field data for the demo villages.
**Decision**: All demo site data tagged `DataTag.ILLUSTRATIVE`. UI will show a badge.
**Rationale**: Rule 3 — never fabricate data. Synthetic stand-ins must be clearly labelled.
