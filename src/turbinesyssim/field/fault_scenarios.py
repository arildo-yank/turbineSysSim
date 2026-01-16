# -*- coding: utf-8 -*-
"""
TurbineSysSim - Fault Scenarios
-------------------------------

Author: Arildo Yank

Definition of realistic turbine fault scenarios used for:
- Training
- Simulation
- Diagnostics validation
- What-if analysis

These scenarios reflect common field issues observed in
industrial gas and steam turbines.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class FaultScenario:
    name: str
    description: str
    fouling_percent: float
    erosion_index: float
    imbalance_level: float
    bearing_wear: float
    misalignment: float
    load_penalty: float
    efficiency_penalty: float


class FaultLibrary:
    """
    Library of predefined turbine fault scenarios.
    """

    @staticmethod
    def healthy() -> FaultScenario:
        return FaultScenario(
            name="Healthy Operation",
            description="Normal operating condition, no detectable faults",
            fouling_percent=0.0,
            erosion_index=0.0,
            imbalance_level=0.0,
            bearing_wear=0.0,
            misalignment=0.0,
            load_penalty=0.0,
            efficiency_penalty=0.0,
        )

    # -------------------------------------------------

    @staticmethod
    def compressor_fouling() -> FaultScenario:
        return FaultScenario(
            name="Compressor Fouling",
            description="Reduced airflow and efficiency due to fouling",
            fouling_percent=15.0,
            erosion_index=0.1,
            imbalance_level=0.1,
            bearing_wear=0.1,
            misalignment=0.0,
            load_penalty=0.08,
            efficiency_penalty=0.12,
        )

    # -------------------------------------------------

    @staticmethod
    def blade_erosion() -> FaultScenario:
        return FaultScenario(
            name="Blade Erosion",
            description="Erosion on compressor or turbine blades",
            fouling_percent=5.0,
            erosion_index=0.5,
            imbalance_level=0.2,
            bearing_wear=0.2,
            misalignment=0.1,
            load_penalty=0.12,
            efficiency_penalty=0.15,
        )

    # -------------------------------------------------

    @staticmethod
    def rotor_imbalance() -> FaultScenario:
        return FaultScenario(
            name="Rotor Imbalance",
            description="Rotor mass imbalance causing vibration and noise",
            fouling_percent=2.0,
            erosion_index=0.1,
            imbalance_level=0.7,
            bearing_wear=0.2,
            misalignment=0.1,
            load_penalty=0.05,
            efficiency_penalty=0.06,
        )

    # -------------------------------------------------

    @staticmethod
    def bearing_degradation() -> FaultScenario:
        return FaultScenario(
            name="Bearing Degradation",
            description="Progressive bearing wear increasing vibration",
            fouling_percent=3.0,
            erosion_index=0.1,
            imbalance_level=0.3,
            bearing_wear=0.8,
            misalignment=0.2,
            load_penalty=0.07,
            efficiency_penalty=0.08,
        )

    # -------------------------------------------------

    @staticmethod
    def shaft_misalignment() -> FaultScenario:
        return FaultScenario(
            name="Shaft Misalignment",
            description="Coupling or shaft alignment issues",
            fouling_percent=1.0,
            erosion_index=0.1,
            imbalance_level=0.3,
            bearing_wear=0.4,
            misalignment=0.8,
            load_penalty=0.06,
            efficiency_penalty=0.07,
        )

    # -------------------------------------------------

    @staticmethod
    def severe_combined_fault() -> FaultScenario:
        return FaultScenario(
            name="Severe Combined Fault",
            description="Multiple concurrent degradation mechanisms",
            fouling_percent=25.0,
            erosion_index=0.7,
            imbalance_level=0.8,
            bearing_wear=0.9,
            misalignment=0.7,
            load_penalty=0.20,
            efficiency_penalty=0.30,
        )

    # -------------------------------------------------

    @staticmethod
    def all_scenarios() -> Dict[str, FaultScenario]:
        """
        Return all scenarios in a dictionary for UI or batch simulation.
        """
        return {
            "healthy": FaultLibrary.healthy(),
            "compressor_fouling": FaultLibrary.compressor_fouling(),
            "blade_erosion": FaultLibrary.blade_erosion(),
            "rotor_imbalance": FaultLibrary.rotor_imbalance(),
            "bearing_degradation": FaultLibrary.bearing_degradation(),
            "shaft_misalignment": FaultLibrary.shaft_misalignment(),
            "severe_combined_fault": FaultLibrary.severe_combined_fault(),
        }