"""
Bhujal — Phase 4 Derived Data Loader
====================================
Provides thread-safe, lazy, cached access to pre-aggregated derived datasets
in data/derived/*.json.

Guarantees:
- Never imports pandas
- Never reads raw CSVs (~8.9 MB)
- Never reads files at module import time
- Cached via @lru_cache(maxsize=1) for sub-millisecond repeated queries
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger("derived_loader")

DERIVED_DIR = Path(__file__).resolve().parent.parent / "data" / "derived"


@lru_cache(maxsize=1)
def load_derived_groundwater() -> dict[str, Any]:
    """Lazily load and cache precomputed CGWB groundwater summaries."""
    path = DERIVED_DIR / "groundwater.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    logger.warning("Derived groundwater file missing at %s", path)
    return {"metadata": {}, "districts": {}, "stations": []}


@lru_cache(maxsize=1)
def load_derived_temperature() -> dict[str, Any]:
    """Lazily load and cache precomputed IMD temperature climatology."""
    path = DERIVED_DIR / "temperature.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    logger.warning("Derived temperature file missing at %s", path)
    return {"metadata": {}, "grid_cells": {}}


@lru_cache(maxsize=1)
def load_derived_rainfall() -> dict[str, Any]:
    """Lazily load and cache precomputed IMD rainfall statistics."""
    path = DERIVED_DIR / "rainfall.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    logger.warning("Derived rainfall file missing at %s", path)
    return {"metadata": {}, "districts": {}}


@lru_cache(maxsize=1)
def load_derived_settlements() -> dict[str, Any]:
    """Lazily load and cache mapped demonstration settlements."""
    path = DERIVED_DIR / "settlements.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    logger.warning("Derived settlements file missing at %s", path)
    return {"metadata": {}, "settlements": {}}


def get_settlement_derived_data(site_id: str) -> dict[str, Any] | None:
    """Retrieve derived empirical indicators for a demonstration settlement."""
    settlements = load_derived_settlements().get("settlements", {})
    return settlements.get(site_id)


def get_district_groundwater_summary(district: str) -> dict[str, Any] | None:
    """Retrieve derived groundwater metrics for a normalized district."""
    norm = " ".join(district.strip().upper().split())
    return load_derived_groundwater().get("districts", {}).get(norm)


def get_district_rainfall_summary(district: str) -> dict[str, Any] | None:
    """Retrieve derived rainfall statistics for a normalized district."""
    norm = " ".join(district.strip().upper().split())
    return load_derived_rainfall().get("districts", {}).get(norm)


def get_nearest_temperature_summary(lat: float, lon: float) -> dict[str, Any] | None:
    """Retrieve derived temperature climatology for the nearest 1.0 deg grid cell."""
    grid_cells = load_derived_temperature().get("grid_cells", {})
    if not grid_cells:
        return None

    best_cell = None
    min_dist_sq = float("inf")
    for cell in grid_cells.values():
        clat, clon = cell["lat"], cell["lon"]
        d2 = (clat - lat) ** 2 + (clon - lon) ** 2
        if d2 < min_dist_sq:
            min_dist_sq = d2
            best_cell = cell

    return best_cell
