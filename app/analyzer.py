"""
Circuit Analysis Engine for CircuitMind.

Implements algorithms for computing electrical circuit parameters:
- Cutoff frequencies
- Time constants
- Impedance
- Phase shift
- Quality factor (Q)
- Resonant frequency
- Bandwidth

Designed to mirror the analysis approach used in EDA automation tools
like those developed at Fraunhofer IIS Mixed-Signal Automation group.
"""

import math
from typing import Optional
from app.models import CircuitParameters, AnalysisResult, CircuitType


def analyze_circuit(params: CircuitParameters) -> AnalysisResult:
    """
    Main dispatch function: routes circuit parameters to the correct
    analysis algorithm based on circuit topology.
    """
    ct = params.circuit_type

    if ct == CircuitType.RC_LOW_PASS:
        return _analyze_rc_low_pass(params)
    elif ct == CircuitType.RC_HIGH_PASS:
        return _analyze_rc_high_pass(params)
    elif ct == CircuitType.RL_LOW_PASS:
        return _analyze_rl_low_pass(params)
    elif ct == CircuitType.RL_HIGH_PASS:
        return _analyze_rl_high_pass(params)
    elif ct == CircuitType.RLC_BAND_PASS:
        return _analyze_rlc_band_pass(params)
    elif ct == CircuitType.RLC_BAND_STOP:
        return _analyze_rlc_band_stop(params)
    else:
        raise ValueError(f"Unsupported circuit type: {ct}")


# ── RC Low-Pass ──────────────────────────────────────────────────────────────

def _analyze_rc_low_pass(params: CircuitParameters) -> AnalysisResult:
    R = params.resistance
    C = params.capacitance
    f = params.frequency

    if C is None:
        raise ValueError("Capacitance required for RC circuit")

    tau = R * C                          # time constant
    fc = 1.0 / (2 * math.pi * R * C)    # cutoff frequency

    impedance = phase = gain_db = None
    if f is not None:
        omega = 2 * math.pi * f
        Xc = 1.0 / (omega * C)
        impedance = math.sqrt(R**2 + Xc**2)
        phase = -math.degrees(math.atan(omega * R * C))
        gain = 1.0 / math.sqrt(1 + (f / fc)**2)
        gain_db = 20 * math.log10(gain)

    return AnalysisResult(
        circuit_type="RC Low-Pass Filter",
        cutoff_frequency_hz=round(fc, 4),
        time_constant_s=round(tau, 8),
        impedance_at_frequency_ohm=round(impedance, 4) if impedance else None,
        phase_shift_deg=round(phase, 4) if phase else None,
        quality_factor=None,
        resonant_frequency_hz=None,
        bandwidth_hz=round(fc, 4),
        gain_db=round(gain_db, 4) if gain_db else None,
        summary=(
            f"RC Low-Pass: fc={fc:.2f} Hz, τ={tau*1000:.4f} ms. "
            f"Passes signals below {fc:.2f} Hz with -3dB attenuation at cutoff."
        )
    )


# ── RC High-Pass ─────────────────────────────────────────────────────────────

def _analyze_rc_high_pass(params: CircuitParameters) -> AnalysisResult:
    R = params.resistance
    C = params.capacitance
    f = params.frequency

    if C is None:
        raise ValueError("Capacitance required for RC circuit")

    tau = R * C
    fc = 1.0 / (2 * math.pi * R * C)

    impedance = phase = gain_db = None
    if f is not None:
        omega = 2 * math.pi * f
        Xc = 1.0 / (omega * C)
        impedance = math.sqrt(R**2 + Xc**2)
        phase = math.degrees(math.atan(1.0 / (omega * R * C)))
        gain = (f / fc) / math.sqrt(1 + (f / fc)**2)
        gain_db = 20 * math.log10(gain) if gain > 0 else -float("inf")

    return AnalysisResult(
        circuit_type="RC High-Pass Filter",
        cutoff_frequency_hz=round(fc, 4),
        time_constant_s=round(tau, 8),
        impedance_at_frequency_ohm=round(impedance, 4) if impedance else None,
        phase_shift_deg=round(phase, 4) if phase else None,
        quality_factor=None,
        resonant_frequency_hz=None,
        bandwidth_hz=None,
        gain_db=round(gain_db, 4) if gain_db and gain_db != -float("inf") else None,
        summary=(
            f"RC High-Pass: fc={fc:.2f} Hz, τ={tau*1000:.4f} ms. "
            f"Passes signals above {fc:.2f} Hz."
        )
    )


# ── RL Low-Pass ──────────────────────────────────────────────────────────────

def _analyze_rl_low_pass(params: CircuitParameters) -> AnalysisResult:
    R = params.resistance
    L = params.inductance
    f = params.frequency

    if L is None:
        raise ValueError("Inductance required for RL circuit")

    tau = L / R
    fc = R / (2 * math.pi * L)

    impedance = phase = gain_db = None
    if f is not None:
        omega = 2 * math.pi * f
        XL = omega * L
        impedance = math.sqrt(R**2 + XL**2)
        phase = -math.degrees(math.atan(omega * L / R))
        gain = 1.0 / math.sqrt(1 + (f / fc)**2)
        gain_db = 20 * math.log10(gain)

    return AnalysisResult(
        circuit_type="RL Low-Pass Filter",
        cutoff_frequency_hz=round(fc, 4),
        time_constant_s=round(tau, 8),
        impedance_at_frequency_ohm=round(impedance, 4) if impedance else None,
        phase_shift_deg=round(phase, 4) if phase else None,
        quality_factor=None,
        resonant_frequency_hz=None,
        bandwidth_hz=round(fc, 4),
        gain_db=round(gain_db, 4) if gain_db else None,
        summary=(
            f"RL Low-Pass: fc={fc:.2f} Hz, τ={tau*1000:.4f} ms."
        )
    )


