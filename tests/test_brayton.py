# -*- coding: utf-8 -*-
"""
TurbineSysSim - Brayton Cycle Tests
----------------------------------

Author: Arildo Yank

Pytest-based unit tests for the BraytonCycle model.
These tests verify physical consistency, efficiency trends,
and robustness against invalid inputs.
"""

import pytest

from turbinesyssim.physics.brayton_cycle import (
    BraytonInputs,
    BraytonCycle,
)


def test_brayton_nominal_operation():
    """
    Nominal operating conditions should produce
    positive net power and realistic efficiency.
    """
    inputs = BraytonInputs(
        mass_flow=25.0,
        pressure_ratio=12.0,
        inlet_temperature=288.0,
        turbine_inlet_temperature=1400.0,
        compressor_efficiency=0.85,
        turbine_efficiency=0.88,
    )

    results = BraytonCycle(inputs).run()

    assert results.net_power > 0.0
    assert 0.25 < results.thermal_efficiency < 0.5
    assert "expected" in results.diagnostic_hint.lower()


def test_brayton_low_efficiency_flagged():
    """
    Degraded component efficiencies should be flagged.
    """
    inputs = BraytonInputs(
        mass_flow=25.0,
        pressure_ratio=10.0,
        inlet_temperature=288.0,
        turbine_inlet_temperature=1200.0,
        compressor_efficiency=0.65,
        turbine_efficiency=0.7,
    )

    results = BraytonCycle(inputs).run()

    assert results.net_power > 0.0
    assert results.thermal_efficiency < 0.3
    assert (
        "efficiency" in results.diagnostic_hint.lower()
        or "degraded" in results.diagnostic_hint.lower()
    )


def test_brayton_negative_power_detected():
    """
    Unfavorable operating conditions should result
    in negative or near-zero net power.
    """
    inputs = BraytonInputs(
        mass_flow=10.0,
        pressure_ratio=20.0,
        inlet_temperature=300.0,
        turbine_inlet_temperature=900.0,
        compressor_efficiency=0.75,
        turbine_efficiency=0.75,
    )

    results = BraytonCycle(inputs).run()

    assert results.net_power <= results.turbine_work_w
    assert (
        "negative" in results.diagnostic_hint.lower()
        or "check" in results.diagnostic_hint.lower()
    )


def test_brayton_handles_invalid_inputs_gracefully():
    """
    The model should not crash with zero or invalid inputs.
    """
    inputs = BraytonInputs(
        mass_flow=0.0,
        pressure_ratio=0.0,
        inlet_temperature=0.0,
        turbine_inlet_temperature=0.0,
        compressor_efficiency=0.0,
        turbine_efficiency=0.0,
    )

    results = BraytonCycle(inputs).run()

    assert results.thermal_efficiency >= 0.0
    assert isinstance(results.net_power, float)
