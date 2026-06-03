"""
CircuitMind — FastAPI REST API

Endpoints:
  POST /analyze      — analyze circuit parameters → AnalysisResult
  POST /generate     — generate component values from spec → GeneratedDesign
  POST /advise       — get AI-powered design advice → AIAdvice
  GET  /health       — health check
  GET  /circuit-types — list supported circuit types

Run locally:
  uvicorn app.main:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    CircuitParameters, DesignSpec,
    AnalysisResult, GeneratedDesign, AIAdvice, CircuitType
)
from app.analyzer import analyze_circuit
from app.generator import generate_design
from app.ai_advisor import get_ai_advice

app = FastAPI(
    title="CircuitMind EDA API",
    description=(
        "AI-powered EDA design automation tool for analog integrated circuit design. "
        "Provides circuit analysis, component generation, and AI-driven design advice. "
        "Built to demonstrate EDA automation concepts aligned with Fraunhofer IIS "
        "Mixed-Signal Automation research (Intelligent IP project)."
    ),
    version="1.0.0",
    contact={
        "name": "Jattin Shah",
        "email": "jattinshahgli@gmail.com"
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health_check():
    """Returns API health status."""
    return {"status": "ok", "service": "CircuitMind EDA API", "version": "1.0.0"}


@app.get("/circuit-types", tags=["System"])
def list_circuit_types():
    """Returns all supported circuit topologies."""
    return {
        "circuit_types": [ct.value for ct in CircuitType],
        "descriptions": {
            "rc_low_pass": "RC Low-Pass Filter — passes low frequencies, attenuates high",
            "rc_high_pass": "RC High-Pass Filter — passes high frequencies, attenuates low",
            "rl_low_pass": "RL Low-Pass Filter — inductor-based low-pass",
            "rl_high_pass": "RL High-Pass Filter — inductor-based high-pass",
            "rlc_band_pass": "RLC Band-Pass Filter — passes band around resonant frequency",
            "rlc_band_stop": "RLC Band-Stop (Notch) Filter — rejects band around resonant frequency",
        }
    }


@app.post("/analyze", response_model=AnalysisResult, tags=["Analysis"])
def analyze(params: CircuitParameters):
    """
    Analyze circuit parameters and return key electrical characteristics:
    cutoff frequency, time constant, impedance, phase shift, Q-factor, bandwidth.
    """
    try:
        return analyze_circuit(params)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/generate", response_model=GeneratedDesign, tags=["Generator"])
def generate(spec: DesignSpec):
    """
    Generate optimal E24-standard component values for a given design specification.
    Implements the circuit generator approach used in EDA automation research.
    """
    try:
        return generate_design(spec)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/advise", response_model=AIAdvice, tags=["AI Advisor"])
def advise(params: CircuitParameters):
    """
    Get AI-powered design advice for the given circuit.
    Uses Claude API (if ANTHROPIC_API_KEY set) or falls back to rule-based advisor.
    Returns recommendations, potential issues, and optimization tips.
    """
    try:
        analysis = analyze_circuit(params)
        return get_ai_advice(params, analysis)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
