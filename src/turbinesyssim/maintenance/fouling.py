# -*- coding: utf-8 -*-
"""
TurbineSysSim - Fouling Model
----------------------------

Author: Arildo Yank

Simple fouling degradation model affecting compressor efficiency.
"""


def apply_fouling(
    base_efficiency: float,
    fouling_percent: float,
) -> float:
    """
    Reduce compressor efficiency based on fouling level.

    Fouling is modeled as a linear efficiency penalty.
    """

    penalty = fouling_percent / 100.0
    degraded_efficiency = base_efficiency * (1.0 - penalty)

    return max(degraded_efficiency, 0.5)