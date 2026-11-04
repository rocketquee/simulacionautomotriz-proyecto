"""Asynchronous simulation use case.

CPU-bound integration runs in a worker thread so the event loop remains
responsive for orchestration, progress reporting or an API server. The service
depends only on ports, which makes the adapter set swappable in tests.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import Executor, ThreadPoolExecutor
from os import cpu_count
from types import TracebackType

from suspension_sim.core.entities import SimulationResult
from suspension_sim.core.physics import QuarterCarModel
from suspension_sim.core.ports import (
    KpiCalculator,
    OdeSolver,
    SimulationRepository,
    SimulationUseCase,
)
from suspension_sim.core.schemas import KpiSettings, SimulationRequest
from suspension_sim.infrastructure.logging import get_logger
from suspension_sim.infrastructure.road_profiles import RoadProfileFactory

_LOGGER = get_logger(__name__)


class SimulationService(SimulationUseCase):
    """End-to-end orchestration: road -> plant -> integrator -> KPIs -> storage."""

    def __init__(
        self,
        solver: OdeSolver,
        kpi_calculator: KpiCalculator,
        *,
        repository: SimulationRepository | None = None,
        kpi_settings: KpiSettings | None = None,
        executor: Executor | None = None,
        max_workers: int | None = None,
    ) -> None:
        self._solver = solver
        self._kpi_calculator = kpi_calculator
        self._repository = repository
        self._kpi_settings = kpi_settings or KpiSettings()
        self._owns_executor = executor is None
        workers = max_workers or min(4, max(1, (cpu_count() or 1)))
        self._executor: Executor = executor or ThreadPoolExecutor(
            max_workers=workers,
            thread_name_prefix="suspension-sim",
        )

    async def execute(self, request: SimulationRequest) -> SimulationResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self.run_sync, request)

    def run_sync(self, request: SimulationRequest) -> SimulationResult:
        """Blocking variant used by workers and deterministic tests."""

        road = RoadProfileFactory.create(request.road)
        model = QuarterCarModel(parameters=request.suspension, road_profile=road)
        initial_state = model.initial_state(request.simulation)

        solution = self._solver.solve(model, request.simulation, initial_state)
        time_s = solution.time_s
        states = solution.states
        road_displacement = road.elevation_array(time_s)

        sprung_acceleration, _unsprung_acceleration = model.accelerations(states, road_displacement)
        suspension_travel = model.suspension_travel(states)
        tire_deflection = model.tire_deflection(states, road_displacement)

        kpis = self._kpi_calculator.compute(
            time_s=time_s,
            sprung_acceleration_m_s2=sprung_acceleration,
            suspension_travel_m=suspension_travel,
            tire_deflection_m=tire_deflection,
            parameters=request.suspension,
            settings=self._kpi_settings,
        )

        result = SimulationResult(
            label=request.label,
            time_s=time_s,
            sprung_displacement_m=states[:, 0],
            unsprung_displacement_m=states[:, 1],
            sprung_velocity_m_s=states[:, 2],
            unsprung_velocity_m_s=states[:, 3],
            sprung_acceleration_m_s2=sprung_acceleration,
            road_displacement_m=road_displacement,
            suspension_travel_m=suspension_travel,
            tire_deflection_m=tire_deflection,
            kpis=kpis,
            parameters=request.suspension,
            road_settings=request.road,
            metadata={
                "solver": request.simulation.solver.value,
                "road_profile": road.description(),
                "function_evaluations": solution.function_evaluations,
                "jacobian_evaluations": solution.jacobian_evaluations,
                "linear_solver_evaluations": solution.linear_solver_evaluations,
                "integrator_message": solution.message,
            },
        )

        if self._repository is not None:
            self._repository.save(result)

        _LOGGER.info(
            "simulation_completed",
            extra={
                "label": request.label,
                "samples": result.sample_count,
                "road_kind": request.road.kind.value,
                "rms_acceleration": kpis.rms_sprung_acceleration_m_s2,
                "peak_acceleration": kpis.peak_sprung_acceleration_m_s2,
            },
        )
        return result

    def close(self) -> None:
        if self._owns_executor:
            self._executor.shutdown(wait=True, cancel_futures=False)

    def __enter__(self) -> SimulationService:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    async def __aenter__(self) -> SimulationService:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
