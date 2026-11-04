from __future__ import annotations

from math import sqrt

import numpy as np
import pytest

from suspension_sim.core.exceptions import DomainValidationError
from suspension_sim.core.schemas import KpiSettings, SuspensionParameters
from suspension_sim.services.kpi_service import DefaultKpiCalculator, frequency_weighted_rms


def test_harmonic_rms_and_crest_factor(suspension_parameters: SuspensionParameters) -> None:
    sample_rate = 1_000.0
    time = np.arange(0.0, 20.0, 1.0 / sample_rate)
    acceleration = 2.0 * np.sin(2.0 * np.pi * 2.0 * time)
    zeros = np.zeros_like(time)

    kpis = DefaultKpiCalculator().compute(
        time_s=time,
        sprung_acceleration_m_s2=acceleration,
        suspension_travel_m=zeros,
        tire_deflection_m=zeros,
        parameters=suspension_parameters,
        settings=KpiSettings(),
    )

    assert kpis.rms_sprung_acceleration_m_s2 == pytest.approx(sqrt(2.0), rel=1.0e-6)
    assert kpis.peak_sprung_acceleration_m_s2 == pytest.approx(2.0, rel=1.0e-6)
    assert kpis.crest_factor == pytest.approx(sqrt(2.0), rel=1.0e-6)
    assert kpis.rms_weighted_acceleration_m_s2 == pytest.approx(sqrt(2.0), rel=0.02)
    assert kpis.max_tire_load_factor == pytest.approx(1.0)


def test_settling_time_uses_envelope_threshold(
    suspension_parameters: SuspensionParameters,
) -> None:
    sample_rate = 1_000.0
    time = np.arange(0.0, 4.0, 1.0 / sample_rate)
    acceleration = np.exp(-time / 0.5)
    zeros = np.zeros_like(time)

    kpis = DefaultKpiCalculator().compute(
        time_s=time,
        sprung_acceleration_m_s2=acceleration,
        suspension_travel_m=zeros,
        tire_deflection_m=zeros,
        parameters=suspension_parameters,
        settings=KpiSettings(settling_threshold_ratio=0.02),
    )

    expected = 0.5 * np.log(1.0 / 0.02)
    assert kpis.settling_time_s is not None
    assert kpis.settling_time_s == pytest.approx(expected, abs=2.0 / sample_rate)


def test_tire_load_factor_uses_static_load(
    suspension_parameters: SuspensionParameters,
) -> None:
    time = np.linspace(0.0, 1.0, 1_001)
    acceleration = np.zeros_like(time)
    travel = np.zeros_like(time)
    deflection = np.full_like(time, 0.01)

    kpis = DefaultKpiCalculator().compute(
        time_s=time,
        sprung_acceleration_m_s2=acceleration,
        suspension_travel_m=travel,
        tire_deflection_m=deflection,
        parameters=suspension_parameters,
        settings=KpiSettings(),
    )

    expected = 1.0 + 190_000.0 * 0.01 / suspension_parameters.static_tire_load_n
    assert kpis.max_tire_load_factor == pytest.approx(expected)
    assert kpis.max_suspension_travel_m == 0.0
    assert kpis.settling_time_s == 0.0


def test_mismatched_lengths_are_rejected(
    suspension_parameters: SuspensionParameters,
) -> None:
    with pytest.raises(DomainValidationError, match="samples"):
        DefaultKpiCalculator().compute(
            time_s=np.linspace(0.0, 1.0, 100),
            sprung_acceleration_m_s2=np.zeros(99),
            suspension_travel_m=np.zeros(100),
            tire_deflection_m=np.zeros(100),
            parameters=suspension_parameters,
            settings=KpiSettings(),
        )


def test_weighted_rms_falls_back_on_short_signals() -> None:
    signal = np.array([1.0, -1.0, 1.0, -1.0])
    assert frequency_weighted_rms(signal, 1_000.0, low_hz=0.5, high_hz=80.0) == pytest.approx(1.0)


def test_settling_time_is_none_when_still_ringing(
    suspension_parameters: SuspensionParameters,
) -> None:
    time = np.linspace(0.0, 1.0, 1_001)
    acceleration = 0.5 + 0.5 * np.sin(np.linspace(0.0, 20.0 * np.pi, time.size))
    kpis = DefaultKpiCalculator().compute(
        time_s=time,
        sprung_acceleration_m_s2=acceleration,
        suspension_travel_m=np.zeros_like(time),
        tire_deflection_m=np.zeros_like(time),
        parameters=suspension_parameters,
        settings=KpiSettings(settling_threshold_ratio=1.0e-6),
    )
    assert kpis.settling_time_s is None
