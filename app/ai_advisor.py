"""
AI Design Advisor for CircuitMind.

Integrates with Anthropic Claude API to provide natural-language
design guidance, optimization tips, and potential issue detection
for analog circuit designs — mirroring the AI-based automation
approach described in Fraunhofer IIS Intelligent IP project.

Falls back to rule-based advice when API key is not available.
"""

import os
from app.models import CircuitParameters, AnalysisResult, AIAdvice, CircuitType

try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False


def get_ai_advice(params: CircuitParameters, analysis: AnalysisResult) -> AIAdvice:
    """
    Generate AI-powered design advice for the given circuit.
    Uses Claude API if available, otherwise falls back to rule-based engine.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if _ANTHROPIC_AVAILABLE and api_key:
        return _claude_advice(params, analysis, api_key)
    else:
        return _rule_based_advice(params, analysis)


def _claude_advice(
    params: CircuitParameters,
    analysis: AnalysisResult,
    api_key: str
) -> AIAdvice:
    """Call Claude API for natural-language circuit design guidance."""
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are an expert analog circuit design engineer.
Analyze this circuit and provide concise, actionable advice.

Circuit Type: {analysis.circuit_type}
Resistance: {params.resistance} Ω
Capacitance: {params.capacitance} F
Inductance: {params.inductance} H
Operating Frequency: {params.frequency} Hz
Analysis Summary: {analysis.summary}
Cutoff Frequency: {analysis.cutoff_frequency_hz} Hz
Quality Factor: {analysis.quality_factor}
Gain: {analysis.gain_db} dB

Provide:
1. A brief parameter summary (1-2 sentences)
2. Three specific design recommendations
3. Two potential issues or risks to watch out for
4. Two optimization tips for better performance

Be specific and technical. Mention component tolerances, parasitic effects, and real-world concerns."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text

    # Parse sections from Claude's response
    lines = raw.strip().split("\n")
    sections = {"summary": [], "rec": [], "issues": [], "tips": []}
    current = "summary"

    for line in lines:
        l = line.lower()
        if "recommendation" in l or "suggest" in l:
            current = "rec"
        elif "issue" in l or "risk" in l or "watch" in l:
            current = "issues"
        elif "optim" in l or "tip" in l or "improve" in l:
            current = "tips"
        elif line.strip():
            sections[current].append(line.strip())

    return AIAdvice(
        circuit_type=analysis.circuit_type,
        parameters_summary="\n".join(sections["summary"]) or raw[:200],
        recommendations="\n".join(sections["rec"]) or "See full analysis above.",
        potential_issues="\n".join(sections["issues"]) or "Review component tolerances.",
        optimization_tips="\n".join(sections["tips"]) or "Consider tighter tolerance components."
    )


def _rule_based_advice(params: CircuitParameters, analysis: AnalysisResult) -> AIAdvice:
    """
    Offline rule-based design advisor. Applies engineering heuristics
    for common circuit issues. Used when Claude API is unavailable.
    """
    ct = params.circuit_type
    R = params.resistance
    C = params.capacitance
    L = params.inductance
    Q = analysis.quality_factor

    # Parameter summary
    summary = analysis.summary

    # Recommendations
    recs = []
    if R > 100_000:
        recs.append("⚠️ High resistance (>100kΩ): susceptible to noise pickup. "
                    "Consider shielding or reducing R with proportional C adjustment.")
    elif R < 10:
        recs.append("⚠️ Very low resistance (<10Ω): high current draw. "
                    "Verify power ratings of all components.")
    else:
        recs.append("✅ Resistance in good practical range (10Ω–100kΩ).")

    if C and C < 1e-12:
        recs.append("⚠️ Extremely small capacitance — parasitic capacitance may dominate. "
                    "Consider layout carefully on PCB.")
    elif C and C > 1e-3:
        recs.append("⚠️ Large capacitance — use electrolytic cap; mind polarity and ESR.")

    if ct in (CircuitType.RC_LOW_PASS, CircuitType.RC_HIGH_PASS):
        recs.append("Use 1% tolerance components for precise cutoff frequency control.")

    # Issues
    issues = []
    if ct in (CircuitType.RLC_BAND_PASS, CircuitType.RLC_BAND_STOP):
        if Q and Q > 10:
            issues.append(f"High Q ({Q:.1f}) means narrow bandwidth — very sensitive to "
                          "component tolerances. Use precision (0.1%) L and C.")
        elif Q and Q < 0.5:
            issues.append(f"Low Q ({Q:.1f}) — overdamped. Band-pass behavior will be broad "
                          "and poorly defined. Consider increasing L/C ratio.")
        issues.append("Inductor parasitic resistance (DCR) will reduce effective Q at high frequencies.")

    if analysis.cutoff_frequency_hz and analysis.cutoff_frequency_hz > 1e6:
        issues.append("At MHz frequencies: lead inductance and PCB trace impedance become significant. "
                      "Use SMD components and minimise trace lengths.")

    if not issues:
        issues.append("No critical issues detected. Verify component datasheets for temperature coefficients.")

    # Optimization tips
    tips = [
        "Buffer the output with an op-amp voltage follower to prevent load-dependent frequency shift.",
        "For production designs, run Monte Carlo tolerance analysis on ±5% component variations."
    ]
    if ct in (CircuitType.RC_LOW_PASS, CircuitType.RC_HIGH_PASS) and C:
        tips.append(f"Use NP0/C0G ceramic capacitors for stable fc across temperature — "
                    f"avoid Y5V/Z5U which drift ±80%.")

    return AIAdvice(
        circuit_type=analysis.circuit_type,
        parameters_summary=summary,
        recommendations="\n".join(f"• {r}" for r in recs),
        potential_issues="\n".join(f"• {i}" for i in issues),
        optimization_tips="\n".join(f"• {t}" for t in tips)
    )
