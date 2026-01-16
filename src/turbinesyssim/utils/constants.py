"""
CONSTANTS.PY
------------
Physical constants, material properties, and reference values for the TurbineSysSim.
Standard: SI Units (kg, m, s, K, Pa, J, W).

Precision: Aligned with CODATA 2018 and standard ISO conditions for Gas Turbines.
Ref: NASA Glenn Research Center - Thermodymanic Data.
"""

from typing import Final, Dict

# --- Universal Constants ---
R_UNIVERSAL: Final[float] = 8.314462618  # J/(mol·K) - Universal gas constant
G_GRAVITY: Final[float] = 9.80665        # m/s² - Standard gravity
STEFAN_BOLTZMANN: Final[float] = 5.670374419e-8 # W/(m²·K⁴) - For radiation heat transfer

# --- Atmospheric / ISO Conditions (Standard Day) ---
# Used for GE Vernova/Siemens standard performance ratings
P_STD_ATM: Final[float] = 101325.0       # Pa (1 atm)
T_STD_ATM: Final[float] = 288.15         # K (15°C) - ISO 3977 Standard
RHO_STD_AIR: Final[float] = 1.225        # kg/m³ - Standard air density at sea level

# --- Gas Properties (Air as Ideal Gas Mixture) ---
# Composition approximation: 78% N2, 21% O2, 1% Ar
MOLAR_MASS_AIR: Final[float] = 0.0289647 # kg/mol
R_SPECIFIC_AIR: Final[float] = R_UNIVERSAL / MOLAR_MASS_AIR # ~287.05 J/(kg·K)
GAMMA_AIR_STD: Final[float] = 1.4        # Ratio of specific heats (at 288K only)

# --- NASA Polynomial Coefficients (Shomate Equation) ---
# Used to calculate Cp(T), H(T), S(T) dynamically.
# Better than constant Cp because turbine temp ranges from 300K to 1600K.
# Source: NIST Chemistry WebBook
# Format: [A, B, C, D, E, F, G, H]
# Valid range approx: 298K - 1200K (Low) and 1200K - 6000K (High)
NASA_COEFFS_AIR_LOW: Final[list[float]] = [
    28.11, 0.196768e-2, 0.480228e-5, -1.96614e-9,
    -254.3854, -56.5583, -19.2631, 0.0
]

# --- Material Limits (Metallurgy) ---
# Based on Superalloys (e.g., Inconel 718, Rene 80 used in GE turbines)
T_MAX_BLADE_METAL: Final[float] = 1173.15  # K (900°C) - Material limit without cooling
T_MELTING_POINT: Final[float] = 1533.15    # K (~1260°C) - Catastrophic failure point
E_MODULUS_STEEL: Final[float] = 200.0e9    # Pa - Young's Modulus
POISSON_RATIO: Final[float] = 0.3

# --- Simulation Constraints ---
MIN_DT: Final[float] = 1e-4  # s - Minimum physics time step
MAX_DT: Final[float] = 0.1   # s - Maximum time step to prevent tunneling