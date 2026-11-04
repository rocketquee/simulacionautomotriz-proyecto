"""Domain entities produced by the simulation engine.

Entities are lightweight frozen containers. They intentionally avoid framework
dependencies beyond NumPy so they can be persisted, plotted or transmitted
without import cycles.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
from numpy.typing import NDArray

from suspension_sim.core.schemas import (
    RoadProfileSettings,
    SimulationSettings,
    SuspensionParameters,
)

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class SolverOutput:
    """Raw trajectory returned by an ODE integrator."""

    time_s: FloatArray
    states: FloatArray
    success: bool
    message: str
    function_evaluations: int
    jacobian_evaluations: int
    linear_solver_evaluations: int


@dataclass(frozen=True, slots=True)
class KpiSummary:
    """Ride comfort, packaging and road-holding indicators."""

    rms_sprung_acceleration_m_s2: float
    peak_sprung_acceleration_m_s2: float
    rms_weighted_acceleration_m_s2: float
    crest_factor: float
    max_suspension_travel_m: float
    max_tire_deflection_m: float
    max_tire_load_factor: float
    settling_time_s: float | None
    ride_frequency_hz: float
    damping_ratio: float
    wheel_hop_frequency_hz: float

    def as_dict(self) -> dict[str, float | None]:
        return {
            "rms_sprung_acceleration_m_s2": self.rms_sprung_acceleration_m_s2,
            "peak_sprung_acceleration_m_s2": self.peak_sprung_acceleration_m_s2,
            "rms_weighted_acceleration_m_s2": self.rms_weighted_acceleration_m_s2,
            "crest_factor": self.crest_factor,
            "max_suspension_travel_m": self.max_suspension_travel_m,
            "max_tire_deflection_m": self.max_tire_deflection_m,
            "max_tire_load_factor": self.max_tire_load_factor,
            "settling_time_s": self.settling_time_s,
            "ride_frequency_hz": self.ride_frequency_hz,
            "damping_ratio": self.damping_ratio,
            "wheel_hop_frequency_hz": self.wheel_hop_frequency_hz,
        }


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Complete time-domain response of a quarter-car corner."""

    label: str
    time_s: FloatArray
    sprung_displacement_m: FloatArray
    unsprung_displacement_m: FloatArray
    sprung_velocity_m_s: FloatArray
    unsprung_velocity_m_s: FloatArray
    sprung_acceleration_m_s2: FloatArray
    road_displacement_m: FloatArray
    suspension_travel_m: FloatArray
    tire_deflection_m: FloatArray
    kpis: KpiSummary
    parameters: SuspensionParameters
    road_settings: RoadProfileSettings
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def sample_count(self) -> int:
        return int(self.time_s.size)

    def as_rows(self) -> Iterator[dict[str, float]]:
        """Yield one serialisation record per sample without materialising a frame."""

        arrays = (
            self.time_s,
            self.sprung_displacement_m,
            self.unsprung_displacement_m,
            self.sprung_velocity_m_s,
            self.unsprung_velocity_m_s,
            self.sprung_acceleration_m_s2,
            self.road_displacement_m,
            self.suspension_travel_m,
            self.tire_deflection_m,
        )
        keys = (
            "time_s",
            "sprung_displacement_m",
            "unsprung_displacement_m",
            "sprung_velocity_m_s",
            "unsprung_velocity_m_s",
            "sprung_acceleration_m_s2",
            "road_displacement_m",
            "suspension_travel_m",
            "tire_deflection_m",
        )
        for index in range(self.time_s.size):
            yield {key: float(values[index]) for key, values in zip(keys, arrays, strict=True)}

    def metadata_dict(self) -> dict[str, Any]:
        """Build a JSON-safe description of the run."""

        return {
            "label": self.label,
            "sample_count": self.sample_count,
            "duration_s": float(self.time_s[-1]) if self.time_s.size else 0.0,
            "parameters": self.parameters.model_dump(mode="json"),
            "road": self.road_settings.model_dump(mode="json"),
            "kpis": self.kpis.as_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class SweepResult:
    """One point of a parameter sweep."""

    label: str
    spring_stiffness_n_per_m: float
    damping_coefficient_n_s_per_m: float
    kpis: KpiSummary

    @property
    def damping_ratio(self) -> float:
        return self.kpis.damping_ratio

    def as_dict(self) -> dict[str, float | str | None]:
        return {
            "label": self.label,
            "spring_stiffness_n_per_m": self.spring_stiffness_n_per_m,
            "damping_coefficient_n_s_per_m": self.damping_coefficient_n_s_per_m,
            **self.kpis.as_dict(),
        }


@dataclass(frozen=True, slots=True)
class ExperimentReport:
    """Aggregated output of a parameter sweep."""

    results: tuple[SweepResult, ...]
    generated_at: datetime
    baseline: SuspensionParameters
    simulation: SimulationSettings
    road: RoadProfileSettings

    @property
    def case_count(self) -> int:
        return len(self.results)

    def best_by(self, metric: str, *, minimise: bool = True) -> SweepResult:
        """Return the extreme case for a KPI present in ``KpiSummary``."""

        if not self.results:
            raise ValueError("experiment report has no results")
        if not hasattr(self.results[0].kpis, metric):
            raise ValueError(f"unknown KPI metric: {metric}")
        selector = min if minimise else max
        return selector(self.results, key=lambda item: getattr(item.kpis, metric))

    def to_rows(self) -> list[dict[str, float | str | None]]:
        return [result.as_dict() for result in self.results]
