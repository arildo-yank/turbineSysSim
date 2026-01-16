

# -*- coding: utf-8 -*-
"""
TurbineSysSim - Vibration Model
------------------------------

Author: Arildo Yank

System-level vibration model for rotating machinery (gas/steam turbines).
This model is intended for diagnostics, trending, and engineering reasoning.
It is NOT a full rotor-dynamics or FEM model.
"""

from dataclasses import dataclass
import math


@dataclass
class VibrationInputs:
    rpm: float                  # Shaft speed [RPM]
    load_factor: float          # 0.0 – 1.0
    imbalance_level: float      # 0.0 – 1.0
    bearing_wear: float = 0.0   # 0.0 – 1.0
    misalignment: float = 0.0   # 0.0 – 1.0


@dataclass
class VibrationResults:
    rms_velocity_mm_s: float    # ISO 10816 style metric
    peak_acceleration_g: float
    dominant_frequency_hz: float
    diagnostic_hint: str


class TurbineVibrationModel:
    """
    Engineering-oriented vibration model.
    """

    BASE_VELOCITY = 1.2  # mm/s RMS (healthy machine)

    def __init__(self, inputs: VibrationInputs):
        self.inputs = inputs

    # -------------------------------------------------

    def run(self) -> VibrationResults:
        rpm = max(self.inputs.rpm, 1.0)
        load = max(0.0, min(1.0, self.inputs.load_factor))
        imbalance = max(0.0, self.inputs.imbalance_level)
        bearing = max(0.0, self.inputs.bearing_wear)
        misalignment = max(0.0, self.inputs.misalignment)

        # Dominant mechanical frequency (1x RPM)
        freq_hz = rpm / 60.0

        # Velocity contributions
        imbalance_term = 4.0 * imbalance * (rpm / 3000.0)
        bearing_term = 3.0 * bearing
        misalignment_term = 2.5 * misalignment
        load_term = 1.5 * load

        rms_velocity = (
            self.BASE_VELOCITY
            + imbalance_term
            + bearing_term
            + misalignment_term
            + load_term
        )

        # Peak acceleration (simplified conversion)
        peak_accel = 0.1 * rms_velocity * freq_hz / 9.81

        diagnostic = self._diagnostic(
            imbalance, bearing, misalignment, rms_velocity
        )

        return VibrationResults(
            rms_velocity_mm_s=round(rms_velocity, 2),
            peak_acceleration_g=round(peak_accel, 3),
            dominant_frequency_hz=round(freq_hz, 1),
            diagnostic_hint=diagnostic,
        )

    # -------------------------------------------------

    @staticmethod
    def _diagnostic(imbalance, bearing, misalignment, rms):
        if rms > 7.1:
            return "Severe vibration – immediate inspection recommended"
        if bearing > 0.6:
            return "Bearing wear suspected"
        if imbalance > 0.5:
            return "Rotor imbalance likely"
        if misalignment > 0.5:
            return "Coupling or shaft misalignment likely"
        return "Vibration levels within acceptable limits"