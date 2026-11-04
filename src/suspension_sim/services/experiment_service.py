"""Parallel parameter-sweep orchestration.

Cases are independent, CPU-bound and deterministic, which makes them an ideal
fit for process-level parallelism. Results are always sorted by stiffness and
damping so that reports and regression baselines are stable regardless of
completion order.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from concurrent.futures import Executor, ProcessPoolExecutor
from datetime import UTC, datetime

from suspension_sim.core.entities import ExperimentReport, SweepResult
from suspension_sim.core.exceptions import ExperimentError
from suspension_sim.core.schemas import (
    ExperimentSettings,
    KpiSettings,
    SweepRequest,
)
from suspension_sim.infrastructure.logging import get_logger
from suspension_sim.services.sweep_worker import SweepCase, execute_case

_LOGGER = get_logger(__name__)
ExecutorFactory = Callable[[int], Executor]


class ExperimentService:
    """Build and execute a Cartesian parameter grid."""

    def __init__(
        self,
        settings: ExperimentSettings | None = None,
        kpi_settings: KpiSettings | None = None,
        *,
        executor_factory: ExecutorFactory | None = None,
    ) -> None:
        self._settings = settings or ExperimentSettings()
        self._kpi_settings = kpi_settings or KpiSettings()
        self._executor_factory = executor_factory

    def build_cases(self, request: SweepRequest) -> tuple[SweepCase, ...]:
        cases: list[SweepCase] = []
        for spring_multiplier in request.spring_stiffness_multipliers:
            for damping_multiplier in request.damping_multipliers:
                label = (
                    f"{request.label_prefix}_k{spring_multiplier:.3f}"
                    f"_c{damping_multiplier:.3f}"
                )
                cases.append(
                    SweepCase(
                        label=label,
                        spring_multiplier=spring_multiplier,
                        damping_multiplier=damping_multiplier,
                        base=request.base,
                        simulation=request.simulation,
                        road=request.road,
                        kpi_settings=self._kpi_settings,
                    )
                )
        if not cases:
            raise ExperimentError("sweep request produced no cases")
        return tuple(cases)

    async def run(self, request: SweepRequest) -> ExperimentReport:
        cases = self.build_cases(request)
        loop = asyncio.get_running_loop()
        executor = self._create_executor()
        _LOGGER.info(
            "experiment_started",
            extra={
                "cases": len(cases),
                "max_workers": self._settings.max_workers,
                "road_kind": request.road.kind.value,
            },
        )

        try:
            futures = [
                loop.run_in_executor(executor, execute_case, case) for case in cases
            ]
            results = await asyncio.gather(*futures)
        except Exception as exc:
            raise ExperimentError(f"parameter sweep failed: {exc}") from exc
        finally:
            executor.shutdown(wait=True, cancel_futures=True)

        ordered = tuple(
            sorted(
                results,
                key=lambda item: (
                    item.spring_stiffness_n_per_m,
                    item.damping_coefficient_n_s_per_m,
                ),
            )
        )
        report = ExperimentReport(
            results=ordered,
            generated_at=datetime.now(tz=UTC),
            baseline=request.base,
            simulation=request.simulation,
            road=request.road,
        )
        _LOGGER.info(
            "experiment_completed",
            extra={
                "cases": report.case_count,
                "best_rms_acceleration": report.best_by(
                    "rms_sprung_acceleration_m_s2"
                ).label,
            },
        )
        return report

    def _create_executor(self) -> Executor:
        if self._executor_factory is not None:
            return self._executor_factory(self._settings.max_workers)
        return ProcessPoolExecutor(max_workers=self._settings.max_workers)


def sort_report_results(results: tuple[SweepResult, ...]) -> tuple[SweepResult, ...]:
    """Stable ordering shared by CLI tables and regression snapshots."""

    return tuple(
        sorted(
            results,
            key=lambda item: (
                item.spring_stiffness_n_per_m,
                item.damping_coefficient_n_s_per_m,
            ),
        )
    )
