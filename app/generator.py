"""
Circuit Parameter Generator for CircuitMind.

Given a target specification (e.g. desired cutoff frequency),
this module generates optimal component values using standard
E-series resistor/capacitor values — the same approach used
in automated IC design generators like Intelligent IP.
"""

import math
from typing import Tuple
from app.models import DesignSpec, GeneratedDesign, CircuitType


# Standard E12 component series values (multipliers)
E12_VALUES = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
E24_VALUES = [
    1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
    3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1
]


def _e24_candidates(min_val: float, max_val: float) -> list:
    """Generate all E24 standard values within [min_val, max_val]."""
    candidates = []
    decade = 1e-12  # start at pico scale
    while decade <= 1e6:
        for m in E24_VALUES:
            v = m * decade
            if min_val <= v <= max_val:
                candidates.append(v)
        decade *= 10
    return sorted(candidates)


def _nearest_e24(value: float) -> float:
    """Return the nearest E24 standard value to the given value."""
    if value <= 0:
        raise ValueError("Value must be positive")
    decade = 10 ** math.floor(math.log10(value))
    best = None
    best_err = float("inf")
    for m in E24_VALUES:
        candidate = m * decade
        err = abs(candidate - value) / value
        if err < best_err:
            best_err = err
            best = candidate
    # also check next decade up
    for m in E24_VALUES:
        candidate = m * decade * 10
        err = abs(candidate - value) / value
        if err < best_err:
            best_err = err
            best = candidate
    return best


def generate_design(spec: DesignSpec) -> GeneratedDesign:
    """
    Generate optimal component values for the given design spec.
    Uses E24 standard values to ensure real-world sourcing compatibility.
    """
    ct = spec.circuit_type
    fc = spec.target_cutoff_frequency

    if ct in (CircuitType.RC_LOW_PASS, CircuitType.RC_HIGH_PASS):
        return _generate_rc(spec)
    elif ct in (CircuitType.RL_LOW_PASS, CircuitType.RL_HIGH_PASS):
        return _generate_rl(spec)
    elif ct in (CircuitType.RLC_BAND_PASS, CircuitType.RLC_BAND_STOP):
        return _generate_rlc(spec)
    else:
        raise ValueError(f"Unsupported circuit type: {ct}")


def _generate_rc(spec: DesignSpec) -> GeneratedDesign:
    fc = spec.target_cutoff_frequency

    if spec.preferred_resistance:
        R = _nearest_e24(spec.preferred_resistance)
        C_ideal = 1.0 / (2 * math.pi * fc * R)
        C = _nearest_e24(C_ideal)
    elif spec.preferred_capacitance:
        C = _nearest_e24(spec.preferred_capacitance)
        R_ideal = 1.0 / (2 * math.pi * fc * C)
        R = _nearest_e24(R_ideal)
    else:
        # Default: pick R=10kΩ, compute C
        R = 10000.0
        C_ideal = 1.0 / (2 * math.pi * fc * R)
        C = _nearest_e24(C_ideal)

    achieved_fc = 1.0 / (2 * math.pi * R * C)
    error_pct = abs(achieved_fc - fc) / fc * 100

    notes = (
        f"Using E24 standard values: R={_format_val(R)}Ω, C={_format_val(C)}F. "
        f"Achieved fc={achieved_fc:.2f} Hz ({error_pct:.1f}% error from target {fc} Hz). "
        f"Time constant τ = RC = {R*C*1000:.4f} ms."
    )

    return GeneratedDesign(
        circuit_type=spec.circuit_type.value,
        target_cutoff_hz=fc,
        recommended_resistance_ohm=R,
        recommended_capacitance_f=C,
        recommended_inductance_h=None,
        achieved_cutoff_hz=round(achieved_fc, 4),
        design_notes=notes
    )


def _generate_rl(spec: DesignSpec) -> GeneratedDesign:
    fc = spec.target_cutoff_frequency

    if spec.preferred_resistance:
        R = _nearest_e24(spec.preferred_resistance)
        L_ideal = R / (2 * math.pi * fc)
        L = _nearest_e24(L_ideal)
    else:
        R = 1000.0
        L_ideal = R / (2 * math.pi * fc)
        L = _nearest_e24(L_ideal)

    achieved_fc = R / (2 * math.pi * L)
    error_pct = abs(achieved_fc - fc) / fc * 100

    notes = (
        f"Using E24 standard values: R={_format_val(R)}Ω, L={_format_val(L)}H. "
        f"Achieved fc={achieved_fc:.2f} Hz ({error_pct:.1f}% error). "
        f"Time constant τ = L/R = {(L/R)*1000:.4f} ms."
    )

    return GeneratedDesign(
        circuit_type=spec.circuit_type.value,
        target_cutoff_hz=fc,
        recommended_resistance_ohm=R,
        recommended_capacitance_f=None,
        recommended_inductance_h=L,
        achieved_cutoff_hz=round(achieved_fc, 4),
        design_notes=notes
    )


def _generate_rlc(spec: DesignSpec) -> GeneratedDesign:
    fc = spec.target_cutoff_frequency  # treated as resonant frequency f0
    R = spec.preferred_resistance or 100.0
    R = _nearest_e24(R)

    # Choose L, then compute C for resonance at fc
    L_ideal = R / (2 * math.pi * fc)   # heuristic: Q≈1 starting point
    L = _nearest_e24(L_ideal)
    C_ideal = 1.0 / ((2 * math.pi * fc) ** 2 * L)
    C = _nearest_e24(C_ideal)

    achieved_f0 = 1.0 / (2 * math.pi * math.sqrt(L * C))
    Q = (1.0 / R) * math.sqrt(L / C)
    BW = achieved_f0 / Q
    error_pct = abs(achieved_f0 - fc) / fc * 100

    notes = (
        f"R={_format_val(R)}Ω, L={_format_val(L)}H, C={_format_val(C)}F. "
        f"Resonant f0={achieved_f0:.2f} Hz ({error_pct:.1f}% error), "
        f"Q={Q:.3f}, BW={BW:.2f} Hz."
    )

    return GeneratedDesign(
        circuit_type=spec.circuit_type.value,
        target_cutoff_hz=fc,
        recommended_resistance_ohm=R,
        recommended_capacitance_f=C,
        recommended_inductance_h=L,
        achieved_cutoff_hz=round(achieved_f0, 4),
        design_notes=notes
    )


def _format_val(v: float) -> str:
    """Format component value with SI prefix."""
    if v >= 1e6:
        return f"{v/1e6:.2f}M"
    elif v >= 1e3:
        return f"{v/1e3:.2f}k"
    elif v >= 1:
        return f"{v:.2f}"
    elif v >= 1e-3:
        return f"{v*1e3:.2f}m"
    elif v >= 1e-6:
        return f"{v*1e6:.2f}μ"
    elif v >= 1e-9:
        return f"{v*1e9:.2f}n"
    else:
        return f"{v*1e12:.2f}p"
