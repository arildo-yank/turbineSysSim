a
# -*- coding: utf-8 -*-
"""
TurbineSysSim - Airflow Model Tests
----------------------------------

Author: Arildo Yank

Pytest-based unit tests for the AirflowModel.
These tests validate physical consistency, bounds,
and expected degradation behaviour.
"""

import pytest

from turbinesyssim.physics.airflow import (
    AirflowInputs,
    AirflowModel,
)


def test_airflow_nominal_conditions():
    """
    Nominal operating conditions should produce
    positive and realistic airflow values.
    """
    inputs = AirflowInputs(
        inlet_pressure_pa=101325,
        inlet_temperature_k=288.0,
        inlet_area_m2=2.0,
        pressure_ratio=12.0,
        inlet_loss_coeff=0.05,
        fouling_factor=0.0,
    )

    results = AirflowModel(inputs).run()

    assert results.air_density_kg_m3 > 1.0
    assert results.mass_flow_kg_s > 0.0
    assert results.volumetric_flow_m3_s > 0.0
    assert results.inlet_velocity_m_s > 0.0
    assert results.pressure_loss_pa >= 0.0
    assert "expected" in results.diagnostic_hint.lower()


def test_airflow_with_fouling_reduces_mass_flow():
    """
    Increased fouling should reduce effective airflow.
    """
    clean_inputs = AirflowInputs(
        inlet_pressure_pa=101325,
        inlet_temperature_k=288.0,
        inlet_area_m2=2.0,
        pressure_ratio=10.0,
        fouling_factor=0.0,
    )

    fouled_inputs = AirflowInputs(
        inlet_pressure_pa=101325,
        inlet_temperature_k=288.0,
        inlet_area_m2=2.0,
        pressure_ratio=10.0,
        fouling_factor=0.5,
    )

    clean_results = AirflowModel(clean_inputs).run()
    fouled_results = AirflowModel(fouled_inputs).run()

    assert fouled_results.mass_flow_kg_s < clean_results.mass_flow_kg_s
    assert "fouling" in fouled_results.diagnostic_hint.lower()


def test_airflow_high_pressure_loss_flagged():
    """
    Excessive inlet losses should be flagged in diagnostics.
    """
    inputs = AirflowInputs(
        inlet_pressure_pa=101325,
        inlet_temperature_k=300.0,
        inlet_area_m2=0.8,
        pressure_ratio=15.0,
        inlet_loss_coeff=0.3,
        fouling_factor=0.2,
    )

    results = AirflowModel(inputs).run()

    assert results.pressure_loss_pa > 0.0
    assert (
        "pressure loss" in results.diagnostic_hint.lower()
        or "restriction" in results.diagnostic_hint.lower()
    )


def test_airflow_handles_invalid_inputs_gracefully():
    """
    Model should not crash with zero or negative inputs.
    """
    inputs = AirflowInputs(
        inlet_pressure_pa=0.0,
        inlet_temperature_k=0.0,
        inlet_area_m2=0.0,
        pressure_ratio=0.0,
        fouling_factor=-1.0,
    )

    results = AirflowModel(inputs).run()

    assert results.air_density_kg_m3 > 0.0
    assert results.mass_flow_kg_s >= 0.0
    assert results.volumetric_flow_m3_s >= 0.0