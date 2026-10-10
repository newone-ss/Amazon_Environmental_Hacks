"""
Integration tests for FastAPI REST API endpoints.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


class TestApiEndpoints:
    def test_get_meta(self) -> None:
        response = client.get("/meta")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "0.2.0"
        assert "Odisha" in data["aoi_name"]
        assert data["total_villages"] == 13
        assert "supported_states" in data
        assert "Odisha" in data["supported_states"]
        assert "Madhya Pradesh" in data["supported_states"]
        assert "Jharkhand" in data["supported_states"]
        assert "scoring_weights_hash" in data

    def test_get_villages(self) -> None:
        response = client.get("/villages")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 13
        village_names = [v["name"] for v in data]
        assert "Laxmipur" in village_names
        assert "Kotpad Town" in village_names
        assert "Bichhiya" in village_names
        assert "Torpa" in village_names

    def test_get_villages_filter_by_state(self) -> None:
        # Filter by Odisha
        resp_od = client.get("/villages?state=Odisha")
        assert resp_od.status_code == 200
        data_od = resp_od.json()
        assert len(data_od) == 5
        assert all(v["state"] == "Odisha" for v in data_od)

        # Filter by Madhya Pradesh
        resp_mp = client.get("/villages?state=Madhya Pradesh")
        assert resp_mp.status_code == 200
        data_mp = resp_mp.json()
        assert len(data_mp) == 4
        assert all(v["state"] == "Madhya Pradesh" for v in data_mp)

        # Filter by Jharkhand
        resp_jh = client.get("/villages?state=Jharkhand")
        assert resp_jh.status_code == 200
        data_jh = resp_jh.json()
        assert len(data_jh) == 4
        assert all(v["state"] == "Jharkhand" for v in data_jh)

    def test_get_site_madhya_pradesh(self) -> None:
        # Bichhiya, Mandla (Safe site)
        response = client.get("/sites/site_mp_001")
        assert response.status_code == 200
        data = response.json()
        assert data["village"]["state"] == "Madhya Pradesh"
        assert data["safety"]["status"] == "SAFE"
        assert len(data["recommendations"]) > 0

    def test_get_site_jharkhand(self) -> None:
        # Torpa, Khunti (Safe site)
        response = client.get("/sites/site_jh_001")
        assert response.status_code == 200
        data = response.json()
        assert data["village"]["state"] == "Jharkhand"
        assert data["safety"]["status"] == "SAFE"
        assert len(data["recommendations"]) > 0

    def test_get_site_valid(self) -> None:
        response = client.get("/sites/site_001")
        assert response.status_code == 200
        data = response.json()
        assert data["village"]["id"] == "site_001"
        assert len(data["scores"]) == 3
        assert data["safety"]["status"] == "SAFE"
        assert len(data["recommendations"]) > 0

    def test_get_site_vetoed(self) -> None:
        response = client.get("/sites/site_002")
        assert response.status_code == 200
        data = response.json()
        assert data["safety"]["status"] == "REJECTED"
        assert "SLOPE_STEEP" in data["safety"]["rule_ids"]
        assert len(data["recommendations"]) == 0

    def test_get_site_not_found(self) -> None:
        response = client.get("/sites/invalid_site_xyz")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_post_scenario(self) -> None:
        payload = {
            "site_id": "site_001",
            "rainfall_fraction": 0.8,
            "include_intervention": "check_dam",
        }
        response = client.post("/scenario", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["site_id"] == "site_001"
        assert data["rainfall_mm_adjusted"] == 1120.0
        assert data["intervention_applied"] == "check_dam"

    def test_post_recommendation(self) -> None:
        payload = {"site_id": "site_001"}
        response = client.post("/recommendation", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_observations_crud(self) -> None:
        create_payload = {
            "site_id": "site_001",
            "observer_name": "Test Geologist",
            "observation_type": "spring_flow",
            "value": 3.4,
            "unit": "litres_per_second",
            "notes": "Post-monsoon measurement",
            "photo_filename": "test_spring.jpg",
        }
        create_resp = client.post("/observations", json=create_payload)
        assert create_resp.status_code == 201
        created_data = create_resp.json()
        assert created_data["observation_id"].startswith("obs_")
        assert created_data["value"] == 3.4
        assert "photo_url" in created_data

        # List observations filtered by site_id
        list_resp = client.get("/observations?site_id=site_001")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert any(
            o["observation_id"] == created_data["observation_id"] for o in list_data
        )

    def test_post_report(self) -> None:
        payload = {
            "site_ids": ["site_001", "site_002"],
            "include_scenario": True,
            "rainfall_fraction": 0.85,
        }
        response = client.post("/report", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["site_count"] == 2
        assert data["format"] == "html"
        assert data["download_url"].startswith("/reports/")

        # Verify that the generated report HTML is accessible
        filename = data["download_url"].replace("/reports/", "")
        get_rpt = client.get(f"/reports/{filename}")
        assert get_rpt.status_code == 200
        assert "Bhujal: Watershed Planning Action Dossier" in get_rpt.text
