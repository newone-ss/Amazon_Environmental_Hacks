#!/usr/bin/env python3
"""
Smoke test script for Bhujal deployed API.
Tests all major endpoints to ensure the deployment is working correctly.
"""

import argparse
import json
import sys
import uuid
from urllib.parse import urljoin

import requests


def test_endpoint(
    method, url, data=None, files=None, params=None, expected_status=200, description=""
):
    """Helper function to test an endpoint and report results."""
    print(f"\nTesting: {description}")
    print(f"  {method} {url}")

    try:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            if files:
                resp = requests.post(url, data=data, files=files, timeout=30)
            else:
                resp = requests.post(url, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")

        print(f"  Status: {resp.status_code} (expected {expected_status})")

        if resp.status_code != expected_status:
            print("  ERROR: Unexpected status code")
            print(f"  Response: {resp.text[:500]}")
            return False

        # Try to parse JSON response for most endpoints
        if resp.headers.get("content-type", "").startswith("application/json"):
            try:
                data = resp.json()
                print(
                    f"  Response JSON keys: {list(data.keys()) if isinstance(data, dict) else 'Non-dict JSON'}"
                )
                if isinstance(data, dict) and len(data) < 10:
                    print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
            except json.JSONDecodeError:
                print(f"  Response (non-JSON): {resp.text[:200]}")
        else:
            print(f"  Response length: {len(resp.content)} bytes")
            if len(resp.content) < 200:
                print(f"  Response: {resp.content}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Request failed: {e}")
        return False
    except Exception as e:  # noqa: BLE001
        print(f"  ERROR: Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Smoke test for Bhujal deployed API")
    parser.add_argument(
        "--url",
        required=True,
        help="Base URL of the deployed API (e.g., https://abcde12345.execute-api.us-east-1.amazonaws.com/prod)",
    )
    parser.add_argument(
        "--site-id", default="site_001", help="Site ID to use for tests"
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="Request timeout in seconds"
    )
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    site_id = args.site_id

    print(f"Starting smoke test for API at: {base_url}")
    print(f"Using site ID: {site_id}")
    print("=" * 60)

    # Track test results
    tests_passed = 0
    tests_total = 0

    # Test 1: /meta endpoint
    tests_total += 1
    if test_endpoint("GET", urljoin(base_url, "/meta"), description="Get API metadata"):
        tests_passed += 1

    # Test 2: /villages endpoint
    tests_total += 1
    if test_endpoint(
        "GET", urljoin(base_url, "/villages"), description="List all villages"
    ):
        tests_passed += 1

    # Test 3: /villages with state filter
    tests_total += 1
    if test_endpoint(
        "GET",
        urljoin(base_url, "/villages"),
        params={"state": "Odisha"},
        description="List villages filtered by state",
    ):
        tests_passed += 1

    # Test 4: /sites/{site_id} endpoint
    tests_total += 1
    if test_endpoint(
        "GET",
        urljoin(base_url, f"/sites/{site_id}"),
        description=f"Get details for site {site_id}",
    ):
        tests_passed += 1

    # Test 5: /scenario endpoint
    tests_total += 1
    if test_endpoint(
        "POST",
        urljoin(base_url, "/scenario"),
        data={
            "site_id": site_id,
            "rainfall_fraction": 0.8,
            "include_intervention": True,
        },
        description="Run rainfall scenario",
    ):
        tests_passed += 1

    # Test 6: /recommendation endpoint
    tests_total += 1
    if test_endpoint(
        "POST",
        urljoin(base_url, "/recommendation"),
        data={"site_id": site_id},
        description="Get recommendations for site",
    ):
        tests_passed += 1

    # Test 7: /participatory/observe/text endpoint
    tests_total += 1
    observation_text = (
        f"Test observation {uuid.uuid4()} - Water level seems lower than usual"
    )
    if test_endpoint(
        "POST",
        urljoin(base_url, "/participatory/observe/text"),
        data={
            "text": observation_text,
            "observer_id": "+1234567890",
            "observer_name": "Test Observer",
            "language_code": "en-IN",
        },
        description="Submit text observation",
    ):
        tests_passed += 1

    # Test 8: /participatory/leaderboard endpoint
    tests_total += 1
    if test_endpoint(
        "GET",
        urljoin(base_url, "/participatory/leaderboard"),
        params={"limit": 5},
        description="Get leaderboard",
    ):
        tests_passed += 1

    # Test 9: /pathways/generate endpoint
    tests_total += 1
    if test_endpoint(
        "POST",
        urljoin(base_url, "/pathways/generate"),
        data={
            "site_id": site_id,
            "ssp_scenario": "SSP2-4.5",
            "base_rainfall_fraction": 1.0,
        },
        description="Generate adaptation pathway",
    ):
        tests_passed += 1

    # Test 10: /pathways/compare endpoint
    tests_total += 1
    if test_endpoint(
        "POST",
        urljoin(base_url, "/pathways/compare"),
        data={
            "site_id": site_id,
            "scenarios": "SSP1-2.6,SSP2-4.5",
            "base_rainfall_fraction": 1.0,
        },
        description="Compare pathways",
    ):
        tests_passed += 1

    # Test 11: /report endpoint
    tests_total += 1
    if test_endpoint(
        "POST",
        urljoin(base_url, "/report"),
        data={
            "site_ids": f"{site_id},site_002"
            if site_id != "site_002"
            else f"{site_id},site_003"
        },
        description="Generate report for multiple sites",
    ):
        tests_passed += 1

    # Test 12: /dpr/generate endpoint (should return presigned URL)
    tests_total += 1
    print("\nTesting: DPR generation")
    print(f"  POST {urljoin(base_url, '/dpr/generate')}")
    try:
        resp = requests.post(
            urljoin(base_url, "/dpr/generate"),
            data={
                "site_ids": site_id,
                "project_name": "Smoke Test Project",
                "include_pdf": "false",
            },
            timeout=30,
        )
        print(f"  Status: {resp.status_code} (expected 200)")

        if resp.status_code == 200:
            data = resp.json()
            if data.get("presigned_url"):
                print("  SUCCESS: Received presigned URL for DPR download")
                # Optionally test downloading the ZIP (commented out to avoid bandwidth usage in smoke test)
                # download_resp = requests.get(data["presigned_url"], timeout=30)
                # if download_resp.status_code == 200 and download_resp.headers.get('content-type') == 'application/zip':
                #     print(f"  SUCCESS: Downloaded DPR ZIP ({len(download_resp.content)} bytes)")
                #     tests_passed += 1
                # else:
                #     print(f"  WARNING: Could not verify DPR download")
                tests_passed += 1  # Count as passed if we got the presigned URL
            else:
                print("  ERROR: Missing presigned_url in response")
                print(f"  Response: {json.dumps(data, indent=2)[:500]}")
        else:
            print("  ERROR: Unexpected status code")
            print(f"  Response: {resp.text[:500]}")
    except Exception as e:  # noqa: BLE001
        print(f"  ERROR: Request failed: {e}")

    # Test 13: /dpr/schemes endpoint
    tests_total += 1
    if test_endpoint(
        "GET", urljoin(base_url, "/dpr/schemes"), description="Get DPR scheme mapping"
    ):
        tests_passed += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"SMOKE TEST RESULTS: {tests_passed}/{tests_total} tests passed")
    if tests_passed == tests_total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {tests_total - tests_passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
