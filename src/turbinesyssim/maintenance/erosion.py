# -*- coding: utf-8 -*-
"""
TurbineSysSim - Erosion Model
----------------------------

Author: Arildo Yank

System-level erosion model for gas and steam turbine components.
This model estimates performance degradation caused by:
- Particle ingestion (dust, sand, ash)
- Droplet impingement (wet steam / inlet fogging)
- Long-term surface roughness increase

This is NOT CFD or blade-resolved erosion.
It is intended for performance trending, diagnostics,
and maintenance planning.
"""

from dataclasses import dataclass


@dataclass
class ErosionInputs:
    erosion_index: float        # 0.0 – 1.0 (severity)
    operating_hours: float      # Total operating hours
    particle_severity: float    # 0.0 – 1.0 (environmental harshness)


@dataclass
class ErosionResults:
    efficiency_penalty: float   # Fractional loss (0–1)
    flow_capacity_loss: float   # Fractional airflow loss
    diagnostic_hint: str


class TurbineErosionModel:
    """
    Engineering-oriented erosion degradation model.
    """

    BASE_EFFICIENCY_LOSS = 0.02   # baseline erosion penalty
    BASE_FLOW_LOSS = 0.015

    def __init__(self, inputs: ErosionInputs):
        self.inputs = inputs

    # -------------------------------------------------

    def run(self) -> ErosionResults:
        erosion = max(0.0, min(1.0, self.inputs.erosion_index))
        hours = max(0.0, self.inputs.operating_hours)
        particles = max(0.0, min(1.0, self.inputs.particle_severity))

        # Time-based accumulation factor (logarithmic saturation)
        time_factor = min(1.0, 0.15 * (hours / 10000.0))

        # Efficiency degradation
        efficiency_loss = (
            self.BASE_EFFICIENCY_LOSS
            + 0.20 * erosion
            + 0.10 * particles
        ) * (1.0 + time_factor)

        # Flow capacity reduction
        flow_loss = (
            self.BASE_FLOW_LOSS
            + 0.18 * erosion
            + 0.08 * particles
        ) * (1.0 + time_factor)

        diagnostic = self._diagnostic(erosion, particles, hours)

        return ErosionResults(
            efficiency_penalty=round(efficiency_loss, 3),
            flow_capacity_loss=round(flow_loss, 3),
            diagnostic_hint=diagnostic,
        )

    # -------------------------------------------------

    @staticmethod
    def _diagnostic(erosion, particles, hours):
        if erosion > 0.6:
            return "Severe blade erosion likely"
        if particles > 0.6:
            return "High particle ingestion environment"
        if hours > 30000:
            return "Long-term erosion effects accumulating"
        return "Erosion levels within expected limits"