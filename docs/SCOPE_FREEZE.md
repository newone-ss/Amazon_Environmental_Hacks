# Scope Freeze - Bhujal MVP Features

The following features are frozen as part of the Minimum Viable Product (MVP) for the Amazon Environmental Hacks 2026 submission. No new features will be added to this list; any additional capabilities will be documented in `docs/future.md`.

## Frozen MVP Features

1. **Interactive geospatial map with layered scoring visualizers** - Core visualization of settlement points and scoring overlays.
2. **Groundwater recharge suitability calculation module** - Multi-criteria weighted linear combination for infiltration potential.
3. **Heat-water vulnerability scoring module** - Compound metric indexing surface thermal stress, hydrological deficit, and physical access constraints.
4. **Heuristic springhead desiccation risk index** - Morphometric and hydrological heuristic for seasonal drying probabilities.
5. **Deterministic safety veto evaluator** - Geotechnical and regulatory safety boundaries (slope stability, landslide hazard, flood buffer, ecological protection).
6. **Civil intervention composer with MGNREGA cost schedule** - Rule-based matching of site constraints to appropriate engineering structures with state-calibrated costing.
7. **Dynamic rainfall scenario slider with real-time score perturbation** - What-if analysis of rainfall variations (0.5x to 1.5x) and intervention resilience.
8. **Ground-truth field observation capture with photo upload capability** - Community monitoring system for submitting observations via text (WhatsApp) with optional photo upload.
9. **Downloadable planner action dossier (HTML/PDF format)** - Generated reports summarizing site evaluations and recommendations.
10. **Scientific validation and calibration panel** - Ground-truth comparison with CGWB and IMD datasets for model validation.

## Stubbed Features (Demo Only)

The following features are stubbed in the demonstration implementation, with only the text-based path functional:

- **WhatsApp Business API integration** - Inbound message processing for community observations (text path only; voice and media processing stubbed).
- **Voice note processing** - Audio file handling and transcription (stubbed; text observations only).
- **Amazon Transcribe integration** - Speech-to-text processing for voice observations (stubbed; text observations only).

## Implementation Status

All frozen MVP features are implemented and functional. Stubbed features accept input but produce deterministic placeholder responses for demonstration purposes.

## Change Control

Any modifications to this scope freeze require explicit documentation in `docs/future.md` and approval through the project's decision log (`docs/DECISIONS.md`).