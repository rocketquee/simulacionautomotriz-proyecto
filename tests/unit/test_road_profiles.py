from __future__ import annotations

from math import sqrt

import numpy as np
import pytest

from suspension_sim.core.schemas import RoadKind, RoadProfileSettings
from suspension_sim.infrastructure.road_profiles import (
    Iso8608Road,
    RoadProfileFactory,
    SinusoidalRoad,
    SmoothBumpRoad,
    StepRoad,
)


def _settings(**overrides: object) -> RoadProfileSettings:
    base = {
        "kind": RoadKind.SMOOTH_BUMP,
        "amplitude_m": 0.05,
        "bump_length_m": 1.0,
        "wavelength_m": 4.0,
        "speed_m_per_s": 10.0,
        "start_distance_m": 1.0,
    }
    base.update(overrides)
    return RoadProfileSettings(**base)  # type: ignore[arg-type]


def test_smooth_bump_peaks_at_half_length() -> None:
    road = SmoothBumpRoad(_settings())
    assert road.elevation(0.0) == 0.0
    assert road.elevation(0.15) == pytest.approx(0.05)
    assert road.elevation(0.4) == 0.0
    assert road.velocity(0.12) > 0.0
    assert road.description().startswith("smooth_bump")


def test_smooth_bump_vectorised_matches_scalar() -> None:
    road = SmoothBumpRoad(_settings())
    times = np.linspace(0.0, 0.5, 500)
    vectorised = road.elevation_array(times)
    scalar = np.array([road.elevation(float(value)) for value in times])
    np.testing.assert_allclose(vectorised, scalar)


def test_sinusoidal_rms_and_bounds() -> None:
    road = SinusoidalRoad(_settings(kind=RoadKind.SINUSOIDAL, wavelength_m=4.0))
    times = np.linspace(0.0, 20.0, 20_000)
    values = road.elevation_array(times)
    assert np.max(np.abs(values)) <= 0.05 + 1.0e-12
    assert float(np.sqrt(np.mean(values**2))) == pytest.approx(0.05 / sqrt(2.0), rel=0.02)


def test_step_reaches_amplitude_after_transition() -> None:
    road = StepRoad(_settings(kind=RoadKind.STEP))
    assert road.elevation(0.09) == pytest.approx(0.0, abs=1.0e-12)
    assert road.elevation(0.3) == pytest.approx(0.05)
    assert road.velocity(0.3) == 0.0


def test_iso8608_is_deterministic_and_seed_sensitive() -> None:
    first = Iso8608Road(_settings(kind=RoadKind.ISO8608, random_seed=10))
    second = Iso8608Road(_settings(kind=RoadKind.ISO8608, random_seed=10))
    third = Iso8608Road(_settings(kind=RoadKind.ISO8608, random_seed=11))

    times = np.linspace(0.0, 10.0, 2_000)
    first_values = first.elevation_array(times)
    np.testing.assert_allclose(first_values, second.elevation_array(times))
    assert not np.allclose(first_values, third.elevation_array(times))
    assert float(np.max(np.abs(first_values))) > 1.0e-3
    assert np.all(np.isfinite(first.velocity_array(times)))


def test_factory_builds_every_supported_kind() -> None:
    for kind in RoadKind:
        road = RoadProfileFactory.create(_settings(kind=kind))
        assert road.elevation(0.5) == pytest.approx(road.elevation(0.5))
        assert isinstance(road.description(), str)
