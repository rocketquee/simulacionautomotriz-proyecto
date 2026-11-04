"""Deterministic road excitation adapters.

All profiles are expressed as functions of time. Spatial quantities are mapped
to time through the constant forward speed ``x = v * t``. This keeps the plant
equations time-invariant and lets the same profile be replayed at different
speeds without regenerating the road geometry.

The ISO 8608 profile is a finite sum of spatial sinusoids whose amplitudes are
derived from the one-sided displacement PSD::

    Gd(n) = Gd(n0) * (n / n0) ** (-w)

with ``n0 = 0.1 cycles/m``. The sum is deterministic for a given seed, which is
essential for reproducible experiments and regression testing.
"""

from __future__ import annotations

from math import cos, pi, sin
from typing import ClassVar

import numpy as np
from numpy.typing import NDArray

from suspension_sim.core.exceptions import RoadProfileError
from suspension_sim.core.ports import RoadProfile
from suspension_sim.core.schemas import RoadKind, RoadProfileSettings

FloatArray = NDArray[np.float64]

_ISO_REFERENCE_FREQUENCY = 0.1
_ISO_MIN_FREQUENCY = 0.01
_ISO_MAX_FREQUENCY = 3.0
_ISO_BANDS = 240
_STEP_TRANSITION_M = 0.05
_VECTOR_CHUNK = 20_000


class _TimeRoadProfile(RoadProfile):
    """Shared speed and distance bookkeeping."""

    def __init__(self, settings: RoadProfileSettings) -> None:
        self._settings = settings
        self._speed = settings.speed_m_per_s
        self._start_distance = settings.start_distance_m

    @property
    def settings(self) -> RoadProfileSettings:
        return self._settings

    def _distance(self, time_s: float) -> float:
        return self._speed * time_s - self._start_distance

    def _distance_array(self, time_s: FloatArray) -> FloatArray:
        return self._speed * time_s - self._start_distance


class SmoothBumpRoad(_TimeRoadProfile):
    """Raised-cosine single bump, C¹ continuous with the flat road."""

    def elevation(self, time_s: float) -> float:
        distance = self._distance(time_s)
        length = self._settings.bump_length_m
        if distance <= 0.0 or distance >= length:
            return 0.0
        return 0.5 * self._settings.amplitude_m * (1.0 - cos(2.0 * pi * distance / length))

    def velocity(self, time_s: float) -> float:
        distance = self._distance(time_s)
        length = self._settings.bump_length_m
        if distance <= 0.0 or distance >= length:
            return 0.0
        slope = 0.5 * self._settings.amplitude_m * (2.0 * pi / length) * sin(
            2.0 * pi * distance / length
        )
        return slope * self._speed

    def elevation_array(self, time_s: FloatArray) -> FloatArray:
        distance = self._distance_array(time_s)
        length = self._settings.bump_length_m
        mask = (distance > 0.0) & (distance < length)
        values = np.zeros_like(time_s, dtype=np.float64)
        values[mask] = 0.5 * self._settings.amplitude_m * (
            1.0 - np.cos(2.0 * pi * distance[mask] / length)
        )
        return values

    def velocity_array(self, time_s: FloatArray) -> FloatArray:
        distance = self._distance_array(time_s)
        length = self._settings.bump_length_m
        mask = (distance > 0.0) & (distance < length)
        values = np.zeros_like(time_s, dtype=np.float64)
        values[mask] = (
            self._speed
            * 0.5
            * self._settings.amplitude_m
            * (2.0 * pi / length)
            * np.sin(2.0 * pi * distance[mask] / length)
        )
        return values

    def description(self) -> str:
        return (
            f"smooth_bump(amplitude={self._settings.amplitude_m:.4f} m, "
            f"length={self._settings.bump_length_m:.3f} m)"
        )


class SinusoidalRoad(_TimeRoadProfile):
    """Harmonic road excitation with a fixed spatial wavelength."""

    def elevation(self, time_s: float) -> float:
        distance = self._distance(time_s)
        return self._settings.amplitude_m * sin(2.0 * pi * distance / self._settings.wavelength_m)

    def velocity(self, time_s: float) -> float:
        distance = self._distance(time_s)
        spatial_frequency = 2.0 * pi / self._settings.wavelength_m
        return (
            self._settings.amplitude_m
            * spatial_frequency
            * cos(spatial_frequency * distance)
            * self._speed
        )

    def elevation_array(self, time_s: FloatArray) -> FloatArray:
        distance = self._distance_array(time_s)
        return self._settings.amplitude_m * np.sin(
            2.0 * pi * distance / self._settings.wavelength_m
        )

    def velocity_array(self, time_s: FloatArray) -> FloatArray:
        distance = self._distance_array(time_s)
        spatial_frequency = 2.0 * pi / self._settings.wavelength_m
        return (
            self._settings.amplitude_m
            * spatial_frequency
            * np.cos(spatial_frequency * distance)
            * self._speed
        )

    def description(self) -> str:
        return (
            f"sinusoidal(amplitude={self._settings.amplitude_m:.4f} m, "
            f"wavelength={self._settings.wavelength_m:.3f} m)"
        )


