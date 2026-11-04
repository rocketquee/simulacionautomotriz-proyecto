"""Abstract contracts that isolate the domain from its adapters.

Every port is a narrow interface. Infrastructure modules depend on these
abstractions, never the other way around, which keeps the core testable without
SciPy, YAML, filesystem access or a running event loop.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from suspension_sim.core.entities import KpiSummary, SolverOutput
from suspension_sim.core.schemas import (
    KpiSettings,
    SimulationRequest,
    SimulationSettings,
    SuspensionParameters,
)

if TYPE_CHECKING:
    from suspension_sim.core.entities import SimulationResult

FloatArray = NDArray[np.float64]


class RoadProfile(ABC):
    """Vertical road displacement as a function of time."""

    @abstractmethod
    def elevation(self, time_s: float) -> float:
        """Road height in metres at a given instant."""

    @abstractmethod
    def velocity(self, time_s: float) -> float:
        """Vertical road velocity in metres per second at a given instant."""

    @abstractmethod
    def description(self) -> str:
        """Human-readable identifier used in metadata and plots."""

    def elevation_array(self, time_s: FloatArray) -> FloatArray:
        """Vectorised elevation. Concrete profiles may override for speed."""

        return np.fromiter(
            (self.elevation(float(value)) for value in time_s),
            dtype=np.float64,
            count=time_s.size,
        )


class DynamicalSystem(ABC):
    """First-order state-space system consumed by the ODE solver port."""

    @abstractmethod
    def derivatives(self, time_s: float, state: FloatArray) -> FloatArray:
        """Return dx/dt for the current state vector."""


class OdeSolver(ABC):
    """Numerical integrator port."""

    @abstractmethod
    def solve(
        self,
        system: DynamicalSystem,
        settings: SimulationSettings,
        initial_state: FloatArray,
    ) -> SolverOutput:
        """Integrate ``system`` over the grid described by ``settings``."""


class KpiCalculator(ABC):
    """Domain service contract for ride and road-holding indicators."""

    @abstractmethod
    def compute(
        self,
        *,
        time_s: FloatArray,
        sprung_acceleration_m_s2: FloatArray,
        suspension_travel_m: FloatArray,
        tire_deflection_m: FloatArray,
        parameters: SuspensionParameters,
        settings: KpiSettings,
    ) -> KpiSummary:
        """Derive a KPI summary from a solved trajectory."""


class SimulationRepository(ABC):
    """Persistence port for simulation artifacts."""

    @abstractmethod
    def save(self, result: SimulationResult) -> Path:
        """Persist one result and return the path of the primary artifact."""

    @abstractmethod
    def save_many(self, results: tuple[SimulationResult, ...]) -> tuple[Path, ...]:
        """Persist a batch of results."""


class SimulationUseCase(ABC):
    """Asynchronous use case boundary exposed to driving adapters."""

    @abstractmethod
    async def execute(self, request: SimulationRequest) -> SimulationResult:
        """Run a simulation request and return its domain result."""
