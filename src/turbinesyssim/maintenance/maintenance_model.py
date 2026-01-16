# -*- coding: utf-8 -*-
"""
TurbineSysSim - Maintenance Degradation Model
---------------------------------------------

Author: Arildo Yank

Integrated maintenance degradation model combining:
- Fouling
- Erosion
- Operating hours (aging)

This module aggregates degradation mechanisms and produces
net performance penalties suitable for:
- Simulation loops
- Diagnostics
- Maintenance planning
"""

from dataclasses import dataclass

from .fouling import apply_fouling
from .erosion import (
    ErosionInputs,
    TurbineErosionModel,
)


@dataclass
class MaintenanceInputs:
    base_compressor_efficiency: float
    base_turbine_efficiency: float
    fouling_percent: float
    erosion_index: float
    operating_hours: float
    particle_severity: float


@dataclass
class MaintenanceResults:
    compressor_efficiency: float
    turbine_efficiency: float
    efficiency_penalty: float
    flow_capacity_loss: float
    diagnostic_hint: str


class MaintenanceModel:
    """
    High-level maintenance degradation aggregator.
    """

    def __init__(self, inputs: MaintenanceInputs):
        self.inputs = inputs

    # -------------------------------------------------

    def run(self) -> MaintenanceResults:
        # --- Fouling impact (compressor-centric) ---
        compressor_eff = apply_fouling(
            self.inputs.base_compressor_efficiency,
            self.inputs.fouling_percent,
        )

        fouling_penalty = (
            self.inputs.base_compressor_efficiency - compressor_eff
        )

        # --- Erosion impact (turbine + flow capacity) ---
        erosion_inputs = ErosionInputs(
            erosion_index=self.inputs.erosion_index,
            operating_hours=self.inputs.operating_hours,
            particle_severity=self.inputs.particle_severity,
        )

        erosion_model = TurbineErosionModel(erosion_inputs)
        erosion_results = erosion_model.run()

        turbine_eff = max(
            0.5,
            self.inputs.base_turbine_efficiency
            * (1.0 - erosion_results.efficiency_penalty),
        )

        # --- Aggregate penalties ---
        total_efficiency_penalty = (
            fouling_penalty + erosion_results.efficiency_penalty
        )

        diagnostic = self._diagnostic(
            self.inputs.fouling_percent,
            self.inputs.erosion_index,
            self.inputs.operating_hours,
        )

        return MaintenanceResults(
            compressor_efficiency=round(compressor_eff, 3),
            turbine_efficiency=round(turbine_eff, 3),
            efficiency_penalty=round(total_efficiency_penalty, 3),
            flow_capacity_loss=round(
                erosion_results.flow_capacity_loss, 3
            ),
            diagnostic_hint=diagnostic,
        )

    # -------------------------------------------------

    @staticmethod
    def _diagnostic(fouling, erosion, hours):
        if fouling > 15 and erosion > 0.4:
            return "Combined fouling and erosion – maintenance strongly recommended"
        if fouling > 15:
            return "Significant compressor fouling detected"
        if erosion > 0.5:
            return "Advanced blade erosion detected"
        if hours > 30000:
            return "Age-related degradation accumulating"
        return "Maintenance condition within expected limits"