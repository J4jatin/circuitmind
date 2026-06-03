"""
Pydantic models for CircuitMind API.
Defines circuit types, parameters, and response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class CircuitType(str, Enum):
    RC_LOW_PASS = "rc_low_pass"
    RC_HIGH_PASS = "rc_high_pass"
    RL_LOW_PASS = "rl_low_pass"
    RL_HIGH_PASS = "rl_high_pass"
    RLC_BAND_PASS = "rlc_band_pass"
    RLC_BAND_STOP = "rlc_band_stop"


class CircuitParameters(BaseModel):
    circuit_type: CircuitType
    resistance: float = Field(..., gt=0, description="Resistance in Ohms")
    capacitance: Optional[float] = Field(None, gt=0, description="Capacitance in Farads")
    inductance: Optional[float] = Field(None, gt=0, description="Inductance in Henrys")
    frequency: Optional[float] = Field(None, gt=0, description="Operating frequency in Hz")

    class Config:
        json_schema_extra = {
            "example": {
                "circuit_type": "rc_low_pass",
                "resistance": 1000,
                "capacitance": 1e-6,
                "frequency": 1000
            }
        }


class DesignSpec(BaseModel):
    circuit_type: CircuitType
    target_cutoff_frequency: float = Field(..., gt=0, description="Desired cutoff frequency in Hz")
    preferred_resistance: Optional[float] = Field(None, gt=0, description="Preferred resistance value in Ohms")
    preferred_capacitance: Optional[float] = Field(None, gt=0, description="Preferred capacitance in Farads")

    class Config:
        json_schema_extra = {
            "example": {
                "circuit_type": "rc_low_pass",
                "target_cutoff_frequency": 1000,
                "preferred_resistance": 1000
            }
        }


class AnalysisResult(BaseModel):
    circuit_type: str
    cutoff_frequency_hz: Optional[float]
    time_constant_s: Optional[float]
    impedance_at_frequency_ohm: Optional[float]
    phase_shift_deg: Optional[float]
    quality_factor: Optional[float]
    resonant_frequency_hz: Optional[float]
    bandwidth_hz: Optional[float]
    gain_db: Optional[float]
    summary: str


class GeneratedDesign(BaseModel):
    circuit_type: str
    target_cutoff_hz: float
    recommended_resistance_ohm: float
    recommended_capacitance_f: Optional[float]
    recommended_inductance_h: Optional[float]
    achieved_cutoff_hz: float
    design_notes: str


class AIAdvice(BaseModel):
    circuit_type: str
    parameters_summary: str
    recommendations: str
    potential_issues: str
    optimization_tips: str
