"""
CircuitMind — Streamlit GUI Dashboard

Interactive EDA design automation interface with:
- Circuit parameter input
- Real-time frequency response visualization
- Component generation wizard
- AI design advisor panel

Run: streamlit run gui/dashboard.py
"""

import math
import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import numpy as np

from app.models import CircuitParameters, DesignSpec, CircuitType
from app.analyzer import analyze_circuit
from app.generator import generate_design
from app.ai_advisor import get_ai_advice

# ── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CircuitMind EDA",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚡ CircuitMind — EDA Design Automation")
st.markdown(
    "_AI-powered analog circuit analysis and component generation. "
    "Inspired by Fraunhofer IIS Intelligent IP circuit generator research._"
)

# ── Sidebar: Circuit Parameters ───────────────────────────────────────────────

st.sidebar.header("🔧 Circuit Parameters")

circuit_type = st.sidebar.selectbox(
    "Circuit Topology",
    options=[ct.value for ct in CircuitType],
    format_func=lambda x: {
        "rc_low_pass":   "RC Low-Pass Filter",
        "rc_high_pass":  "RC High-Pass Filter",
        "rl_low_pass":   "RL Low-Pass Filter",
        "rl_high_pass":  "RL High-Pass Filter",
        "rlc_band_pass": "RLC Band-Pass Filter",
        "rlc_band_stop": "RLC Band-Stop (Notch)",
    }[x]
)

resistance = st.sidebar.number_input(
    "Resistance (Ω)", min_value=1.0, max_value=10_000_000.0,
    value=1000.0, step=100.0, format="%.1f"
)

needs_cap = circuit_type.startswith("rc") or circuit_type.startswith("rlc")
needs_ind = circuit_type.startswith("rl") or circuit_type.startswith("rlc")

capacitance = None
inductance = None

if needs_cap:
    cap_exp = st.sidebar.slider("Capacitance exponent (10^x F)", -12, -3, -6)
    cap_mantissa = st.sidebar.number_input("Capacitance mantissa", 0.1, 9.9, 1.0, 0.1)
    capacitance = cap_mantissa * (10 ** cap_exp)
    st.sidebar.markdown(f"**C = {capacitance:.2e} F**")

if needs_ind:
    ind_exp = st.sidebar.slider("Inductance exponent (10^x H)", -6, 0, -3)
    ind_mantissa = st.sidebar.number_input("Inductance mantissa", 0.1, 9.9, 1.0, 0.1)
    inductance = ind_mantissa * (10 ** ind_exp)
    st.sidebar.markdown(f"**L = {inductance:.2e} H**")

frequency = st.sidebar.number_input(
    "Operating Frequency (Hz)", min_value=0.1, max_value=1e9,
    value=1000.0, step=100.0
)

analyze_btn = st.sidebar.button("🔍 Analyze Circuit", type="primary", use_container_width=True)

# ── Main Tabs ─────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📊 Analysis", "🎛️ Design Generator", "🤖 AI Advisor"])

# ── Tab 1: Analysis ───────────────────────────────────────────────────────────

