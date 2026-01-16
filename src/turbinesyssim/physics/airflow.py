"""
AIRFLOW.PY
----------
High-Fidelity Airflow & Intake Model.
Simulates Compressor Intake dynamics including IGV (Inlet Guide Vane) modulation,
Corrected Speed effects, and Environmental correction factors.

Standards:
- ISO 3977 (Gas Turbines - Procurement)
- Mach Number monitoring
- Corrected Flow calculations (Theta/Delta method)
"""

from dataclasses import dataclass
import numpy as np
from typing import Final

from ..utils.constants import (
    R_SPECIFIC_AIR,
    P_STD_ATM,
    T_STD_ATM,
    GAMMA_AIR_STD
)


@dataclass
class AirflowInputs:
    # Environmental / State
    inlet_pressure: float  # Pa (Ambient static)
    inlet_temperature: float  # K (Ambient)
    rotor_speed_rpm: float  # Current RPM

    # Geometry / Control
    inlet_area: float  # m² (Geometric area of the bellmouth)
    igv_angle: float  # Degrees (0° = Closed/Min Flow, 90° = Fully Open)

    # Degradation
    fouling_factor: float = 0.0  # 0.0 (Clean) to 1.0 (Blocked)

    # Design Constants (Reference for the specific turbine model)
    design_rpm: float = 3600.0  # RPM at 100% speed
    design_mass_flow: float = 600.0  # kg/s at ISO conditions


@dataclass
class AirflowResults:
    mass_flow: float  # kg/s (Actual)
    corrected_flow: float  # kg/s (Standardized to ISO)
    volumetric_flow: float  # m³/s
    inlet_velocity: float  # m/s
    mach_number: float  # Dimensionless
    pressure_drop: float  # Pa (Loss across filters/silencers)
    air_density: float  # kg/m³
    diagnostic_status: str


class AirflowModel:
    """
    Simulates the 'breathing' of the gas turbine.
    Uses 'Corrected Parameter' method used in Aero-thermal performance decks.
    """

    def __init__(self, inputs: AirflowInputs):
        self.cfg = inputs

    def run(self) -> AirflowResults:
        # 1. Environmental Corrections (Theta & Delta)
        # Theta: Temperature correction factor
        theta = max(self.cfg.inlet_temperature, 200.0) / T_STD_ATM
        # Delta: Pressure correction factor
        delta = max(self.cfg.inlet_pressure, 1000.0) / P_STD_ATM

        # 2. Density Calculation (Ideal Gas approximation for intake is sufficient)
        # rho = P / (R * T)
        rho = self.cfg.inlet_pressure / (R_SPECIFIC_AIR * self.cfg.inlet_temperature)

        # 3. Corrected Speed Calculation
        # The compressor behaves according to N / sqrt(theta)
        # On a hot day (high theta), corrected speed is lower -> less flow capability
        n_corrected = self.cfg.rotor_speed_rpm / np.sqrt(theta)

        # 4. IGV (Inlet Guide Vane) Modulation Factor
        # Real IGVs typically modulate flow between ~40% (closed) and 100% (open)
        # Linear interpolation for simulation simplified:
        # Angle usually ranges 34 deg to 86 deg on GE frames.
        # We normalize 0-90 for simplicity.
        # factor 0.4 at 0 deg, 1.0 at 90 deg
        igv_factor = 0.4 + (0.6 * (np.clip(self.cfg.igv_angle, 0, 90) / 90.0))

        # 5. Mass Flow Calculation (Compressor Map Approximation)
        # Flow is proportional to RPM, but follows a curve.
        # For simulation: Linear approximation near rated speed, cubic at low speed.
        speed_ratio = n_corrected / self.cfg.design_rpm

        if speed_ratio < 0.1:
            # Below 10% speed (cranking), flow is very low/parasitic
            flow_characteristic = 0.05 * speed_ratio
        else:
            # Power law approximation for compressor pumping
            flow_characteristic = speed_ratio ** 1.5

        # Apply Fouling (reduces flow capacity)
        fouling_mult = 1.0 - (0.3 * self.cfg.fouling_factor)

        # Calculate Corrected Mass Flow
        m_dot_corrected = self.cfg.design_mass_flow * flow_characteristic * igv_factor * fouling_mult

        # De-correct to get Actual Mass Flow
        # m_actual = m_corrected * delta / sqrt(theta)
        m_dot_actual = m_dot_corrected * delta / np.sqrt(theta)

        # 6. Velocities and Mach
        # Effective Area reduced by fouling
        eff_area = self.cfg.inlet_area * (1.0 - (0.1 * self.cfg.fouling_factor))
        velocity = m_dot_actual / (rho * eff_area) if eff_area > 0 else 0.0

        # Speed of sound a = sqrt(gamma * R * T)
        speed_of_sound = np.sqrt(GAMMA_AIR_STD * R_SPECIFIC_AIR * self.cfg.inlet_temperature)
        mach = velocity / speed_of_sound

        # 7. Pressure Drop (Bernoulli loss across filters)
        # dP = k * 0.5 * rho * v^2
        # Clean filter k ~ 1.5, Dirty adds more
        loss_k = 1.5 + (2.0 * self.cfg.fouling_factor)
        p_drop = loss_k * 0.5 * rho * (velocity ** 2)

        # Diagnostics
        status = self._analyze_health(mach, self.cfg.fouling_factor, p_drop)

        return AirflowResults(
            mass_flow=m_dot_actual,
            corrected_flow=m_dot_corrected,
            volumetric_flow=m_dot_actual / rho,
            inlet_velocity=velocity,
            mach_number=mach,
            pressure_drop=p_drop,
            air_density=rho,
            diagnostic_status=status
        )

    def _analyze_health(self, mach, fouling, p_drop) -> str:
        if mach > 0.75:
            return "CRITICAL: Inlet Choking Risk (Mach > 0.75)"
        if fouling > 0.5:
            return "WARNING: High Filter Fouling - Maintenance Required"
        if p_drop > 2500:  # 10 inches of water approx
            return "ALARM: High Inlet Differential Pressure"
        return "NORMAL: Inlet Conditions Nominal"