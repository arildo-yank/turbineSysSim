"""
BRAYTON_CYCLE.PY
----------------
System-level Brayton cycle model for Industrial Gas Turbines (Heavy Duty).
FIXED: Divide by zero protection for zero mass flow.
"""

from dataclasses import dataclass
import numpy as np
from typing import Optional

from ..utils.constants import P_STD_ATM, T_STD_ATM
from .thermodynamics import ThermoPhysics, GasState


@dataclass
class BraytonInputs:
    mass_flow_air: float
    pressure_ratio: float
    inlet_temperature: float = T_STD_ATM
    turbine_inlet_temp: float = 1700.0
    compressor_efficiency: float = 0.89
    turbine_efficiency: float = 0.91
    combustor_efficiency: float = 0.99
    inlet_loss: float = 0.01
    combustor_loss: float = 0.04
    exhaust_loss: float = 0.02
    fuel_lhv: float = 50000000.0


@dataclass
class BraytonResults:
    compressor_power: float
    turbine_power: float
    net_power: float
    thermal_efficiency: float
    heat_rate: float
    specific_work: float
    fuel_flow: float
    total_mass_flow: float
    t_compressor_out: float
    p_compressor_out: float
    t_exhaust: float
    p_exhaust: float
    status_msg: str


class BraytonCycle:
    def __init__(self, inputs: BraytonInputs):
        self.cfg = inputs

    def run(self) -> BraytonResults:
        p1 = P_STD_ATM * (1.0 - self.cfg.inlet_loss)
        t1 = self.cfg.inlet_temperature
        m_air = self.cfg.mass_flow_air

        p2 = p1 * self.cfg.pressure_ratio

        t2 = ThermoPhysics.isentropic_compression(
            p_in=p1, p_out=p2, t_in=t1,
            efficiency=self.cfg.compressor_efficiency
        )

        w_comp = ThermoPhysics.calculate_power(m_air, t2, t1)

        p3 = p2 * (1.0 - self.cfg.combustor_loss)
        t3 = self.cfg.turbine_inlet_temp

        cp_combustor_avg = ThermoPhysics.shomate_cp((t2 + t3) / 2)
        heat_needed = m_air * cp_combustor_avg * (t3 - t2)

        lhv_eff = self.cfg.fuel_lhv * self.cfg.combustor_efficiency
        m_fuel = heat_needed / lhv_eff if lhv_eff > 0 else 0.0

        m_total = m_air + m_fuel

        p4 = P_STD_ATM * (1.0 + self.cfg.exhaust_loss)

        t4 = ThermoPhysics.isentropic_expansion(
            p_in=p3, p_out=p4, t_in=t3,
            efficiency=self.cfg.turbine_efficiency
        )

        w_turb = ThermoPhysics.calculate_power(m_total, t3, t4)

        net_power = w_turb - w_comp

        eff_thermal = net_power / (m_fuel * self.cfg.fuel_lhv) if m_fuel > 0 else 0.0
        heat_rate = (3600.0 / eff_thermal) if eff_thermal > 0 else float('inf')

        # FIXED: ZeroDivisionError protection
        if m_air > 1e-5:
            specific_work = (net_power / 1000.0) / m_air
        else:
            specific_work = 0.0

        diag = self._generate_diagnostic(net_power, eff_thermal, t4)

        return BraytonResults(
            compressor_power=w_comp,
            turbine_power=w_turb,
            net_power=net_power,
            thermal_efficiency=eff_thermal,
            heat_rate=heat_rate,
            specific_work=specific_work,
            fuel_flow=m_fuel,
            total_mass_flow=m_total,
            t_compressor_out=t2,
            p_compressor_out=p2,
            t_exhaust=t4,
            p_exhaust=p4,
            status_msg=diag
        )

    def _generate_diagnostic(self, power, eff, t_exhaust) -> str:
        if power <= 0:
            return "CRITICAL: Negative Net Power."
        if t_exhaust > 950.0:
            return "WARNING: Exhaust Temp exceeds safe limits."
        if eff < 0.25:
            return "POOR PERFORMANCE."
        return "NORMAL."