class StepRoad(_TimeRoadProfile):
    """Step input with a 50 mm smoothstep transition to keep velocities finite."""

    def _smoothstep(self, distance: FloatArray) -> tuple[FloatArray, FloatArray]:
        ratio = np.clip(distance / _STEP_TRANSITION_M, 0.0, 1.0)
        height = self._settings.amplitude_m * (3.0 * ratio**2 - 2.0 * ratio**3)
        slope = self._settings.amplitude_m * (6.0 * ratio - 6.0 * ratio**2) / _STEP_TRANSITION_M
        return height, slope

    def elevation(self, time_s: float) -> float:
        distance = self._distance(time_s)
        if distance <= 0.0:
            return 0.0
        if distance >= _STEP_TRANSITION_M:
            return self._settings.amplitude_m
        ratio = distance / _STEP_TRANSITION_M
        return self._settings.amplitude_m * (3.0 * ratio**2 - 2.0 * ratio**3)

    def velocity(self, time_s: float) -> float:
        distance = self._distance(time_s)
        if distance <= 0.0 or distance >= _STEP_TRANSITION_M:
            return 0.0
        ratio = distance / _STEP_TRANSITION_M
        slope = self._settings.amplitude_m * (6.0 * ratio - 6.0 * ratio**2) / _STEP_TRANSITION_M
        return slope * self._speed

    def elevation_array(self, time_s: FloatArray) -> FloatArray:
        height, _ = self._smoothstep(self._distance_array(time_s))
        return height

    def velocity_array(self, time_s: FloatArray) -> FloatArray:
        _, slope = self._smoothstep(self._distance_array(time_s))
        return slope * self._speed

    def description(self) -> str:
        return f"step(amplitude={self._settings.amplitude_m:.4f} m)"


class Iso8608Road(_TimeRoadProfile):
    """Stochastic road generated from a discretised ISO 8608 displacement PSD."""

    def __init__(self, settings: RoadProfileSettings) -> None:
        super().__init__(settings)
        self._spatial_frequency, self._amplitude, self._phase = self._build_spectrum(settings)

    @staticmethod
    def _build_spectrum(
        settings: RoadProfileSettings,
    ) -> tuple[FloatArray, FloatArray, FloatArray]:
        frequencies = np.geomspace(
            _ISO_MIN_FREQUENCY, _ISO_MAX_FREQUENCY, num=_ISO_BANDS, dtype=np.float64
        )
        deltas = np.diff(frequencies)
        delta_n = np.empty_like(frequencies)
        delta_n[:-1] = deltas
        delta_n[-1] = deltas[-1]

        ratio = frequencies / _ISO_REFERENCE_FREQUENCY
        psd = settings.roughness_coefficient_m3 * np.power(ratio, -settings.waviness)
        amplitudes = np.sqrt(2.0 * psd * delta_n)

        rng = np.random.default_rng(settings.random_seed)
        phases = rng.uniform(0.0, 2.0 * pi, size=frequencies.size)
        return frequencies, amplitudes, phases

    def _evaluate(self, time_s: FloatArray, *, derivative: bool) -> FloatArray:
        distance = self._distance_array(time_s)
        if distance.size == 0:
            return np.empty(0, dtype=np.float64)

        output = np.empty_like(distance, dtype=np.float64)
        angular = 2.0 * pi * self._spatial_frequency
        coefficient = self._amplitude * angular if derivative else self._amplitude
        phase_scale = self._speed if derivative else 1.0

        for start in range(0, distance.size, _VECTOR_CHUNK):
            stop = min(start + _VECTOR_CHUNK, distance.size)
            phase = np.multiply.outer(distance[start:stop], angular) + self._phase
            if derivative:
                output[start:stop] = phase_scale * (np.cos(phase) @ coefficient)
            else:
                output[start:stop] = np.sin(phase) @ coefficient
        return output

    def elevation(self, time_s: float) -> float:
        distance = self._distance(time_s)
        phase = 2.0 * pi * self._spatial_frequency * distance + self._phase
        return float(np.dot(np.sin(phase), self._amplitude))

    def velocity(self, time_s: float) -> float:
        distance = self._distance(time_s)
        phase = 2.0 * pi * self._spatial_frequency * distance + self._phase
        angular = 2.0 * pi * self._spatial_frequency
        return float(self._speed * np.dot(np.cos(phase), self._amplitude * angular))

    def elevation_array(self, time_s: FloatArray) -> FloatArray:
        return self._evaluate(time_s, derivative=False)

    def velocity_array(self, time_s: FloatArray) -> FloatArray:
        return self._evaluate(time_s, derivative=True)

    def description(self) -> str:
        return (
            f"iso8608(Gd0={self._settings.roughness_coefficient_m3:.3e} m³, "
            f"waviness={self._settings.waviness:.2f}, seed={self._settings.random_seed})"
        )


class RoadProfileFactory:
    """Translate a validated road schema into a concrete profile adapter."""

    _BUILDERS: ClassVar[dict[RoadKind, type[RoadProfile]]] = {
        RoadKind.SMOOTH_BUMP: SmoothBumpRoad,
        RoadKind.SINUSOIDAL: SinusoidalRoad,
        RoadKind.STEP: StepRoad,
        RoadKind.ISO8608: Iso8608Road,
    }

    @classmethod
    def create(cls, settings: RoadProfileSettings) -> RoadProfile:
        builder = cls._BUILDERS.get(settings.kind)
        if builder is None:
            raise RoadProfileError(f"unsupported road kind: {settings.kind!r}")
        try:
            return builder(settings)
        except (ValueError, FloatingPointError) as exc:
            raise RoadProfileError(f"could not construct road profile: {exc}") from exc
