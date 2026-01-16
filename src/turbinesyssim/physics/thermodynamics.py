"""
THERMODYNAMICS.PY
-----------------
Core thermodynamic calculations engine.
Implements Real Gas effects approximations necessary for high-fidelity
Gas Turbine simulation (GE/Siemens class).

Key Features:
- Temperature-dependent Specific Heat (Cp) using NASA Shomate Equations.
- Isentropic flow relations.
- State management for gas parcels.
"""

import numpy as np
from dataclasses import dataclass
from typing import Union, Tuple

from ..utils.constants import (
    R_SPECIFIC_AIR,
    NASA_COEFFS_AIR_LOW,
    MOLAR_MASS_AIR,
    P_STD_ATM,
    T_STD_ATM
)

# Type alias for scalar or vector (for vectorized numpy operations)
FloatOrArray = Union[float, np.ndarray]


@dataclass(frozen=True)
class GasState:
    """
    Represents a snapshot of the gas properties at a specific point in the cycle.
    Frozen (immutable) to ensure physics consistency across steps.
    """
    temperature: float  # Kelvin
    pressure: float  # Pascals
    mass_flow: float  # kg/s

    # Derived properties (computed on init usually, but kept simple here)
    @property
    def density(self) -> float:
        """Calculates density (rho) using Ideal Gas Law: rho = P / (R*T)"""
        if self.temperature <= 0: return 0.0
        return self.pressure / (R_SPECIFIC_AIR * self.temperature)


class ThermoPhysics:
    """
    Static physics engine for thermodynamic transformations.
    """

    @staticmethod
    def shomate_cp(temperature: FloatOrArray) -> FloatOrArray:
        """
        Calculates Specific Heat at Constant Pressure (Cp) [J/(kg·K)].
        Uses NASA Shomate Polynomials for high fidelity at high temps.

        Ref: NIST Chemistry WebBook
        """
        # Clamp temperature to avoid math errors (min 200K, max 2500K for this model)
        T = np.clip(temperature, 200.0, 2500.0)
        t = T / 1000.0  # Shomate equation uses T/1000

        coeffs = NASA_COEFFS_AIR_LOW

        # Cp_molar = A + B*t + C*t^2 + D*t^3 + E/t^2  (J/(mol·K))
        cp_molar = (
                coeffs[0] +
                coeffs[1] * t +
                coeffs[2] * (t ** 2) +
                coeffs[3] * (t ** 3) +
                coeffs[4] / (t ** 2)
        )

        # Convert Molar Cp to Specific Cp (J/(kg·K))
        cp_specific = cp_molar / MOLAR_MASS_AIR

        return cp_specific

    @staticmethod
    def get_gamma(temperature: FloatOrArray) -> FloatOrArray:
        """
        Calculates Heat Capacity Ratio (Gamma = Cp / Cv).
        Real gases do not have a fixed 1.4 gamma. It drops as temp rises.
        """
        cp = ThermoPhysics.shomate_cp(temperature)
        cv = cp - R_SPECIFIC_AIR  # Mayer's relation
        return cp / cv

    @staticmethod
    def isentropic_compression(
            p_in: float,
            p_out: float,
            t_in: float,
            efficiency: float = 1.0
    ) -> float:
        """
        Calculates output temperature for a compression process.
        Includes Isentropic Efficiency (eta) to simulate real compressor losses.

        Returns:
            T_out (Kelvin)
        """
        if p_in <= 0 or p_out <= 0: return t_in

        pressure_ratio = p_out / p_in

        # We use an average gamma for the process to be more precise than fixed 1.4
        # Iterative approach: guess T_out, calc gamma_avg, refine T_out.
        # For real-time sim (60fps), a single pass estimate using T_in is usually sufficient
        # or a lightweight 2-step estimation.

        gamma = ThermoPhysics.get_gamma(t_in)
        k = (gamma - 1) / gamma

        # Ideal Isentropic Temperature
        t_out_ideal = t_in * (pressure_ratio ** k)

        # Apply Isentropic Efficiency: (T_ideal - T_in) / (T_real - T_in) = eta
        # Rearranged: T_real = T_in + (T_ideal - T_in) / eta

        delta_t_ideal = t_out_ideal - t_in
        t_out_real = t_in + (delta_t_ideal / efficiency)

        return t_out_real

    @staticmethod
    def isentropic_expansion(
            p_in: float,
            p_out: float,
            t_in: float,
            efficiency: float = 1.0
    ) -> float:
        """
        Calculates output temperature for an expansion process (Turbine).
        """
        if p_in <= 0 or p_out <= 0: return t_in

        pressure_ratio = p_out / p_in  # This will be < 1

        # Use T_in to estimate gamma (Simpler for performance)
        gamma = ThermoPhysics.get_gamma(t_in)
        k = (gamma - 1) / gamma

        t_out_ideal = t_in * (pressure_ratio ** k)

        # Turbine Efficiency: (T_in - T_real) / (T_in - T_ideal) = eta
        # Rearranged: T_real = T_in - eta * (T_in - T_ideal)

        delta_t_ideal = t_in - t_out_ideal
        t_out_real = t_in - (efficiency * delta_t_ideal)

        return t_out_real

    @staticmethod
    def calculate_power(
            mass_flow: float,
            t_in: float,
            t_out: float
    ) -> float:
        """
        Calculates Power (Watts) = m_dot * Cp_avg * Delta_T
        Positive for Turbine (Work extraction), Negative for Compressor (Work input).
        """
        t_avg = (t_in + t_out) / 2
        cp = ThermoPhysics.shomate_cp(t_avg)

        # W = m * cp * (T_in - T_out)
        # Note: For compressor, T_out > T_in, so result is negative (consuming power)
        # For turbine, T_in > T_out, so result is positive (generating power)
        return mass_flow * cp * (t_in - t_out)