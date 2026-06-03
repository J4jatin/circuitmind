"""
Tests for circuit analysis engine.
Validates mathematical correctness of all circuit topology analyzers.
"""

import math
import pytest
from app.models import CircuitParameters, CircuitType
from app.analyzer import analyze_circuit


# ── RC Low-Pass Tests ─────────────────────────────────────────────────────────

class TestRCLowPass:

    def _params(self, R=1000, C=1e-6, f=None):
        return CircuitParameters(
            circuit_type=CircuitType.RC_LOW_PASS,
            resistance=R, capacitance=C, frequency=f
        )

    def test_cutoff_frequency_formula(self):
        """fc = 1 / (2π·R·C)"""
        result = analyze_circuit(self._params(R=1000, C=1e-6))
        expected_fc = 1 / (2 * math.pi * 1000 * 1e-6)
        assert abs(result.cutoff_frequency_hz - expected_fc) < 0.01

    def test_time_constant(self):
        """τ = R·C"""
        result = analyze_circuit(self._params(R=1000, C=1e-6))
        assert abs(result.time_constant_s - 1e-3) < 1e-9

    def test_gain_at_cutoff_is_minus_3db(self):
        """At f = fc, gain should be -3 dB (≈ -3.0103)"""
        fc = 1 / (2 * math.pi * 1000 * 1e-6)
        result = analyze_circuit(self._params(R=1000, C=1e-6, f=fc))
        assert result.gain_db is not None
        assert abs(result.gain_db - (-3.0103)) < 0.01

    def test_gain_well_below_cutoff_is_near_zero_db(self):
        """At f << fc, gain ≈ 0 dB"""
        fc = 1 / (2 * math.pi * 1000 * 1e-6)
        result = analyze_circuit(self._params(R=1000, C=1e-6, f=fc / 100))
        assert result.gain_db > -1.0  # nearly 0 dB

    def test_missing_capacitance_raises(self):
        with pytest.raises(ValueError, match="Capacitance required"):
            analyze_circuit(CircuitParameters(
                circuit_type=CircuitType.RC_LOW_PASS,
                resistance=1000, capacitance=None
            ))

    def test_bandwidth_equals_cutoff(self):
        result = analyze_circuit(self._params())
        assert result.bandwidth_hz == result.cutoff_frequency_hz


# ── RC High-Pass Tests ────────────────────────────────────────────────────────

class TestRCHighPass:

    def _params(self, R=1000, C=1e-6, f=None):
        return CircuitParameters(
            circuit_type=CircuitType.RC_HIGH_PASS,
            resistance=R, capacitance=C, frequency=f
        )

    def test_cutoff_frequency_same_as_low_pass(self):
        """Same R and C → same fc regardless of HP/LP topology"""
        lp = analyze_circuit(CircuitParameters(
            circuit_type=CircuitType.RC_LOW_PASS, resistance=1000, capacitance=1e-6))
        hp = analyze_circuit(self._params(R=1000, C=1e-6))
        assert abs(lp.cutoff_frequency_hz - hp.cutoff_frequency_hz) < 0.001

    def test_gain_at_cutoff_is_minus_3db(self):
        fc = 1 / (2 * math.pi * 1000 * 1e-6)
        result = analyze_circuit(self._params(f=fc))
        assert result.gain_db is not None
        assert abs(result.gain_db - (-3.0103)) < 0.05


# ── RL Low-Pass Tests ─────────────────────────────────────────────────────────

class TestRLLowPass:

    def _params(self, R=1000, L=0.1, f=None):
        return CircuitParameters(
            circuit_type=CircuitType.RL_LOW_PASS,
            resistance=R, inductance=L, frequency=f
        )

    def test_cutoff_frequency_formula(self):
        """fc = R / (2π·L)"""
        result = analyze_circuit(self._params(R=1000, L=0.1))
        expected_fc = 1000 / (2 * math.pi * 0.1)
        assert abs(result.cutoff_frequency_hz - expected_fc) < 0.1

    def test_time_constant(self):
        """τ = L/R"""
        result = analyze_circuit(self._params(R=1000, L=1.0))
        assert abs(result.time_constant_s - 1e-3) < 1e-9

    def test_missing_inductance_raises(self):
        with pytest.raises(ValueError, match="Inductance required"):
            analyze_circuit(CircuitParameters(
                circuit_type=CircuitType.RL_LOW_PASS,
                resistance=1000, inductance=None
            ))


# ── RLC Band-Pass Tests ───────────────────────────────────────────────────────

class TestRLCBandPass:

    def _params(self, R=100, L=1e-3, C=1e-6, f=None):
        return CircuitParameters(
            circuit_type=CircuitType.RLC_BAND_PASS,
            resistance=R, inductance=L, capacitance=C, frequency=f
        )

    def test_resonant_frequency_formula(self):
        """f0 = 1 / (2π·√(LC))"""
        L, C = 1e-3, 1e-6
        result = analyze_circuit(self._params(L=L, C=C))
        expected_f0 = 1 / (2 * math.pi * math.sqrt(L * C))
        assert abs(result.resonant_frequency_hz - expected_f0) < 0.1

    def test_quality_factor(self):
        """Q = (1/R)·√(L/C)"""
        R, L, C = 100, 1e-3, 1e-6
        result = analyze_circuit(self._params(R=R, L=L, C=C))
        expected_Q = (1 / R) * math.sqrt(L / C)
        assert abs(result.quality_factor - expected_Q) < 0.001

    def test_bandwidth_equals_f0_over_Q(self):
        """BW = R / (2π·L) — derived directly from component values"""
        R, L, C = 100, 1e-3, 1e-6
        result = analyze_circuit(self._params(R=R, L=L, C=C))
        # BW = R/L / (2π) for series RLC — compute from source values, not rounded stored values
        f0 = 1 / (2 * math.pi * math.sqrt(L * C))
        Q = (1 / R) * math.sqrt(L / C)
        expected_bw = f0 / Q
        assert abs(result.bandwidth_hz - expected_bw) < 1.0  # within 1 Hz

    def test_missing_L_and_C_raises(self):
        with pytest.raises(ValueError):
            analyze_circuit(CircuitParameters(
                circuit_type=CircuitType.RLC_BAND_PASS,
                resistance=100, inductance=None, capacitance=None
            ))


# ── RLC Band-Stop Tests ───────────────────────────────────────────────────────

class TestRLCBandStop:

    def _params(self, R=100, L=1e-3, C=1e-6, f=None):
        return CircuitParameters(
            circuit_type=CircuitType.RLC_BAND_STOP,
            resistance=R, inductance=L, capacitance=C, frequency=f
        )

    def test_resonant_frequency(self):
        L, C = 1e-3, 1e-6
        result = analyze_circuit(self._params(L=L, C=C))
        expected_f0 = 1 / (2 * math.pi * math.sqrt(L * C))
        assert abs(result.resonant_frequency_hz - expected_f0) < 0.1

    def test_q_factor_positive(self):
        result = analyze_circuit(self._params())
    