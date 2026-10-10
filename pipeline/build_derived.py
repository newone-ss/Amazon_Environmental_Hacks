"""
Bhujal — Phase 4 Data Pipeline: Build Derived Datasets
======================================================
Processes raw empirical CSVs (CGWB Groundwater, IMD Max Temperature, IMD Rainfall)
using pandas and generates compact, pre-aggregated derived JSON files in data/derived/.

Lambda functions and runtime engines load ONLY the lightweight derived JSON files
lazily with caching, ensuring fast cold starts (<50ms) and zero raw CSV parsing.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("build_derived")

# Standard canonical district alias dictionary for Odisha, MP, and Jharkhand
DISTRICT_ALIASES: dict[str, str] = {
    # Jharkhand
    "WEST SINGHBHUM (CHAIBASA)": "WEST SINGHBHUM",
    "PASHCHIMI SINGHBHUM": "WEST SINGHBHUM",
    "EAST  SINGHBHUM (JAMSHEDPUR)": "EAST SINGHBHUM",
    "EAST SINGHBHUM (JAMSHEDPUR)": "EAST SINGHBHUM",
    "PURBI SINGHBHUM": "EAST SINGHBHUM",
    "HAZARIBAG": "HAZARIBAGH",
    "KODARMA": "KODERMA",
    "PALAMAU": "PALAMU",
    # Madhya Pradesh
    "HOSHANGABAD": "NARMADAPURAM",
    "WEST NIMAR": "KHARGONE",
    "EAST NIMAR": "KHANDWA",
    "NEEMUCH": "NEEMUCH",
    "NIMACH": "NEEMUCH",
    "NARSIMHAPUR": "NARSINGHPUR",
    "NARSHIMAPURA": "NARSINGHPUR",
    "AGAR MALWA": "AGAR-MALWA",
    "ASHOK NAGAR": "ASHOKNAGAR",
    "VIDISHA": "VIDISHA",
    "VIDESHA": "VIDISHA",
    # Odisha
    "SONAPUR": "SUBARNAPUR",
    "BAUDH": "BOUDH",
    "BAUDA": "BOUDH",
    "BARGARH": "BARGARH",
    "BARAGARH": "BARGARH",
    "GAJAPATI": "GAJAPATI",
    "GAJAPATHI": "GAJAPATI",
    "RAYAGADA": "RAYAGADA",
    "RAYAGARHA": "RAYAGADA",
    "DEBAGARH": "DEOGARH",
    "KENDRAPARA": "KENDRAPARA",
    "KENDRAPARHA": "KENDRAPARA",
    "NUAPADA": "NUAPADA",
    "NUAPARHA": "NUAPADA",
}


def normalize_district_name(raw_name: str | None) -> str:
    """Normalize district names across datasets to uppercase canonical form."""
    if not raw_name or pd.isna(raw_name):
        return "UNKNOWN"
    cleaned = " ".join(str(raw_name).strip().upper().split())
    return DISTRICT_ALIASES.get(cleaned, cleaned)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two points on Earth in kilometers."""
    r = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2.0) ** 2
    return float(2.0 * r * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0))))