with tab1:
    if analyze_btn or True:  # always show on load with defaults
        try:
            params = CircuitParameters(
                circuit_type=CircuitType(circuit_type),
                resistance=resistance,
                capacitance=capacitance,
                inductance=inductance,
                frequency=frequency
            )
            result = analyze_circuit(params)

            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                val = f"{result.cutoff_frequency_hz:.2f} Hz" if result.cutoff_frequency_hz else "N/A"
                st.metric("Cutoff Frequency", val)
            with col2:
                val = f"{result.time_constant_s*1000:.4f} ms" if result.time_constant_s else "N/A"
                st.metric("Time Constant τ", val)
            with col3:
                val = f"{result.quality_factor:.3f}" if result.quality_factor else "N/A"
                st.metric("Quality Factor Q", val)
            with col4:
                val = f"{result.gain_db:.2f} dB" if result.gain_db else "N/A"
                st.metric("Gain at f", val)

            col5, col6 = st.columns(2)
            with col5:
                val = f"{result.phase_shift_deg:.2f}°" if result.phase_shift_deg else "N/A"
                st.metric("Phase Shift", val)
            with col6:
                val = f"{result.bandwidth_hz:.2f} Hz" if result.bandwidth_hz else "N/A"
                st.metric("Bandwidth", val)

            st.info(f"**Summary:** {result.summary}")

            # Frequency response plot
            st.subheader("📈 Frequency Response (Bode Magnitude Plot)")
            freqs = np.logspace(0, 7, 500)  # 1 Hz to 10 MHz

            gains_db = []
            for f_plot in freqs:
                try:
                    p = CircuitParameters(
                        circuit_type=CircuitType(circuit_type),
                        resistance=resistance,
                        capacitance=capacitance,
                        inductance=inductance,
                        frequency=float(f_plot)
                    )
                    r = analyze_circuit(p)
                    gains_db.append(r.gain_db if r.gain_db is not None else -60)
                except Exception:
                    gains_db.append(-60)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=freqs, y=gains_db,
                mode="lines", name="Gain (dB)",
                line=dict(color="#00b4d8", width=2)
            ))
            if result.cutoff_frequency_hz:
                fig.add_vline(
                    x=result.cutoff_frequency_hz,
                    line_dash="dash", line_color="orange",
                    annotation_text=f"fc = {result.cutoff_frequency_hz:.1f} Hz",
                    annotation_position="top right"
                )
            if result.resonant_frequency_hz:
                fig.add_vline(
                    x=result.resonant_frequency_hz,
                    line_dash="dash", line_color="red",
                    annotation_text=f"f0 = {result.resonant_frequency_hz:.1f} Hz",
                    annotation_position="top right"
                )
            fig.add_hline(y=-3, line_dash="dot", line_color="gray",
                          annotation_text="-3 dB")
            fig.update_layout(
                xaxis_type="log",
                xaxis_title="Frequency (Hz)",
                yaxis_title="Gain (dB)",
                template="plotly_dark",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        except ValueError as e:
            st.error(f"Analysis error: {e}")

# ── Tab 2: Design Generator ───────────────────────────────────────────────────

with tab2:
    st.subheader("🎛️ Component Value Generator")
    st.markdown(
        "Enter your desired cutoff/resonant frequency and preferred component values. "
        "The generator selects optimal **E24 standard values** — the same approach used "
        "in EDA circuit generator tools."
    )

    col_a, col_b = st.columns(2)
    with col_a:
        gen_type = st.selectbox("Circuit Type", [ct.value for ct in CircuitType], key="gen_type")
        target_fc = st.number_input("Target Frequency (Hz)", 1.0, 1e9, 1000.0, key="target_fc")
    with col_b:
        pref_r = st.number_input("Preferred Resistance (Ω, optional)", 0.0, 1e7, 1000.0, key="pref_r")
        pref_c = st.number_input("Preferred Capacitance (F, optional, 0=auto)", 0.0, 1.0, 0.0,
                                  format="%.2e", key="pref_c")

    if st.button("⚙️ Generate Design", type="primary"):
        try:
            spec = DesignSpec(
                circuit_type=CircuitType(gen_type),
                target_cutoff_frequency=target_fc,
                preferred_resistance=pref_r if pref_r > 0 else None,
                preferred_capacitance=pref_c if pref_c > 0 else None
            )
            design = generate_design(spec)

            st.success("✅ Design generated using E24 standard values!")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Resistance", f"{design.recommended_resistance_ohm:.0f} Ω")
            with col2:
                if design.recommended_capacitance_f:
                    st.metric("Capacitance", f"{design.recommended_capacitance_f:.2e} F")
            with col3:
                if design.recommended_inductance_h:
                    st.metric("Inductance", f"{design.recommended_inductance_h:.2e} H")

            st.metric("Achieved Frequency", f"{design.achieved_cutoff_hz:.2f} Hz",
                      delta=f"{((design.achieved_cutoff_hz - target_fc)/target_fc*100):+.1f}%")
            st.info(f"**Design Notes:** {design.design_notes}")

        except ValueError as e:
            st.error(f"Generator error: {e}")

# ── Tab 3: AI Advisor ─────────────────────────────────────────────────────────

with tab3:
    st.subheader("🤖 AI Design Advisor")
    st.markdown(
        "Get AI-powered analysis, recommendations, and optimization tips for your circuit. "
        "Uses **Claude API** if `ANTHROPIC_API_KEY` is set, otherwise uses rule-based advisor."
    )

    if st.button("🧠 Get AI Advice", type="primary"):
        try:
            params = CircuitParameters(
                circuit_type=CircuitType(circuit_type),
                resistance=resistance,
                capacitance=capacitance,
                inductance=inductance,
                frequency=frequency
            )
            analysis = analyze_circuit(params)
            advice = get_ai_advice(params, analysis)

            st.markdown("### 📋 Parameter Summary")
            st.write(advice.parameters_summary)

            st.markdown("### ✅ Recommendations")
            st.write(advice.recommendations)

            st.markdown("### ⚠️ Potential Issues")
            st.write(advice.potential_issues)

            st.markdown("### 💡 Optimization Tips")
            st.write(advice.optimization_tips)

        except ValueError as e:
            st.error(f"Error: {e}")

# ── Footer ────────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "CircuitMind | EDA Design Automation | "
    "Built by Jattin Shah · MSc Applied AI, TU Dresden · "
    "Inspired by Fraunhofer IIS Mixed-Signal Automation research"
)
