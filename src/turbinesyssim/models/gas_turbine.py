# -*- coding: utf-8 -*-
"""
TurbineSysSim - Gas Turbine Model
--------------------------------

Author: Arildo Yank

System-level gas turbine model representing the mechanical power
output of an industrial gas turbine.

This model bridges thermodynamics (Brayton cycle) and the rotating
machinery / generator domain. It is NOT a CFD or blade-resolved model.
"""

from dataclasses import dataclass


@dataclass
class GasTurbineInputs:
    thermal_power_w: float        # Thermal power available from combustion [W]
    turbine_efficiency: float     # 0.0 – 1.0
    mechanical_losses: float      # Fractional mechanical loss (0–1)
    shaft_speed_rpm: float        # Shaft speed [RPM]


@dataclass
class GasTurbineResults:
    mechanical_power_w: float     # Shaft mechanical power [W]
    shaft_speed_rpm: float
    mechanical_losses_w: float
    diagnostic_hint: str


class GasTurbineModel:
    """
    Engineering-oriented gas turbine shaft power model.
    """

    MIN_EFFICIENCY = 0.80

    def __init__(self, inputs: GasTurbineInputs):
        self.inputs = inputs

    # -------------------------------------------------

    def run(self) -> GasTurbineResults:
        thermal_power = max(0.0, self.inputs.thermal_power_w)

        efficiency = max(
            self.MIN_EFFICIENCY,
            min(1.0, self.inputs.turbine_efficiency),
        )

        mech_loss_frac = max(
            0.0,
            min(0.2, self.inputs.mechanical_losses),
        )

        shaft_speed = max(0.0, self.inputs.shaft_speed_rpm)

        # Ideal mechanical output from turbine
        ideal_mechanical_power = thermal_power * efficiency

        # Mechanical losses (bearings, gearbox, seals)
        mechanical_losses_w = ideal_mechanical_power * mech_loss_frac

        mechanical_power = ideal_mechanical_power - mechanical_losses_w

        diagnostic = self._diagnostic(
            efficiency,
            mech_loss_frac,
            shaft_speed,
        )

        return GasTurbineResults(
            mechanical_power_w=round(mechanical_power, 1),
            shaft_speed_rpm=round(shaft_speed, 1),
            mechanical_losses_w=round(mechanical_losses_w, 1),
            diagnostic_hint=diagnostic,
        )

    # -------------------------------------------------

    @staticmethod
    def _diagnostic(efficiency, mech_loss, rpm):
        if efficiency < 0.85:
            return "Reduced turbine efficiency detected"
        if mech_loss > 0.12:
            return "Elevated mechanical losses detected"
        if rpm <= 0:
            return "Shaft not rotating – check turbine operation"
        return "Gas turbine operating within expected limits"