def build_groundwater_derived(
    csv_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Process CGWB groundwater hydrographs.
    Outputs pre/post-monsoon depth, seasonal rise (pre - post), 2021-2025 trend,
    and lean-season depth by district and key stations.
    """
    logger.info("Processing groundwater data from %s", csv_path)
    df = pd.read_csv(csv_path)

    # Clean missing level records
    df = df.dropna(subset=["groundwater_level_m"]).copy()
    # Filter physical extremes (groundwater depth > 300m or < -2m are sensor artifacts)
    df = df[(df["groundwater_level_m"] >= -2.0) & (df["groundwater_level_m"] <= 150.0)]

    df["dt"] = pd.to_datetime(df["measurement_datetime"])
    df["year"] = df["dt"].dt.year
    df["month"] = df["dt"].dt.month
    df["norm_district"] = df["district"].apply(normalize_district_name)

    # Pre-monsoon: April (4), May (5)
    # Post-monsoon: August (8), September (9), November (11)
    districts_data: dict[str, Any] = {}
    stations_data: list[dict[str, Any]] = []

    for dist, grp in df.groupby("norm_district"):
        pre_grp = grp[grp["month"].isin([4, 5])]
        post_grp = grp[grp["month"].isin([8, 9, 11])]
        lean_grp = grp[grp["month"].isin([1, 5])]

        pre_mean = (
            float(pre_grp["groundwater_level_m"].mean())
            if len(pre_grp) > 0
            else float(grp["groundwater_level_m"].mean())
        )
        post_mean = (
            float(post_grp["groundwater_level_m"].mean())
            if len(post_grp) > 0
            else float(grp["groundwater_level_m"].mean())
        )

        pre_val = round(pre_mean, 2)
        post_val = round(post_mean, 2)
        # Sign convention: seasonal rise = pre minus post
        # A deeper post-monsoon level gives a negative rise
        seasonal_rise = round(pre_val - post_val, 2)

        lean_depth = (
            float(lean_grp["groundwater_level_m"].mean())
            if len(lean_grp) > 0
            else float(grp["groundwater_level_m"].max())
        )

        # 2021-2025 trend: annual slope of yearly mean depths (meters per year)
        yearly_means = grp.groupby("year")["groundwater_level_m"].mean().dropna()
        if len(yearly_means) >= 2:
            years = yearly_means.index.values.astype(float)
            levels = yearly_means.values.astype(float)
            slope, _ = np.polyfit(years, levels, 1)
            trend_m_yr = float(slope)
        else:
            trend_m_yr = 0.0

        districts_data[dist] = {
            "state": grp["state"].iloc[0],
            "station_count": int(grp["station"].nunique()),
            "reading_count": len(grp),
            "pre_monsoon_mean_depth_m": pre_val,
            "post_monsoon_mean_depth_m": post_val,
            "seasonal_rise_m": seasonal_rise,
            "lean_season_depth_m": round(lean_depth, 2),
            "trend_2021_2025_m_per_year": round(trend_m_yr, 3),
        }

    for st_name, sgrp in df.groupby("station"):
        s_pre = sgrp[sgrp["month"].isin([4, 5])]["groundwater_level_m"].mean()
        s_post = sgrp[sgrp["month"].isin([8, 9, 11])]["groundwater_level_m"].mean()
        s_pre_val = (
            round(float(s_pre), 2)
            if pd.notna(s_pre)
            else round(float(sgrp["groundwater_level_m"].mean()), 2)
        )
        s_post_val = (
            round(float(s_post), 2)
            if pd.notna(s_post)
            else round(float(sgrp["groundwater_level_m"].mean()), 2)
        )
        stations_data.append(
            {
                "station": st_name,
                "district": sgrp["norm_district"].iloc[0],
                "state": sgrp["state"].iloc[0],
                "lat": float(sgrp["latitude"].iloc[0]),
                "lon": float(sgrp["longitude"].iloc[0]),
                "reading_count": len(sgrp),
                "pre_monsoon_depth_m": s_pre_val,
                "post_monsoon_depth_m": s_post_val,
                "seasonal_rise_m": round(s_pre_val - s_post_val, 2),
            }
        )

    result = {
        "metadata": {
            "source": "Central Ground Water Board (CGWB)",
            "date_range": [str(df["dt"].min().date()), str(df["dt"].max().date())],
            "units": "meters below ground level (m bgl)",
            "sign_convention": "seasonal_rise = pre_monsoon_depth - post_monsoon_depth (positive = water table rose)",
            "total_districts": len(districts_data),
            "total_stations": len(stations_data),
        },
        "districts": districts_data,
        "stations": stations_data,
    }
    return result, stations_data


def build_temperature_derived(
    csv_path: Path, threshold_c: float = 40.0
) -> dict[str, Any]:
    """
    Process IMD maximum temperature gridded data (2021-2024).
    Outputs monthly climatology, summer mean max (March-June),
    days above threshold (default 40C), and 4-year trends per grid cell.
    """
    logger.info(
        "Processing temperature data from %s (threshold=%.1f C)", csv_path, threshold_c
    )
    df = pd.read_csv(csv_path)

    df["dt"] = pd.to_datetime(df["date"])
    df["year"] = df["dt"].dt.year
    df["month"] = df["dt"].dt.month

    grid_cells: dict[str, Any] = {}

    for (lat, lon), grp in df.groupby(["latitude", "longitude"]):
        cell_key = f"{lat:.1f}_{lon:.1f}"

        # Monthly climatology
        monthly_clim: dict[str, float] = {}
        for m, mgrp in grp.groupby("month"):
            monthly_clim[str(m)] = round(float(mgrp["maximum_temperature_c"].mean()), 2)

        # Summer mean max
        summer_grp = grp[grp["month"].isin([3, 4, 5, 6])]
        summer_mean = (
            float(summer_grp["maximum_temperature_c"].mean())
            if len(summer_grp) > 0
            else float(grp["maximum_temperature_c"].mean())
        )

        # Days above threshold
        total_days = len(grp)
        days_above = int((grp["maximum_temperature_c"] >= threshold_c).sum())
        years_count = grp["year"].nunique() or 1
        annual_days_above = round(days_above / years_count, 1)

        # Linear trend: annual mean max temp slope
        yearly_means = grp.groupby("year")["maximum_temperature_c"].mean().dropna()
        if len(yearly_means) >= 2:
            years = yearly_means.index.values.astype(float)
            temps = yearly_means.values.astype(float)
            slope, _ = np.polyfit(years, temps, 1)
            trend_slope = float(slope)
        else:
            trend_slope = 0.0

        grid_cells[cell_key] = {
            "lat": float(lat),
            "lon": float(lon),
            "total_records": int(total_days),
            "monthly_climatology_c": monthly_clim,
            "summer_mean_max_c": round(summer_mean, 2),
            f"days_above_{int(threshold_c)}c_total": days_above,
            f"days_above_{int(threshold_c)}c_per_year": annual_days_above,
            "trend_c_per_year": round(trend_slope, 3),
            "absolute_max_c": round(float(grp["maximum_temperature_c"].max()), 2),
            "absolute_min_c": round(float(grp["maximum_temperature_c"].min()), 2),
        }

    return {
        "metadata": {
            "source": "India Meteorological Department (IMD)",
            "date_range": [str(df["dt"].min().date()), str(df["dt"].max().date())],
            "units": "degrees Celsius (deg C)",
            "threshold_c": threshold_c,
            "grid_resolution_deg": 1.0,
            "total_grid_points": len(grid_cells),
        },
        "grid_cells": grid_cells,
    }


def build_rainfall_derived(csv_path: Path) -> dict[str, Any]:
    """
    Process IMD daily rainfall data.
    Outputs monthly climatology, monsoon cumulative total, and departure statistics by district.
    """
    logger.info("Processing rainfall data from %s", csv_path)
    df = pd.read_csv(csv_path)

    df["dt"] = pd.to_datetime(df["date"])
    df["year"] = df["dt"].dt.year
    df["month"] = df["dt"].dt.month
    df["norm_district"] = df["district"].apply(normalize_district_name)

    districts_data: dict[str, Any] = {}

    for dist, grp in df.groupby("norm_district"):
        # Monthly totals & daily averages
        monthly_clim: dict[str, Any] = {}
        for m, mgrp in grp.groupby("month"):
            monthly_clim[str(m)] = {
                "total_mm": round(float(mgrp["daily_rainfall_mm"].sum()), 1),
                "daily_mean_mm": round(float(mgrp["daily_rainfall_mm"].mean()), 2),
                "daily_normal_mean_mm": round(float(mgrp["daily_normal_mm"].mean()), 2),
            }

        monsoon_total_mm = round(float(grp["daily_rainfall_mm"].sum()), 1)
        monsoon_normal_mm = round(float(grp["daily_normal_mm"].sum()), 1)
        mean_dep_pct = (
            float(grp["daily_departure_percent"].dropna().mean())
            if grp["daily_departure_percent"].dropna().shape[0] > 0
            else 0.0
        )

        departure_by_year: dict[str, Any] = {}
        for y, ygrp in grp.groupby("year"):
            y_tot = float(ygrp["daily_rainfall_mm"].sum())
            y_norm = float(ygrp["daily_normal_mm"].sum())
            y_dep = round(((y_tot - y_norm) / y_norm * 100.0), 1) if y_norm > 0 else 0.0
            departure_by_year[str(y)] = {
                "monsoon_total_mm": round(y_tot, 1),
                "monsoon_normal_mm": round(y_norm, 1),
                "percent_departure": y_dep,
            }

        districts_data[dist] = {
            "state": grp["state"].iloc[0],
            "days_monitored": len(grp),
            "monthly_climatology_mm": monthly_clim,
            "monsoon_total_mm": monsoon_total_mm,
            "monsoon_normal_mm": monsoon_normal_mm,
            "overall_departure_pct": round(
                ((monsoon_total_mm - monsoon_normal_mm) / monsoon_normal_mm * 100.0)
                if monsoon_normal_mm > 0
                else 0.0,
                1,
            ),
            "departure_by_year": departure_by_year,
            "mean_daily_departure_pct": round(mean_dep_pct, 2),
            "categories": grp["daily_rainfall_category"].value_counts().to_dict(),
        }

    return {
        "metadata": {
            "source": "India Meteorological Department (IMD)",
            "date_range": [str(df["dt"].min().date()), str(df["dt"].max().date())],
            "units": "millimeters (mm)",
            "total_districts": len(districts_data),
        },
        "districts": districts_data,
    }


def map_settlements_to_derived(
    demo_sites_path: Path,
    gw_data: dict[str, Any],
    temp_data: dict[str, Any],
    rain_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Map each of the 13 demo settlements to its district & nearest empirical observation stations.
    """
    logger.info("Mapping demo sites from %s to derived datasets", demo_sites_path)
    with open(demo_sites_path, "r", encoding="utf-8") as f:
        demo_sites = yaml.safe_load(f).get("sites", [])

    grid_items = [
        (cell["lat"], cell["lon"], cell) for cell in temp_data["grid_cells"].values()
    ]
    stations = gw_data.get("stations", [])

    mapped_settlements: dict[str, Any] = {}

    for s in demo_sites:
        site_id = s["id"]
        slat, slon = float(s["lat"]), float(s["lon"])
        norm_dist = normalize_district_name(s.get("district"))

        # 1. District Groundwater Summary
        dist_gw = gw_data["districts"].get(norm_dist)

        # 2. Nearest CGWB Station
        nearest_st = None
        min_st_dist = float("inf")
        for st in stations:
            d = haversine_distance_km(slat, slon, st["lat"], st["lon"])
            if d < min_st_dist:
                min_st_dist = d
                nearest_st = st

        # 3. Nearest IMD Temperature Grid Cell
        nearest_grid = None
        min_grid_dist = float("inf")
        for glat, glon, gcell in grid_items:
            d = haversine_distance_km(slat, slon, glat, glon)
            if d < min_grid_dist:
                min_grid_dist = d
                nearest_grid = gcell

        # 4. District Rainfall Summary
        dist_rain = rain_data["districts"].get(norm_dist)

        mapped_settlements[site_id] = {
            "name": s["name"],
            "district": s.get("district"),
            "norm_district": norm_dist,
            "state": s.get("state"),
            "lat": slat,
            "lon": slon,
            "provenance_tag": "derived",
            "groundwater": {
                "district_summary": dist_gw,
                "nearest_station": {
                    "station_name": nearest_st["station"] if nearest_st else None,
                    "distance_km": round(min_st_dist, 1) if nearest_st else None,
                    "pre_monsoon_depth_m": nearest_st.get("pre_monsoon_depth_m")
                    if nearest_st
                    else None,
                    "post_monsoon_depth_m": nearest_st.get("post_monsoon_depth_m")
                    if nearest_st
                    else None,
                    "seasonal_rise_m": nearest_st.get("seasonal_rise_m")
                    if nearest_st
                    else None,
                }
                if nearest_st
                else None,
            },
            "temperature": {
                "nearest_grid_lat": nearest_grid["lat"] if nearest_grid else None,
                "nearest_grid_lon": nearest_grid["lon"] if nearest_grid else None,
                "distance_km": round(min_grid_dist, 1) if nearest_grid else None,
                "summer_mean_max_c": nearest_grid.get("summer_mean_max_c")
                if nearest_grid
                else None,
                "days_above_40c_per_year": nearest_grid.get("days_above_40c_per_year")
                if nearest_grid
                else None,
                "trend_c_per_year": nearest_grid.get("trend_c_per_year")
                if nearest_grid
                else None,
            },
            "rainfall": {
                "district_monsoon_total_mm": dist_rain.get("monsoon_total_mm")
                if dist_rain
                else None,
                "district_departure_pct": dist_rain.get("overall_departure_pct")
                if dist_rain
                else None,
                "district_departure_by_year": dist_rain.get("departure_by_year")
                if dist_rain
                else None,
            },
        }

    return {
        "metadata": {
            "description": "Mapping of 13 Bhujal demonstration settlements to nearest derived empirical indicators",
            "total_settlements": len(mapped_settlements),
            "provenance_tag": "derived",
        },
        "settlements": mapped_settlements,
    }


def find_unmatched_names(
    gw_data: dict[str, Any], rain_data: dict[str, Any], demo_sites_path: Path
) -> dict[str, Any]:
    """Identify any district or station names that were unmapped or mismatched."""
    with open(demo_sites_path, "r", encoding="utf-8") as f:
        sites = yaml.safe_load(f).get("sites", [])

    demo_districts = {normalize_district_name(s.get("district")) for s in sites}
    gw_districts = set(gw_data["districts"].keys())
    rain_districts = set(rain_data["districts"].keys())

    unmatched_demo_gw = demo_districts - gw_districts
    unmatched_demo_rain = demo_districts - rain_districts
    gw_not_in_rain = sorted(gw_districts - rain_districts)
    rain_not_in_gw = sorted(rain_districts - gw_districts)

    return {
        "demo_districts_matched_in_groundwater": len(unmatched_demo_gw) == 0,
        "demo_districts_matched_in_rainfall": len(unmatched_demo_rain) == 0,
        "unmatched_demo_districts_gw": list(unmatched_demo_gw),
        "unmatched_demo_districts_rain": list(unmatched_demo_rain),
        "districts_in_gw_not_in_rain": gw_not_in_rain,
        "districts_in_rain_not_in_gw": rain_not_in_gw,
        "normalized_aliases_applied": DISTRICT_ALIASES,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build derived datasets from raw CSVs."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Path to directory containing raw CSVs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/derived"),
        help="Output directory for derived JSON files.",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("config"),
        help="Path to directory containing demo_sites.yaml.",
    )
    parser.add_argument(
        "--temp-threshold",
        type=float,
        default=40.0,
        help="Configurable threshold for high-temperature days (deg C).",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    gw_csv = (
        args.data_dir / "groundwater_level_cleaned_odisha_jharkhand_mp_2021_2025.csv"
    )
    temp_csv = args.data_dir / "imd_max_temperature_odisha_jharkhand_mp_2021_2024.csv"
    rain_csv = args.data_dir / "rainfall_cleaned_odisha_jharkhand_mp.csv"
    demo_sites_yaml = args.config_dir / "demo_sites.yaml"

    # 1. Process Groundwater
    gw_derived, _ = build_groundwater_derived(gw_csv)
    gw_out = args.output_dir / "groundwater.json"
    with open(gw_out, "w", encoding="utf-8") as f:
        json.dump(gw_derived, f, indent=2)
    logger.info("Saved %s (%.1f KB)", gw_out, gw_out.stat().st_size / 1024)

    # 2. Process Temperature
    temp_derived = build_temperature_derived(temp_csv, threshold_c=args.temp_threshold)
    temp_out = args.output_dir / "temperature.json"
    with open(temp_out, "w", encoding="utf-8") as f:
        json.dump(temp_derived, f, indent=2)
    logger.info("Saved %s (%.1f KB)", temp_out, temp_out.stat().st_size / 1024)

    # 3. Process Rainfall
    rain_derived = build_rainfall_derived(rain_csv)
    rain_out = args.output_dir / "rainfall.json"
    with open(rain_out, "w", encoding="utf-8") as f:
        json.dump(rain_derived, f, indent=2)
    logger.info("Saved %s (%.1f KB)", rain_out, rain_out.stat().st_size / 1024)

    # 4. Map 13 settlements
    settlements_derived = map_settlements_to_derived(
        demo_sites_yaml, gw_derived, temp_derived, rain_derived
    )
    settlements_out = args.output_dir / "settlements.json"
    with open(settlements_out, "w", encoding="utf-8") as f:
        json.dump(settlements_derived, f, indent=2)
    logger.info(
        "Saved %s (%.1f KB)", settlements_out, settlements_out.stat().st_size / 1024
    )

    # 5. Unmatched names analysis
    unmatched_names = find_unmatched_names(gw_derived, rain_derived, demo_sites_yaml)
    unmatched_out = args.output_dir / "unmatched_names.json"
    with open(unmatched_out, "w", encoding="utf-8") as f:
        json.dump(unmatched_names, f, indent=2)
    logger.info(
        "Saved %s (%.1f KB)", unmatched_out, unmatched_out.stat().st_size / 1024
    )

    print("\n" + "=" * 60)
    print("PHASE 4 DERIVED DATASET GENERATION SUMMARY")
    print("=" * 60)
    print(f"groundwater.json  : {gw_out.stat().st_size / 1024:.1f} KB")
    print(f"temperature.json  : {temp_out.stat().st_size / 1024:.1f} KB")
    print(f"rainfall.json     : {rain_out.stat().st_size / 1024:.1f} KB")
    print(f"settlements.json  : {settlements_out.stat().st_size / 1024:.1f} KB")
    print(f"unmatched_names   : {unmatched_out.stat().st_size / 1024:.1f} KB")
    print("-" * 60)
    print(f"Demo sites mapped : {len(settlements_derived['settlements'])}/13")
    print(f"Demo unmapped GW  : {unmatched_names['unmatched_demo_districts_gw']}")
    print(f"Demo unmapped Rain: {unmatched_names['unmatched_demo_districts_rain']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
