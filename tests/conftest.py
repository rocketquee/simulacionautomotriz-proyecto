from __future__ import annotations

import pytest

from suspension_sim.core.schemas import (
    RoadProfileSettings,
    SimulationRequest,
    SimulationSettings,
    SuspensionParameters,
)


@pytest.fixture()
def suspension_parameters() -> SuspensionParameters:
    return SuspensionParameters(
        sprung_mass_kg=300.0,
        unsprung_mass_kg=40.0,
        spring_stiffness_n_per_m=25_000.0,
        damping_coefficient_n_s_per_m=1_800.0,
        tire_stiffness_n_per_m=190_000.0,
    )


@pytest.fixture()
def simulation_settings() -> SimulationSettings:
    return SimulationSettings(
        duration_s=3.0,
        sample_rate_hz=1_000.0,
        solver="DOP853",
        relative_tolerance=1.0e-8,
        absolute_tolerance=1.0e-10,
        max_step_s=0.002,
    )


@pytest.fixture()
def road_settings() -> RoadProfileSettings:
    return RoadProfileSettings(
        kind="smooth_bump",
        amplitude_m=0.05,
        bump_length_m=1.0,
        speed_m_per_s=10.0,
        start_distance_m=1.0,
    )


@pytest.fixture()
def simulation_request(
    suspension_parameters: SuspensionParameters,
    simulation_settings: SimulationSettings,
    road_settings: RoadProfileSettings,
) -> SimulationRequest:
    return SimulationRequest(
        label="pytest-corner",
        suspension=suspension_parameters,
        simulation=simulation_settings,
        road=road_settings,
    )
