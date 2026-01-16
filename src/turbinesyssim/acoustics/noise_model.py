

# -*- coding: utf-8 -*-
"""
TurbineSysSim - Acoustic Noise Model
-----------------------------------

Author: Arildo Yank

System-level acoustic noise model for gas and steam turbines.
This is NOT CFD or aeroacoustic simulation.
It provides engineering-consistent noise estimation based on:
- Shaft speed (RPM)
- Load factor
- Fouling / degradation
- Mechanical imbalance

Outputs are suitable for diagnostics, trending, and visualization.
"""

from dataclasses import dataclass
import math


@dataclass
class NoiseInputs:
    rpm: float                  # Shaft speed [RPM]
    load_factor: float          # 0.0 – 1.0
    fouling_index: float        # 0 – 100 (%)
    imbalance_level: float = 0  # 0 – 1 (dimensionless)


@dataclass
class NoiseResults:
    overall_spl_db: float       # Sound Pressure Level [dB(A)]
    tonal_component_db: float   # Dominant tonal noise
    broadband_db: float         # Broadband noise
    diagnostic_hint: str


class TurbineNoiseModel:
    """
    Engineering-oriented turbine noise model.
    """

    BASE_NOISE_DB = 72.0  # Typical industrial baseline

    def __init__(self, inputs: NoiseInputs):
        self.inputs = inputs

    # -------------------------------------------------

    def run(self) -> NoiseResults:
        rpm = max(self.inputs.rpm, 1.0)
        load = max(0.0, min(1.0, self.inputs.load_factor))
        fouling = max(0.0, self.inputs.fouling_index)
        imbalance = max(0.0, self.inputs.imbalance_level)

        # Tonal noise increases strongly with RPM
        tonal = 20.0 * math.log10(rpm / 3000.0 + 1.0)

        # Broadband noise linked to load and flow turbulence
        broadband = 15.0 * load + 0.1 * fouling

        # Mechanical imbalance penalty
        imbalance_penalty = 12.0 * imbalance

        overall = (
            self.BASE_NOISE_DB
            + tonal
            + broadband
            + imbalance_penalty
        )

        diagnostic = self._diagnostic(tonal, broadband, imbalance)

        return NoiseResults(
            overall_spl_db=round(overall, 1),
            tonal_component_db=round(tonal, 1),
            broadband_db=round(broadband, 1),
            diagnostic_hint=diagnostic,
        )

    # -------------------------------------------------

    @staticmethod
    def _diagnostic(tonal, broadband, imbalance):
        if imbalance > 0.5:
            return "High mechanical imbalance detected"
        if tonal > broadband * 1.2:
            return "Dominant tonal noise (possible blade-pass or shaft-related)"
        if broadband > tonal:
            return "Broadband noise dominant (possible fouling or flow turbulence)"
        return "Normal acoustic signature"