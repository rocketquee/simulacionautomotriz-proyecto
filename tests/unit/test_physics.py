from __future__ import annotations

from math import pi, sqrt

import numpy as np
import pytest

from suspension_sim.core.physics import QuarterCarModel, body_bounce_frequency_hz, damping_ratio
from suspension_sim.core.ports import RoadProfile
from suspension_sim.core.schemas import (
    RoadProfileSettings,
    SimulationSettings,
    SuspensionParameters,
)
from suspension_sim.infrastructure.solvers import ScipyOdeSolver


class FlatRoad(RoadProfile):
    def elevation(self, time_s: float) -> float:
        return 0.0

    def velocity(self, time_s: float) -> float:
        return 0.0

    def description(self) -> str:
        return "flat"


def test_closed_form_frequencies(suspension_parameters: SuspensionParameters) -> None:
    expected = sqrt(25_000.0 / 300.0) / (2.0 * pi)
    assert body_bounce_frequency_hz(suspension_parameters) == pytest.approx(expected)
    assert suspension_parameters.ride_frequency_hz == pytest.approx(expected)
    assert suspension_parameters.damping_ratio == pytest.approx(
        1_800.0 / (2.0 * sqrt(25_000.0 * 300.0))
    )
    assert damping_ratio(suspension_parameters) == pytest.approx(
        suspension_parameters.damping_ratio
    )


def test_derivatives_at_equilibrium_are_zero(
    suspension_parameters: SuspensionParameters,
) -> None:
    model = QuarterCarModel(suspension_parameters, FlatRoad())
    derivatives = model.derivatives(0.0, np.zeros(4))
    np.testing.assert_allclose(derivatives, np.zeros(4), atol=1.0e-15)


def test_derivatives_follow_newton_balance(
    suspension_parameters: SuspensionParameters,
) -> None:
    model = QuarterCarModel(suspension_parameters, FlatRoad())
    state = np.array([0.01, 0.0, 0.0, 0.0])
    derivatives = model.derivatives(0.0, state)
    suspension_force = suspension_parameters.spring_stiffness_n_per_m * 0.01

    assert derivatives[0] == pytest.approx(0.0)
    assert derivatives[1] == pytest.approx(0.0)
    assert derivatives[2] == pytest.approx(-suspension_force / 300.0)
    assert derivatives[3] == pytest.approx(suspension_force / 40.0)


def test_solver_returns_expected_grid(
    suspension_parameters: SuspensionParameters,
    simulation_settings: SimulationSettings,
) -> None:
    model = QuarterCarModel(suspension_parameters, FlatRoad())
    output = ScipyOdeSolver().solve(
        model,
        simulation_settings,
        np.array([0.01, 0.0, 0.0, 0.0]),
    )

    assert output.success is True
    assert output.time_s.size == simulation_settings.sample_count
    assert output.states.shape == (simulation_settings.sample_count, 4)
    assert output.time_s[0] == 0.0
    assert output.time_s[-1] == pytest.approx(simulation_settings.duration_s)
    assert np.all(np.isfinite(output.states))
    assert output.function_evaluations > 0


def test_free_vibration_decays_with_damping(
    suspension_parameters: SuspensionParameters,
    simulation_settings: SimulationSettings,
) -> None:
    model = QuarterCarModel(suspension_parameters, FlatRoad())
    output = ScipyOdeSolver().solve(
        model,
        simulation_settings,
        np.array([0.02, 0.0, 0.0, 0.0]),
    )

    early_peak = float(np.max(np.abs(output.states[:200, 0])))
    late_peak = float(np.max(np.abs(output.states[-200:, 0])))
    assert late_peak < 0.2 * early_peak


def test_initial_state_uses_settings(
    suspension_parameters: SuspensionParameters,
) -> None:
    settings = SimulationSettings(
        duration_s=2.0,
        sample_rate_hz=500.0,
        initial_sprung_displacement_m=0.01,
        initial_unsprung_velocity_m_per_s=-0.2,
    )
    model = QuarterCarModel(suspension_parameters, FlatRoad())
    np.testing.assert_allclose(model.initial_state(settings), [0.01, 0.0, 0.0, -0.2])


def test_invalid_state_shape_is_rejected(
    suspension_parameters: SuspensionParameters,
) -> None:
    model = QuarterCarModel(suspension_parameters, FlatRoad())
    with pytest.raises(ValueError, match="shape"):
        model.derivatives(0.0, np.zeros(3))


def test_road_settings_are_validated() -> None:
    with pytest.raises(ValueError):
        RoadProfileSettings(kind="smooth_bump", amplitude_m=-0.1)
