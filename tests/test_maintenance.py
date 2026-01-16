# -*- coding: utf-8 -*-
"""
TurbineSysSim - Maintenance Model Tests
--------------------------------------

Author: Arildo Yank

Pytest-based unit tests for the MaintenanceModel.
These tests validate fouling, erosion, aging effects,
and overall robustness of the maintenance degradation logic.
"""

from src.turbinesyssim.maintenance.maintenance_model import (
    MaintenanceInputs,
    MaintenanceModel,
)


def test_maintenance_nominal_conditions():
    """
    Nominal maintenance conditions should result
    in minimal efficiency penalties.
    """
    inputs = MaintenanceInputs(
        base_compressor_efficiency=0.85,
        base_turbine_efficiency=0.88,
        fouling_percent=0.0,
        erosion_index=0.0,
        operating_hours=1000,
        particle_severity=0.1,
    )

    results = MaintenanceModel(inputs).run()

    assert results.compressor_efficiency <= 0.85
    assert results.turbine_efficiency <= 0.88
    assert results.efficiency_penalty >= 0.0
    assert "expected" in results.diagnostic_hint.lower()


def test_maintenance_fouling_degrades_compressor():
    """
    Increased fouling should reduce compressor efficiency.
    """
    clean_inputs = MaintenanceInputs(
        base_compressor_efficiency=0.85,
        base_turbine_efficiency=0.88,
        fouling_percent=0.0,
        erosion_index=0.0,
        operating_hours=5000,
        particle_severity=0.2,
    )

    fouled_inputs = MaintenanceInputs(
        base_compressor_efficiency=0.85,
        base_turbine_efficiency=0.88,
        fouling_percent=20.0,
        erosion_index=0.0,
        operating_hours=5000,
        particle_severity=0.2,
    )

    clean = MaintenanceModel(clean_inputs).run()
    fouled = MaintenanceModel(fouled_inputs).run()

    assert fouled.compressor_efficiency < clean.compressor_efficiency
    assert "fouling" in fouled.diagnostic_hint.lower()


def test_maintenance_erosion_degrades_turbine():
    """
    Increased erosion should reduce turbine efficiency
    and flow capacity.
    """
    low_erosion = MaintenanceInputs(
        base_compressor_efficiency=0.85,
        base_turbine_efficiency=0.88,
        fouling_percent=5.0,
        erosion_index=0.1,
        operating_hours=15000,
        particle_severity=0.3,
    )

    high_erosion = MaintenanceInputs(
        base_compressor_efficiency=0.85,
        base_turbine_efficiency=0.88,
        fouling_percent=5.0,
        erosion_index=0.7,
        operating_hours=15000,
        particle_severity=0.3,
    )

    low = MaintenanceModel(low_erosion).run()
    high = MaintenanceModel(high_erosion).run()

    assert high.turbine_efficiency < low.turbine_efficiency
    assert high.flow_capacity_loss >= low.flow_capacity_loss
    assert "erosion" in high.diagnostic_hint.lower()


def test_maintenance_combined_degradation_flagged():
    """
    Severe fouling and erosion combined should be flagged
    with a strong maintenance recommendation.
    """
    inputs = MaintenanceInputs(
        base_compressor_efficiency=0.85,
        base_turbine_efficiency=0.88,
        fouling_percent=25.0,
        erosion_index=0.8,
        operating_hours=40000,
        particle_severity=0.6,
    )

    results = MaintenanceModel(inputs).run()

    assert results.efficiency_penalty > 0.2
    assert (
        "maintenance" in results.diagnostic_hint.lower()
        or "recommended" in results.diagnostic_hint.lower()
    )


def test_maintenance_handles_invalid_inputs_gracefully():
    """
    The model should not crash with invalid or zero inputs.
    """
    inputs = MaintenanceInputs(
        base_compressor_efficiency=0.0,
        base_turbine_efficiency=0.0,
        fouling_percent=-10.0,
        erosion_index=-1.0,
        operating_hours=-100.0,
        particle_severity=-0.5,
    )

    results = MaintenanceModel(inputs).run()

    assert results.compressor_efficiency >= 0.0
    assert results.turbine_efficiency >= 0.0
