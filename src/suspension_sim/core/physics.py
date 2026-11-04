"""Two-degree-of-freedom quarter-car equations of motion.

State vector ordering is fixed across the platform::

    [z_s, z_u, v_s, v_u]

where ``z_s`` and ``z_u`` are the absolute vertical displacements of the sprung
and unsprung masses, and ``v_s`` and ``v_u`` their velocities. The road input
``z_r(t)`` enters only through the tyre deflection ``z_u - z_r``.

The model neglects tyre damping, suspension friction, geometric non-linearities
and pitch/roll coupling. Those assumptions are deliberate: they produce a
numerically stiff but well-posed linear system suitable for repeatable
experiments and for validating future higher-fidelity models.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt

import numpy as np
from numpy.typing import NDArray

from suspension_sim.core.ports import DynamicalSystem, RoadProfile
from suspension_sim.core.schemas import SimulationSettings, SuspensionParameters

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class QuarterCarModel(DynamicalSystem):
    """Linear quarter-car plant with a time-dependent road input."""

    parameters: SuspensionParameters
    road_profile: RoadProfile

    def derivatives(self, time_s: float, state: FloatArray) -> FloatArray:
        if state.shape != (4,):
            raise ValueError(f"quarter-car state must have shape (4,), received {state.shape}")

        z_s, z_u, v_s, v_u = (float(component) for component in state)
        road_height = self.road_profile.elevation(time_s)

        suspension_force = (
            self.parameters.spring_stiffness_n_per_m * (z_s - z_u)
            + self.parameters.damping_coefficient_n_s_per_m * (v_s - v_u)
        )
        tire_force = self.parameters.tire_stiffness_n_per_m * (z_u - road_height)

        sprung_acceleration = -suspension_force / self.parameters.sprung_mass_kg
        unsprung_acceleration = (
            suspension_force - tire_force
        ) / self.parameters.unsprung_mass_kg

        return np.array(
            [v_s, v_u, sprung_acceleration, unsprung_acceleration],
            dtype=np.float64,
        )

    def initial_state(self, settings: SimulationSettings) -> FloatArray:
        return np.array(
            [
                settings.initial_sprung_displacement_m,
                settings.initial_unsprung_displacement_m,
                settings.initial_sprung_velocity_m_per_s,
                settings.initial_unsprung_velocity_m_per_s,
            ],
            dtype=np.float64,
        )

    def accelerations(
        self,
        states: FloatArray,
        road_elevation_m: FloatArray,
    ) -> tuple[FloatArray, FloatArray]:
        """Vectorised accelerations for the full trajectory."""

        if states.ndim != 2 or states.shape[1] != 4:
            raise ValueError(f"states must have shape (n, 4), received {states.shape}")
        if road_elevation_m.shape != (states.shape[0],):
            raise ValueError("road elevation vector must match the state sample count")

        z_s = states[:, 0]
        z_u = states[:, 1]
        v_s = states[:, 2]
        v_u = states[:, 3]

        suspension_force = (
            self.parameters.spring_stiffness_n_per_m * (z_s - z_u)
            + self.parameters.damping_coefficient_n_s_per_m * (v_s - v_u)
        )
        tire_force = self.parameters.tire_stiffness_n_per_m * (z_u - road_elevation_m)

        sprung = -suspension_force / self.parameters.sprung_mass_kg
        unsprung = (suspension_force - tire_force) / self.parameters.unsprung_mass_kg
        return sprung, unsprung

    def suspension_travel(self, states: FloatArray) -> FloatArray:
        return states[:, 0] - states[:, 1]

    def tire_deflection(self, states: FloatArray, road_elevation_m: FloatArray) -> FloatArray:
        return states[:, 1] - road_elevation_m

    @property
    def ride_frequency_hz(self) -> float:
        return sqrt(self.parameters.spring_stiffness_n_per_m / self.parameters.sprung_mass_kg) / (
            2.0 * pi
        )

    @property
    def damping_ratio(self) -> float:
        critical = 2.0 * sqrt(
            self.parameters.spring_stiffness_n_per_m * self.parameters.sprung_mass_kg
        )
        return self.parameters.damping_coefficient_n_s_per_m / critical if critical else 0.0

    @property
    def wheel_hop_frequency_hz(self) -> float:
        return sqrt(
            (self.parameters.spring_stiffness_n_per_m + self.parameters.tire_stiffness_n_per_m)
            / self.parameters.unsprung_mass_kg
        ) / (2.0 * pi)


def body_bounce_frequency_hz(parameters: SuspensionParameters) -> float:
    """Closed-form body-bounce natural frequency."""

    return sqrt(parameters.spring_stiffness_n_per_m / parameters.sprung_mass_kg) / (2.0 * pi)


def damping_ratio(parameters: SuspensionParameters) -> float:
    """Dimensionless damping ratio of the body-bounce mode."""

    critical = 2.0 * sqrt(parameters.spring_stiffness_n_per_m * parameters.sprung_mass_kg)
    if critical <= 0.0:
        return 0.0
    return parameters.damping_coefficient_n_s_per_m / critical
