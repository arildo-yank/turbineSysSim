# -*- coding: utf-8 -*-
"""
TurbineSysSim - Electric Generator Model
----------------------------------------

Author: Arildo Yank

System-level electric generator model for gas and steam turbine systems.
This model represents the electrical side of power generation and is
intended for performance estimation, diagnostics, and reporting.

This is NOT an electromagnetic FEM model.
"""

from dataclasses import dataclass


@dataclass
class GeneratorInputs:
    mechanical_power_w: float      # Mechanical input power [W]
    generator_efficiency: float    # 0.0 – 1.0
    power_factor: float            # 0.0 – 1.0
    grid_frequency_hz: float = 50  # Grid frequency (50 / 60 Hz)


@dataclass
class GeneratorResults:
    electrical_power_w: float      # Net electrical output [W]
    electrical_power_mw: float
    losses_w: float
    apparent_power_va: float
    diagnostic_hint: str


class ElectricGeneratorModel:
    """
    Engineering-oriented electric generator model.
    """

    MIN_EFFICIENCY = 0.85

    def __init__(self, inputs: GeneratorInputs):
        self.inputs = inputs

    # -------------------------------------------------

    def run(self) -> GeneratorResults:
        mech_power = max(0.0, self.inputs.mechanical_power_w)

        efficiency = max(
            self.MIN_EFFICIENCY,
            min(1.0, self.inputs.generator_efficiency),
        )

        power_factor = max(
            0.1,
            min(1.0, self.inputs.power_factor),
        )

        electrical_power = mech_power * efficiency
        losses = mech_power - electrical_power

        apparent_power = electrical_power / power_factor

        diagnostic = self._diagnostic(
            efficiency,
            power_factor,
            losses,
        )

        return GeneratorResults(
            electrical_power_w=round(electrical_power, 1),
            electrical_power_mw=round(electrical_power / 1e6, 3),
            losses_w=round(losses, 1),
            apparent_power_va=round(apparent_power, 1),
            diagnostic_hint=diagnostic,
        )

    # -------------------------------------------------

    @staticmethod
    def _diagnostic(efficiency, power_factor, losses):
        if efficiency < 0.9:
            return "Reduced generator efficiency detected"
        if power_factor < 0.85:
            return "Low power factor – reactive compensation recommended"
        if losses > 1e6:
            return "High electrical losses – cooling or insulation check advised"
        return "Generator operating within expected limits"