"""
Tests for circuit parameter generator.
Validates E24 value selection and design accuracy.
"""

import math
import pytest
from app.models import DesignSpec, CircuitType
from app.generator import generate_design, _nearest_e24, _format_val


class TestE24Selection:

    def test_nearest_e24_returns_positive(self):
        assert _nearest_e24(1000) > 0

    def test_nearest_e24_for_1k_ohm(self):
        """1000 Ω is an exact E24 value"""
        assert _nearest_e24(1000) == pytest.approx(1000, rel=0.01)

    def test_nearest_e24_for_1uf(self):
        """1μF is an exact E24 value"""
        assert _nearest_e24(1e-6) == pytest.approx(1e-6, rel=0.01)

    def test_nearest_e24_invalid_raises(self):
        with pytest.raises(ValueError):
            _nearest_e24(-1)

    def test_format_val_kilo(self):
        assert "k" in _format_val(10000)

    def test_format_val_micro(self):
        assert "μ" in _format_val(1e-6)


class TestRCGenerator:

    def test_rc_lowpass_achieves_target_within_20_percent(self):
        spec = DesignSpec(
            circuit_type=CircuitType.RC_LOW_PASS,
            target_cutoff_frequency=1000.0
        )
        design = generate_design(spec)
        error = abs(design.achieved_cutoff_hz - 1000) / 1000
        assert error < 0.20, f"Error {error:.1%} exceeds 20%"

    def test_rc_highpass_returns_capacitance(self):
        spec = DesignSpec(
            circuit_type=CircuitType.RC_HIGH_PASS,
            target_cutoff_frequency=5000.0,
            preferred_resistance=10000
        )
        design = generate_design(spec)
        assert design.recommended_capacitance_f is not None
        assert design.recommended_capacitance_f > 0

    def test_rc_preferred_resistance_is_used(self):
        spec = DesignSpec(
            circuit_type=CircuitType.RC_LOW_PASS,
            target_cutoff_frequency=1000.0,
            preferred_resistance=4700.0
        )
        design = generate_design(spec)
        # Should pick E24 value near 4700
        assert 4000 < design.recommended_resistance_ohm < 6000

    def test_rc_no_inductance_in_output(self):
        spec = DesignSpec(
            circuit_type=CircuitType.RC_LOW_PASS,
            target_cutoff_frequency=1000.0
        )
        design = generate_design(spec)
        assert design.recommended_inductance_h is None


class TestRLGenerator:

    def test_rl_lowpass_achieves_target(self):
        spec = DesignSpec(
            circuit_type=CircuitType.RL_LOW_PASS,
            target_cutoff_frequency=10000.0,
            preferred_resistance=1000
        )
        design = generate_design(spec)
        error = abs(design.achieved_cutoff_hz - 10000) / 10000
        assert error < 0.25

    def test_rl_returns_inductance(self):
        spec = DesignSpec(
            circuit_type=CircuitType.RL_LOW_PASS,
            target_cutoff_frequency=1000.0
        )
        design = generate_design(spec)
        assert design.recommended_inductance_h is not None


class TestRLCGenerator:

    def test_rlc_bandpass_resonant_frequency_close(self):
        spec = DesignSpec(
            circuit_type=CircuitType.RLC_BAND_PASS,
            target_cutoff_frequency=1000.0,
            preferred_resistance=100
        )
        design = generate_design(spec)
        error = abs(design.achieved_cutoff_hz - 1000) / 1000
        assert error < 0.30  # E24 rounding allows up to 30% on RLC

    def test_rlc_returns_both_l_and_c(self):
        spec = DesignSpec(
            circuit_type=CircuitType.RLC_BAND_PASS,
            target_cutoff_frequency=5000.0
        )
        design = generate_design(spec)
        assert design.recommended_inductance_h is not None
        assert design.recommended_capacitance_f is not None

    def test_design_notes_not_empty(self):
        spec = DesignSpec(
            circuit_type=CircuitType.RC_LOW_PASS,
            target_cutoff_frequency=1000.0
        )
        design = generate_design(spec)
        assert len(design.design_notes) > 20
