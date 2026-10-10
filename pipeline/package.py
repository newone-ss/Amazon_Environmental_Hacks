"""
Bhujal — Phase 4 Lambda Packaging Script
=========================================
Builds a production deployment bundle for AWS SAM in build/lambda.

Inclusions:
- backend/
- scoring/
- agent/
- config/
- data/derived/

Strict Exclusions:
- data/raw/
- *.csv (all raw telemetry files)
- frontend/
- tests/
- __pycache__/ and *.pyc
"""

from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("package")

ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT_DIR / "build" / "lambda"


def build_lambda_package() -> None:
    logger.info("Packaging Bhujal Lambda bundle at %s", BUILD_DIR)

    # 1. Clean existing build directory
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Copy allowed source directories
    include_dirs = [
        ("backend", BUILD_DIR / "backend"),
        ("scoring", BUILD_DIR / "scoring"),
        ("agent", BUILD_DIR / "agent"),
        ("config", BUILD_DIR / "config"),
    ]

    for src_rel, dest in include_dirs:
        src = ROOT_DIR / src_rel
        if src.exists():
            shutil.copytree(
                src,
                dest,
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.pyo", ".pytest_cache"
                ),
            )
            logger.info("Copied %s -> %s", src_rel, dest.relative_to(ROOT_DIR))

    # 3. Copy only data/derived (never raw data or CSVs)
    derived_src = ROOT_DIR / "data" / "derived"
    derived_dest = BUILD_DIR / "data" / "derived"
    derived_dest.parent.mkdir(parents=True, exist_ok=True)
    if derived_src.exists():
        shutil.copytree(
            derived_src,
            derived_dest,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        logger.info("Copied data/derived -> %s", derived_dest.relative_to(ROOT_DIR))
    else:
        logger.error(
            "Derived directory missing at %s. Run 'python -m pipeline.build_derived' first.",
            derived_src,
        )
        sys.exit(1)

    # 4. Clean any residual pycache
    for pycache in BUILD_DIR.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache)

    # 5. Strict Validation and Assertions
    raw_data_dir = BUILD_DIR / "data" / "raw"
    if raw_data_dir.exists():
        raise AssertionError(
            "Validation failed: data/raw was packaged into Lambda bundle!"
        )

    raw_csvs = list(BUILD_DIR.rglob("*.csv"))
    if raw_csvs:
        raise AssertionError(
            f"Validation failed: Raw CSV files found in Lambda bundle: {raw_csvs}"
        )

    if (BUILD_DIR / "frontend").exists():
        raise AssertionError(
            "Validation failed: frontend directory found in Lambda bundle!"
        )

    if (BUILD_DIR / "tests").exists():
        raise AssertionError(
            "Validation failed: tests directory found in Lambda bundle!"
        )

    # Verify key entry points
    assert (BUILD_DIR / "backend" / "app.py").exists(), "backend/app.py missing"
    assert (BUILD_DIR / "scoring" / "engine.py").exists(), "scoring/engine.py missing"
    assert (BUILD_DIR / "data" / "derived" / "groundwater.json").exists(), (
        "groundwater.json missing"
    )
    assert (BUILD_DIR / "data" / "derived" / "temperature.json").exists(), (
        "temperature.json missing"
    )
    assert (BUILD_DIR / "data" / "derived" / "rainfall.json").exists(), (
        "rainfall.json missing"
    )
    assert (BUILD_DIR / "data" / "derived" / "settlements.json").exists(), (
        "settlements.json missing"
    )

    # Compute package size
    total_bytes = sum(f.stat().st_size for f in BUILD_DIR.rglob("*") if f.is_file())
    total_mb = total_bytes / (1024 * 1024)

    logger.info("============================================================")
    logger.info("LAMBDA PACKAGE VERIFICATION SUCCEEDED")
    logger.info("Destination : %s", BUILD_DIR)
    logger.info("Total Size  : %.2f MB (%d bytes)", total_mb, total_bytes)
    logger.info("Raw CSVs    : EXCLUDED (0 found)")
    logger.info("data/raw    : EXCLUDED")
    logger.info("frontend    : EXCLUDED")
    logger.info("tests       : EXCLUDED")
    logger.info("============================================================")


if __name__ == "__main__":
    build_lambda_package()
