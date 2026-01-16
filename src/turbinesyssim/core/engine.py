"""
ENGINE.PY
---------
The central dynamic simulation loop (Time-domain solver).
FIXED: Variable naming consistency (t_metal) and initialization logic.
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Final

from ..utils.constants import (
    P_STD_ATM, T_STD_ATM, G_GRAVITY, T_MAX_BLADE_METAL
)
from ..physics.airflow import AirflowModel, AirflowInputs
from ..physics.brayton_cycle import BraytonCycle, BraytonInputs, BraytonResults

# --- Simulation Constants ---
ROTOR_INERTIA: Final[float] = 1500.0  # kg·m² (Massive steel shaft)
DESIGN_RPM: Final[float] = 3600.0  # Rated Speed (60Hz generation)
DESIGN_PR: Final[float] = 18.0  # Design Pressure Ratio
STARTER_TORQUE_MAX: Final[float] = 5000.0  # N·m (Starter motor capability)
FRICTION_COEFF: Final[float] = 0.05  # Aerodynamic drag/bearing friction factor


@dataclass
class EngineState:
    """Snapshot of the engine at current timestep t."""
    time: float = 0.0
    rpm: float = 0.0
    load_mw: float = 0.0
    fuel_flow: float = 0.0

    # Temperatures
    t_inlet: float = T_STD_ATM
    t_compressor_out: float = T_STD_ATM
    t_combustor_out: float = T_STD_ATM  # TIT
    t_exhaust: float = T_STD_ATM
    t_metal: float = T_STD_ATM  # Blade material temp

    # Pressures
    p_compressor_out: float = P_STD_ATM

    # Status
    phase: str = "OFF"  # OFF, CRANKING, FIRED, ACCELERATING, RUNNING, TRIP
    vibration: float = 0.0  # mm/s
    efficiency: float = 0.0


class GasTurbineEngine:
    """
    Main Simulation Controller.
    """

    def __init__(self):
        # Physics Sub-models

        # State Vectors (Variables that change over time)
        self.rpm: float = 0.0
        self.t_metal: float = T_STD_ATM  # FIXED: Was mismatched name
        self.time: float = 0.0

        # Inputs (Control Panel)
        self.target_load_mw: float = 0.0
        self.fuel_demand: float = 0.0  # 0.0 to 1.0 (Valve position)
        self.starter_active: bool = False
        self.igv_angle: float = 34.0  # Min angle

        # Environment
        self.ambient_temp: float = T_STD_ATM
        self.ambient_pressure: float = P_STD_ATM

        # Faults
        self.is_tripped: bool = False
        self.trip_reason: str = ""

    def update(self, dt: float) -> EngineState:
        """
        Advances the physics simulation by timestep dt (seconds).
        """
        if self.is_tripped:
            self.fuel_demand = 0.0
            self.starter_active = False

        # --- 1. Rotor Dynamics & Speed Conversion ---
        # Convert RPM to Rad/s for Physics
        omega = (self.rpm * 2 * np.pi) / 60.0

        # --- 2. Scaling Laws (Off-Design) ---
        # The Pressure Ratio depends heavily on RPM.
        # Simplified Map: PR = 1 + (Design_PR - 1) * (RPM/Rated)^2
        rpm_ratio = self.rpm / DESIGN_RPM
        current_pr = 1.0 + (DESIGN_PR - 1.0) * (rpm_ratio ** 2)
        current_pr = max(1.01, current_pr)

        # --- 3. Airflow Physics ---
        airflow_in = AirflowInputs(
            inlet_pressure=self.ambient_pressure,
            inlet_temperature=self.ambient_temp,
            rotor_speed_rpm=self.rpm,
            inlet_area=2.5,  # m²
            igv_angle=self.igv_angle
        )
        airflow_model = AirflowModel(airflow_in)
        air_res = airflow_model.run()

        # --- 4. Thermodynamics (Brayton Cycle) ---
        max_fuel_rate = 15.0  # kg/s max
        ignition_permissive = self.rpm > (0.15 * DESIGN_RPM)

        actual_fuel_flow = 0.0
        tit_target = self.ambient_temp + 50.0  # Baseline heat

        if ignition_permissive and self.fuel_demand > 0 and not self.is_tripped:
            actual_fuel_flow = self.fuel_demand * max_fuel_rate
            # Energy Balance approximation
            # Q = m_fuel * LHV = m_air * Cp * delta_T
            heat_input = actual_fuel_flow * 50e6  # 50MJ/kg LHV

            # Avoid divide by zero if mass flow is tiny during start
            safe_mass_flow = max(air_res.mass_flow, 0.1)
            cp_air = 1100.0
            temp_rise = heat_input / (safe_mass_flow * cp_air)

            t2_approx = self.ambient_temp * (current_pr ** 0.286)
            tit_target = t2_approx + temp_rise

        # Safety Clamp
        tit_target = min(tit_target, 2500.0)

        brayton_in = BraytonInputs(
            mass_flow_air=air_res.mass_flow,
            pressure_ratio=current_pr,
            inlet_temperature=self.ambient_temp,
            turbine_inlet_temp=tit_target
        )

        cycle = BraytonCycle(brayton_in)
        cycle_res = cycle.run()

        # --- 5. Torque Balance (Swing Equation) ---
        safe_omega = max(omega, 1.0)

        tau_compressor = cycle_res.compressor_power / safe_omega
        tau_turbine = cycle_res.turbine_power / safe_omega

        # Load Torque
        tau_load = 0.0
        if self.rpm > (0.95 * DESIGN_RPM):
            tau_load = (self.target_load_mw * 1e6) / safe_omega

        # Starter Torque
        tau_starter = 0.0
        if self.starter_active and self.rpm < (0.6 * DESIGN_RPM):
            tau_starter = STARTER_TORQUE_MAX * (1.0 - (self.rpm / (0.6 * DESIGN_RPM)))

        # Friction
        tau_friction = (FRICTION_COEFF * self.rpm) + 50.0

        # Net Torque
        tau_net = tau_turbine + tau_starter - tau_compressor - tau_load - tau_friction

        # --- 6. Integration (Euler Method) ---
        alpha = tau_net / ROTOR_INERTIA
        omega_new = omega + (alpha * dt)

        self.rpm = (omega_new * 60.0) / (2 * np.pi)
        if self.rpm < 0: self.rpm = 0

        # --- 7. Thermal Lag (Metal Temperature) ---
        k_thermal = 0.1 * dt
        gas_avg_temp = (cycle_res.t_compressor_out + cycle_res.t_exhaust) / 2
        # Fixed: Using consistent variable self.t_metal
        self.t_metal = self.t_metal + k_thermal * (gas_avg_temp - self.t_metal)

        # --- 8. Status Logic ---
        phase = "OFF"
        if self.rpm > 10: phase = "COOLDOWN"
        if self.starter_active: phase = "CRANKING"
        if cycle_res.fuel_flow > 0.1: phase = "FIRED"
        if phase == "FIRED" and (alpha > 0.5): phase = "ACCELERATING"
        if self.rpm > (DESIGN_RPM * 0.99): phase = "FULL SPEED NO LOAD"
        if self.target_load_mw > 0.1: phase = "ON LOAD"
        if self.is_tripped: phase = "TRIPPED"

        self.time += dt
        self._check_limits(cycle_res.t_exhaust)

        return EngineState(
            time=self.time,
            rpm=self.rpm,
            load_mw=self.target_load_mw if phase == "ON LOAD" else 0.0,
            fuel_flow=cycle_res.fuel_flow,
            t_inlet=self.ambient_temp,
            t_compressor_out=cycle_res.t_compressor_out,
            t_combustor_out=brayton_in.turbine_inlet_temp,
            t_exhaust=cycle_res.t_exhaust,
            t_metal=self.t_metal,
            p_compressor_out=cycle_res.p_compressor_out,
            phase=phase,
            efficiency=cycle_res.thermal_efficiency
        )

    def _check_limits(self, t_exhaust):
        if self.rpm > (DESIGN_RPM * 1.1):
            self.is_tripped = True
            self.trip_reason = "OVERSPEED (110%)"

        if self.t_metal > T_MAX_BLADE_METAL:
            self.is_tripped = True
            self.trip_reason = "METALLURGICAL LIMIT EXCEEDED"

    def set_command(self, fuel: float, load: float, starter: bool, igv: float):
        self.fuel_demand = np.clip(fuel, 0.0, 1.0)
        self.target_load_mw = max(0.0, load)
        self.starter_active = starter
        self.igv_angle = np.clip(igv, 0.0, 90.0)