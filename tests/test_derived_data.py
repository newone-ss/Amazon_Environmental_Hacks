"""
Tests for Phase 4 Data Handling
================================
Verifies:
1. Schema and completeness of precomputed derived JSON files in data/derived/.
2. Strict groundwater sign convention: seasonal rise = pre minus post
   (a deeper post-monsoon level gives a negative rise).
3. The FastAPI application, scoring engine, and derived loaders function
   without pandas installed / in sys.modules.
4. Packaging excludes raw data and CSVs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from scoring.derived_loader import (
    get_district_groundwater_summary,
    get_district_rainfall_summary,
    get_nearest_temperature_summary,
    get_settlement_derived_data,
    load_derived_groundwater,
    load_derived_rainfall,
    load_derived_settlements,
    load_derived_temperature,
)

DERIVED_DIR = Path(__file__).resolve().parent.parent / "data" / "derived"
BUILD_LAMBDA_DIR = Path(__file__).resolve().parent.parent / "build" / "lambda"


# ── 1. Derived JSON Schema & Content Tests ─────────────────────────


class TestDerivedDataSchemas:
    """Validate JSON schemas, data completeness, and physical ranges."""

    def test_derived_files_exist(self) -> None:
        required_files = [
            "groundwater.json",
            "temperature.json",
            "rainfall.json",
            "settlements.json",
            "unmatched_names.json",
        ]
        for fname in required_files:
            fpath = DERIVED_DIR / fname
            assert fpath.exists(), f"Derived file missing: {fname}"
            assert fpath.stat().st_size > 0, f"Derived file is empty: {fname}"

    def test_groundwater_schema_and_metrics(self) -> None:
        data = load_derived_groundwater()
        assert "metadata" in data
        assert "districts" in data
        assert "stations" in data

        meta = data["metadata"]
        assert meta["units"] == "meters below ground level (m bgl)"
        assert "sign_convention" in meta
        assert len(data["districts"]) >= 80
        assert len(data["stations"]) > 3000

        # Validate district structure
        for dist_info in data["districts"].values():
            assert "state" in dist_info
            assert "pre_monsoon_mean_depth_m" in dist_info
            assert "post_monsoon_mean_depth_m" in dist_info
            assert "seasonal_rise_m" in dist_info
            assert "lean_season_depth_m" in dist_info
            assert "trend_2021_2025_m_per_year" in dist_info

            # Physical plausibility
            assert 0.0 <= dist_info["pre_monsoon_mean_depth_m"] <= 100.0
            assert 0.0 <= dist_info["post_monsoon_mean_depth_m"] <= 100.0

    def test_temperature_schema_and_metrics(self) -> None:
        data = load_derived_temperature()
        assert "metadata" in data
        assert "grid_cells" in data

        meta = data["metadata"]
        assert meta["threshold_c"] == 40.0
        assert len(data["grid_cells"]) >= 70

        for cell_info in data["grid_cells"].values():
            assert "lat" in cell_info
            assert "lon" in cell_info
            assert "monthly_climatology_c" in cell_info
            assert "summer_mean_max_c" in cell_info
            assert "days_above_40c_per_year" in cell_info
            assert "trend_c_per_year" in cell_info

            # 12 months present
            clim = cell_info["monthly_climatology_c"]
            assert len(clim) == 12

            # Temperature plausibility in central/eastern India
            assert 20.0 <= cell_info["summer_mean_max_c"] <= 50.0

    def test_rainfall_schema_and_metrics(self) -> None:
        data = load_derived_rainfall()
        assert "metadata" in data
        assert "districts" in data

        assert len(data["districts"]) >= 80

        for dist_info in data["districts"].values():
            assert "state" in dist_info
            assert "monthly_climatology_mm" in dist_info
            assert "monsoon_total_mm" in dist_info
            assert "overall_departure_pct" in dist_info
            assert "departure_by_year" in dist_info

            dep_by_year = dist_info["departure_by_year"]
            assert len(dep_by_year) > 0
            for yinfo in dep_by_year.values():
                assert "monsoon_total_mm" in yinfo
                assert "monsoon_normal_mm" in yinfo
                assert "percent_departure" in yinfo

    def test_settlements_schema_and_coverage(self) -> None:
        data = load_derived_settlements()
        assert "metadata" in data
        assert "settlements" in data

        settlements = data["settlements"]
        assert len(settlements) == 13, "All 13 demo settlements must be mapped"

        expected_site_ids = [
            "site_001",
            "site_002",
            "site_003",
            "site_004",
            "site_005",
            "site_mp_001",
            "site_mp_002",
            "site_mp_003",
            "site_mp_004",
            "site_jh_001",
            "site_jh_002",
            "site_jh_003",
            "site_jh_004",
        ]
        for sid in expected_site_ids:
            assert sid in settlements, f"Settlement {sid} not in derived mappings"
            s = settlements[sid]
            assert s["provenance_tag"] == "derived"
            assert "groundwater" in s
            assert "temperature" in s
            assert "rainfall" in s

            # Ensure nearest station is populated
            assert s["groundwater"]["nearest_station"]["station_name"] is not None
            assert s["temperature"]["summer_mean_max_c"] is not None
            assert s["rainfall"]["district_monsoon_total_mm"] is not None

    def test_unmatched_names_audit(self) -> None:
        unmatched_path = DERIVED_DIR / "unmatched_names.json"
        with open(unmatched_path, "r", encoding="utf-8") as f:
            unmatched = json.load(f)

        assert unmatched["demo_districts_matched_in_groundwater"] is True
        assert unmatched["demo_districts_matched_in_rainfall"] is True
        assert unmatched["unmatched_demo_districts_gw"] == []
        assert unmatched["unmatched_demo_districts_rain"] == []


# ── 2. Groundwater Sign Convention Tests ──────────────────────────


class TestGroundwaterSignConvention:
    """
    Sign convention rule:
    seasonal_rise = pre_monsoon_depth - post_monsoon_depth
    Depths are meters below ground level (m bgl).
    - If water table rises (post-monsoon is shallower, e.g. 5m post vs 8m pre),
      rise = 8 - 5 = +3m (positive).
    - If water table drops/depletes (post-monsoon is deeper, e.g. 8m post vs 5m pre),
      rise = 5 - 8 = -3m (negative).
    """

    def test_sign_convention_formula(self) -> None:
        # Pre-monsoon: 5.0m bgl; Post-monsoon: 8.0m bgl (deeper)
        pre_depth = 5.0
        post_depth = 8.0
        rise = pre_depth - post_depth
        assert rise == -3.0
        assert rise < 0.0, "Deeper post-monsoon level MUST give negative seasonal rise"

        # Pre-monsoon: 8.0m bgl; Post-monsoon: 3.0m bgl (shallower / recharged)
        pre_recharged = 8.0
        post_recharged = 3.0
        rise_recharged = pre_recharged - post_recharged
        assert rise_recharged == +5.0
        assert rise_recharged > 0.0, (
            "Shallower post-monsoon level MUST give positive seasonal rise"
        )

    def test_sign_convention_invariance_across_districts(self) -> None:
        gw_data = load_derived_groundwater()
        for dist_name, dist in gw_data["districts"].items():
            pre = dist["pre_monsoon_mean_depth_m"]
            post = dist["post_monsoon_mean_depth_m"]
            expected_rise = round(pre - post, 2)
            actual_rise = dist["seasonal_rise_m"]
            assert actual_rise == pytest.approx(expected_rise, abs=0.01), (
                f"Sign convention mismatch for district {dist_name}: "
                f"pre={pre}, post={post}, expected={expected_rise}, got={actual_rise}"
            )

    def test_sign_convention_invariance_across_stations(self) -> None:
        gw_data = load_derived_groundwater()
        negative_rise_found = False
        for st in gw_data["stations"]:
            pre = st["pre_monsoon_depth_m"]
            post = st["post_monsoon_depth_m"]
            expected_rise = round(pre - post, 2)
            actual_rise = st["seasonal_rise_m"]
            assert actual_rise == pytest.approx(expected_rise, abs=0.01), (
                f"Sign convention mismatch for station {st['station']}"
            )
            if actual_rise < 0.0:
                negative_rise_found = True

        assert negative_rise_found, (
            "Expected at least one station exhibiting a negative seasonal rise"
        )


# ── 3. Runtime Decoupling: API Starts Without Pandas ───────────────


class TestPandasDecoupling:
    """Verify that backend API, scoring engine, and derived loaders function without pandas."""

    def test_derived_loaders_without_pandas(self) -> None:
        """Derived loaders must load data cleanly when pandas is unavailable."""
        with patch.dict(sys.modules, {"pandas": None}):
            # Clear caches to ensure execution from scratch
            load_derived_groundwater.cache_clear()
            load_derived_temperature.cache_clear()
            load_derived_rainfall.cache_clear()
            load_derived_settlements.cache_clear()

            gw = load_derived_groundwater()
            assert "districts" in gw
            assert len(gw["districts"]) > 0

            temp = load_derived_temperature()
            assert "grid_cells" in temp

            rain = load_derived_rainfall()
            assert "districts" in rain

            settlements = load_derived_settlements()
            assert len(settlements["settlements"]) == 13

            # Query helpers
            settlement_info = get_settlement_derived_data("site_001")
            assert settlement_info is not None
            assert settlement_info["norm_district"] == "KORAPUT"

            dist_gw = get_district_groundwater_summary("KORAPUT")
            assert dist_gw is not None

            dist_rain = get_district_rainfall_summary("KORAPUT")
            assert dist_rain is not None

            temp_cell = get_nearest_temperature_summary(18.8124, 82.7133)
            assert temp_cell is not None

    def test_api_starts_and_responds_without_pandas(self) -> None:
        """FastAPI client must boot and serve requests with pandas blocked."""
        with patch.dict(sys.modules, {"pandas": None}):
            client = TestClient(app)

            # Metadata endpoint
            meta_resp = client.get("/meta")
            assert meta_resp.status_code == 200
            meta_data = meta_resp.json()
            assert meta_data["version"] == "0.2.0"

            # Villages endpoint
            villages_resp = client.get("/villages")
            assert villages_resp.status_code == 200
            assert len(villages_resp.json()) == 13

            # Site evaluation endpoint
            site_resp = client.get("/sites/site_001")
            assert site_resp.status_code == 200
            site_data = site_resp.json()
            assert site_data["village"]["id"] == "site_001"
            assert len(site_data["scores"]) == 3

            # Derived telemetry endpoint
            telemetry_resp = client.get("/telemetry/site_001")
            assert telemetry_resp.status_code == 200
            tdata = telemetry_resp.json()
            assert tdata["provenance_tag"] == "derived"
            assert (
                tdata["groundwater"]["nearest_station"]["station_name"] == "Koraput-i"
            )


# ── 4. Package Exclusions Test ────────────────────────────────────


class TestPackageExclusions:
    """Verify that build/lambda does not bundle raw CSVs or raw directories."""

    def test_package_excludes_raw_data(self) -> None:
        # Build or check build/lambda
        from pipeline.package import build_lambda_package

        build_lambda_package()

        assert BUILD_LAMBDA_DIR.exists()
        assert not (BUILD_LAMBDA_DIR / "data" / "raw").exists()

        # Confirm zero CSV files packaged
        csv_files = list(BUILD_LAMBDA_DIR.rglob("*.csv"))
        assert len(csv_files) == 0, f"Found raw CSVs in Lambda build: {csv_files}"

        # Confirm derived files exist
        assert (BUILD_LAMBDA_DIR / "data" / "derived" / "groundwater.json").exists()
        assert (BUILD_LAMBDA_DIR / "data" / "derived" / "temperature.json").exists()
        assert (BUILD_LAMBDA_DIR / "data" / "derived" / "rainfall.json").exists()
        assert (BUILD_LAMBDA_DIR / "data" / "derived" / "settlements.json").exists()
