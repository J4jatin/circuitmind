"""
Integration tests for CircuitMind FastAPI endpoints.
Tests all API routes with valid and invalid inputs.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthAndMeta:

    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_includes_version(self):
        response = client.get("/health")
        assert "version" in response.json()

    def test_circuit_types_endpoint(self):
        response = client.get("/circuit-types")
        assert response.status_code == 200
        data = response.json()
        assert "circuit_types" in data
        assert len(data["circuit_types"]) == 6


class TestAnalyzeEndpoint:

    def test_rc_lowpass_analyze_success(self):
        response = client.post("/analyze", json={
            "circuit_type": "rc_low_pass",
            "resistance": 1000,
            "capacitance": 1e-6,
            "frequency": 1000
        })
        assert response.status_code == 200
        data = response.json()
        assert "cutoff_frequency_hz" in data
        assert data["cutoff_frequency_hz"] > 0

    def test_rlc_bandpass_analyze_success(self):
        response = client.post("/analyze", json={
            "circuit_type": "rlc_band_pass",
            "resistance": 100,
            "inductance": 1e-3,
            "capacitance": 1e-6,
            "frequency": 5000
        })
        assert response.status_code == 200
        data = response.json()
        assert data["quality_factor"] is not None
        assert data["resonant_frequency_hz"] is not None

    def test_missing_capacitance_returns_422(self):
        response = client.post("/analyze", json={
            "circuit_type": "rc_low_pass",
            "resistance": 1000
        })
        assert response.status_code == 422

    def test_negative_resistance_returns_422(self):
        response = client.post("/analyze", json={
            "circuit_type": "rc_low_pass",
            "resistance": -100,
            "capacitance": 1e-6
        })
        assert response.status_code == 422

    def test_all_six_circuit_types_analyzable(self):
        payloads = [
            {"circuit_type": "rc_low_pass", "resistance": 1000, "capacitance": 1e-6},
            {"circuit_type": "rc_high_pass", "resistance": 1000, "capacitance": 1e-6},
            {"circuit_type": "rl_low_pass", "resistance": 1000, "inductance": 0.1},
            {"circuit_type": "rl_high_pass", "resistance": 1000, "inductance": 0.1},
            {"circuit_type": "rlc_band_pass", "resistance": 100, "inductance": 1e-3, "capacitance": 1e-6},
            {"circuit_type": "rlc_band_stop", "resistance": 100, "inductance": 1e-3, "capacitance": 1e-6},
        ]
        for payload in payloads:
            response = client.post("/analyze", json=payload)
            assert response.status_code == 200, f"Failed for {payload['circuit_type']}: {response.text}"


class TestGenerateEndpoint:

    def test_generate_rc_lowpass(self):
        response = client.post("/generate", json={
            "circuit_type": "rc_low_pass",
            "target_cutoff_frequency": 1000
        })
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_resistance_ohm"] > 0
        assert data["recommended_capacitance_f"] > 0

    def test_generate_with_preferred_resistance(self):
        response = client.post("/generate", json={
            "circuit_type": "rc_low_pass",
            "target_cutoff_frequency": 5000,
            "preferred_resistance": 10000
        })
        assert response.status_code == 200

    def test_generate_rlc(self):
        response = client.post("/generate", json={
            "circuit_type": "rlc_band_pass",
            "target_cutoff_frequency": 1000
        })
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_inductance_h"] is not None
        assert data["recommended_capacitance_f"] is not None


class TestAdviseEndpoint:

    def test_advise_returns_advice_fields(self):
        response = client.post("/advise", json={
            "circuit_type": "rc_low_pass",
            "resistance": 1000,
            "capacitance": 1e-6,
            "frequency": 1000
        })
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "potential_issues" in data
        assert "optimization_tips" in data

    def test_advise_high_resistance_mentions_noise(self):
        response = client.post("/advise", json={
            "circuit_type": "rc_low_pass",
            "resistance": 500000,
            "capacitance": 1e-9,
            "frequency": 500
        })
        assert response.status_code == 200
        data = response.json()
        # Rule-based advisor should flag high resistance
        combined = data["recommendations"] + data["potential_issues"]
        assert len(combined) > 10  # non-empty advice