# ── RL High-Pass ─────────────────────────────────────────────────────────────

def _analyze_rl_high_pass(params: CircuitParameters) -> AnalysisResult:
    R = params.resistance
    L = params.inductance
    f = params.frequency

    if L is None:
        raise ValueError("Inductance required for RL circuit")

    tau = L / R
    fc = R / (2 * math.pi * L)

    impedance = phase = gain_db = None
    if f is not None:
        omega = 2 * math.pi * f
        XL = omega * L
        impedance = math.sqrt(R**2 + XL**2)
        phase = math.degrees(math.atan(R / (omega * L)))
        gain = (f / fc) / math.sqrt(1 + (f / fc)**2)
        gain_db = 20 * math.log10(gain) if gain > 0 else None

    return AnalysisResult(
        circuit_type="RL High-Pass Filter",
        cutoff_frequency_hz=round(fc, 4),
        time_constant_s=round(tau, 8),
        impedance_at_frequency_ohm=round(impedance, 4) if impedance else None,
        phase_shift_deg=round(phase, 4) if phase else None,
        quality_factor=None,
        resonant_frequency_hz=None,
        bandwidth_hz=None,
        gain_db=round(gain_db, 4) if gain_db else None,
        summary=(
            f"RL High-Pass: fc={fc:.2f} Hz, τ={tau*1000:.4f} ms."
        )
    )


# ── RLC Band-Pass ─────────────────────────────────────────────────────────────

def _analyze_rlc_band_pass(params: CircuitParameters) -> AnalysisResult:
    R = params.resistance
    L = params.inductance
    C = params.capacitance

    if L is None or C is None:
        raise ValueError("Both inductance and capacitance required for RLC circuit")

    f0 = 1.0 / (2 * math.pi * math.sqrt(L * C))   # resonant frequency
    Q = (1.0 / R) * math.sqrt(L / C)               # quality factor
    BW = f0 / Q                                     # bandwidth

    impedance = phase = gain_db = None
    f = params.frequency
    if f is not None:
        omega = 2 * math.pi * f
        omega0 = 2 * math.pi * f0
        XL = omega * L
        Xc = 1.0 / (omega * C)
        impedance = math.sqrt(R**2 + (XL - Xc)**2)
        phase = math.degrees(math.atan((XL - Xc) / R))
        gain = R / impedance
        gain_db = 20 * math.log10(gain)

    return AnalysisResult(
        circuit_type="RLC Band-Pass Filter",
        cutoff_frequency_hz=None,
        time_constant_s=None,
        impedance_at_frequency_ohm=round(impedance, 4) if impedance else None,
        phase_shift_deg=round(phase, 4) if phase else None,
        quality_factor=round(Q, 4),
        resonant_frequency_hz=round(f0, 4),
        bandwidth_hz=round(BW, 4),
        gain_db=round(gain_db, 4) if gain_db else None,
        summary=(
            f"RLC Band-Pass: f0={f0:.2f} Hz, Q={Q:.4f}, BW={BW:.2f} Hz. "
            f"Passes signals near {f0:.2f} Hz."
        )
    )


# ── RLC Band-Stop ─────────────────────────────────────────────────────────────

def _analyze_rlc_band_stop(params: CircuitParameters) -> AnalysisResult:
    R = params.resistance
    L = params.inductance
    C = params.capacitance

    if L is None or C is None:
        raise ValueError("Both inductance and capacitance required for RLC circuit")

    f0 = 1.0 / (2 * math.pi * math.sqrt(L * C))
    Q = (1.0 / R) * math.sqrt(L / C)
    BW = f0 / Q

    impedance = phase = gain_db = None
    f = params.frequency
    if f is not None:
        omega = 2 * math.pi * f
        XL = omega * L
        Xc = 1.0 / (omega * C)
        Z_lc = abs(XL - Xc)
        impedance = math.sqrt(R**2 + Z_lc**2)
        # For band-stop, gain approaches 1 far from resonance, 0 at resonance
        omega0 = 2 * math.pi * f0
        ratio = f / f0
        gain_num = abs(ratio**2 - 1)
        gain_den = math.sqrt((ratio**2 - 1)**2 + (ratio / Q)**2)
        gain = gain_num / gain_den if gain_den > 0 else 0
        gain_db = 20 * math.log10(gain) if gain > 1e-10 else -100.0
        phase = math.degrees(math.atan((XL - Xc) / R))

    return AnalysisResult(
        circuit_type="RLC Band-Stop (Notch) Filter",
        cutoff_frequency_hz=None,
        time_constant_s=None,
        impedance_at_frequency_ohm=round(impedance, 4) if impedance else None,
        phase_shift_deg=round(phase, 4) if phase else None,
        quality_factor=round(Q, 4),
        resonant_frequency_hz=round(f0, 4),
        bandwidth_hz=round(BW, 4),
        gain_db=round(gain_db, 4) if gain_db else None,
        summary=(
            f"RLC Band-Stop (Notch): f0={f0:.2f} Hz, Q={Q:.4f}, BW={BW:.2f} Hz. "
            f"Rejects signals near {f0:.2f} Hz."
        )
    )
