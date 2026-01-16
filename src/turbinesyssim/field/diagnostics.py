# -*- coding: utf-8 -*-
"""
TurbineSysSim - Integrated Diagnostics
-------------------------------------

Author: Arildo Yank

Integrated field diagnostics combining:
- Thermodynamic performance
- Acoustic noise
- Mechanical vibration
- Maintenance degradation (fouling / erosion)

This module produces engineering-grade diagnostic conclusions
suitable for operator guidance and technical reports.
"""

from dataclasses import dataclass
from typing import List

from turbinesyssim.acoustics.noise_model import NoiseResults
from turbinesyssim.acoustics.vibration import VibrationResults


@dataclass
class DiagnosticInputs:
    net_power_mw: float
    thermal_efficiency: float
    fouling_percent: float
    erosion_index: float
    noise: NoiseResults
    vibration: VibrationResults


@dataclass
class DiagnosticResult:
    severity: str
    probable_causes: List[str]
    recommended_actions: List[str]


class TurbineDiagnostics:
    """
    Rule-based integrated diagnostic engine.
    Designed to be explainable and defensible.
    """

    def __init__(self, inputs: DiagnosticInputs):
        self.inputs = inputs

    # -------------------------------------------------

    def run(self) -> DiagnosticResult:
        causes = []
        actions = []

        # --- Performance degradation ---
        if self.inputs.thermal_efficiency < 0.30:
            causes.append("Low thermal efficiency")
            actions.append("Inspect compressor and turbine sections")

        if self.inputs.fouling_percent > 10:
            causes.append("Compressor fouling")
            actions.append("Plan online or offline compressor wash")

        if self.inputs.erosion_index > 0.4:
            causes.append("Blade erosion suspected")
            actions.append("Schedule borescope inspection")

        # --- Acoustic indicators ---
        if self.inputs.noise.overall_spl_db > 90:
            causes.append("Abnormally high acoustic emission")
            actions.append("Review operating load and inlet conditions")

        if "tonal" in self.inputs.noise.diagnostic_hint.lower():
            causes.append("Possible blade-pass or shaft-related excitation")
            actions.append("Check rotor balance and blade condition")

        # --- Vibration indicators ---
        if self.inputs.vibration.rms_velocity_mm_s > 7.1:
            causes.append("Excessive vibration (ISO 10816)")
            actions.append("Immediate vibration analysis recommended")

        if "bearing" in self.inputs.vibration.diagnostic_hint.lower():
            causes.append("Bearing degradation")
            actions.append("Inspect lubrication system and bearings")

        if "misalignment" in self.inputs.vibration.diagnostic_hint.lower():
            causes.append("Shaft or coupling misalignment")
            actions.append("Verify alignment during next shutdown")

        # --- Severity assessment ---
        severity = self._assess_severity(causes)

        if not causes:
            causes.append("No abnormal conditions detected")
            actions.append("Continue normal operation and monitoring")

        return DiagnosticResult(
            severity=severity,
            probable_causes=causes,
            recommended_actions=actions,
        )

    # -------------------------------------------------

    @staticmethod
    def _assess_severity(causes: List[str]) -> str:
        if any("Immediate" in c for c in causes):
            return "CRITICAL"
        if len(causes) >= 4:
            return "HIGH"
        if len(causes) >= 2:
            return "MEDIUM"
        return "LOW"