# -*- coding: utf-8 -*-
"""
TurbineSysSim - Steam Turbine Model
----------------------------------

Author: Arildo Yank

System-level steam turbine model representing the mechanical power
output of an industrial steam turbine (Rankine cycle side).

This model is intended for combined-cycle simulations, diagnostics,
and performance estimation.

It is NOT a CFD or blade-resolved thermodynamic model.
"""

from dataclasses import dataclass


@dataclass
class SteamTurbineInputs:
    thermal_power_w: float        # Thermal power from steam expansion [W]
    turbine_efficiency: float     # 0.0 – 1.0 (isentropic efficiency)
    mechanical_losses: float      # Fractional mechanical loss (0–1)
    inlet_pressure_bar: float     # Steam inlet pressure [bar]
    outlet_pressure_bar: float    # Steam outlet pressure [bar]
    shaft_speed_rpm: float        # Shaft speed [RPM]


@dataclass
class SteamTurbineResults:
    mechanical_power_w: float     # Shaft mechanical power [W]
    shaft_speed_rpm: float
    pressure_ratio: float
    mechanical_losses_w: float
    diagnostic_hint: str


class SteamTurbineModel:
    """
    Engineering-oriented steam turbine shaft power model.
    """

    MIN_EFFICIENCY = 0.75

    def __init__(self, inputs: SteamTurbineInputs):
        self.inputs = inputs

    # -------------------------------------------------

    def run(self) -> SteamTurbineResults:
        thermal_power = max(0.0, self.inputs.thermal_power_w)

        efficiency = max(
            self.MIN_EFFICIENCY,
            min(1.0, self.inputs.turbine_efficiency),
        )

        mech_loss_frac = max(
            0.0,
            min(0.25, self.inputs.mechanical_losses),
        )

        inlet_p = max(self.inputs.inlet_pressure_bar, 0.1)
        outlet_p = max(self.inputs.outlet_pressure_bar, 0.01)
        shaft_speed = max(0.0, self.inputs.shaft_speed_rpm)

        pressure_ratio = inlet_p / outlet_p

        # Ideal mechanical output from steam expansion
        ideal_mechanical_power = thermal_power * efficiency

        # Mechanical losses (bearings, seals, gearbox)
        mechanical_losses_w = ideal_mechanical_power * mech_loss_frac

        mechanical_power = ideal_mechanical_power - mechanical_losses_w

        diagnostic = self._diagnostic(
            efficiency,
            mech_loss_frac,
            pressure_ratio,
            shaft_speed,
        )

        return SteamTurbineResults(
            mechanical_power_w=round(mechanical_power, 1),
            shaft_speed_rpm=round(shaft_speed, 1),
            pressure_ratio=round(pressure_ratio, 2),
            mechanical_losses_w=round(mechanical_losses_w, 1),
            diagnostic_hint=diagnostic,
        )

    # -------------------------------------------------

    @staticmethod
    def _diagnostic(efficiency, mech_loss, pressure_ratio, rpm):
        if efficiency < 0.80:
            return "Reduced steam turbine efficiency detected"
        if mech_loss > 0.15:
            return "Elevated mechanical losses detected"
        if pressure_ratio < 2.0:
            return "Low pressure ratio – check steam conditions"
        if rpm <= 0:
            return "Shaft not rotating – check steam admission"
        return "Steam turbine operating within expected limits"