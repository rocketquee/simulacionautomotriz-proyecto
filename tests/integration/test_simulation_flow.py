from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from suspension_sim.api_or_interface.cli import main
from suspension_sim.core.schemas import (
    ExperimentSettings,
    KpiSettings,
    SimulationRequest,
    SweepRequest,
)
from suspension_sim.infrastructure.repositories import (
    FileSystemSimulationRepository,
    InMemorySimulationRepository,
)
from suspension_sim.infrastructure.solvers import ScipyOdeSolver
from suspension_sim.services.experiment_service import ExperimentService
from suspension_sim.services.kpi_service import DefaultKpiCalculator
from suspension_sim.services.simulation_service import SimulationService


@pytest.mark.asyncio
async def test_simulation_service_end_to_end(
    simulation_request: SimulationRequest,
    tmp_path: Path,
) -> None:
    repository = FileSystemSimulationRepository(tmp_path)
    with SimulationService(
        ScipyOdeSolver(),
        DefaultKpiCalculator(),
        repository=repository,
        kpi_settings=KpiSettings(),
    ) as service:
        result = await service.execute(simulation_request)

    assert result.label == simulation_request.label
    assert result.sample_count == simulation_request.simulation.sample_count
    assert result.kpis.rms_sprung_acceleration_m_s2 > 0.0
    assert result.kpis.peak_sprung_acceleration_m_s2 >= (
        result.kpis.rms_sprung_acceleration_m_s2
    )
    assert result.metadata["solver"] == "DOP853"
    assert len(list(tmp_path.glob("*.csv"))) == 1
    assert len(list(tmp_path.glob("*.json"))) == 1


@pytest.mark.asyncio
async def test_simulation_service_with_in_memory_repository(
    simulation_request: SimulationRequest,
) -> None:
    repository = InMemorySimulationRepository()
    with SimulationService(
        ScipyOdeSolver(),
        DefaultKpiCalculator(),
        repository=repository,
    ) as service:
        await service.execute(simulation_request)

    assert len(repository.results) == 1


@pytest.mark.asyncio
async def test_experiment_service_returns_sorted_grid(
    simulation_request: SimulationRequest,
) -> None:
    sweep = SweepRequest(
        base=simulation_request.suspension,
        simulation=simulation_request.simulation,
        road=simulation_request.road,
        spring_stiffness_multipliers=[0.9, 1.1],
        damping_multipliers=[0.8, 1.2],
    )
    service = ExperimentService(
        ExperimentSettings(max_workers=2),
        KpiSettings(),
        executor_factory=lambda workers: ThreadPoolExecutor(max_workers=workers),
    )
    report = await service.run(sweep)

    assert report.case_count == 4
    assert report.results[0].spring_stiffness_n_per_m <= report.results[-1].spring_stiffness_n_per_m
    assert all(result.kpis.rms_sprung_acceleration_m_s2 >= 0.0 for result in report.results)
    best = report.best_by("rms_sprung_acceleration_m_s2")
    assert best.label.startswith("sweep_k")


def test_cli_simulate_outputs_json(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(
        [
            "simulate",
            "--no-save",
            "--duration",
            "0.6",
            "--label",
            "cli-smoke",
            "--road",
            "smooth_bump",
        ]
    )
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "simulate"
    assert payload["label"] == "cli-smoke"
    assert payload["samples"] == 601
    assert payload["kpis"]["rms_sprung_acceleration_m_s2"] > 0.0


@pytest.mark.asyncio
async def test_multiple_simulations_run_concurrently(
    simulation_request: SimulationRequest,
) -> None:
    repository = InMemorySimulationRepository()
    with SimulationService(
        ScipyOdeSolver(),
        DefaultKpiCalculator(),
        repository=repository,
        max_workers=2,
    ) as service:
        results = await asyncio.gather(
            service.execute(simulation_request),
            service.execute(simulation_request),
            service.execute(simulation_request),
        )

    assert len(results) == 3
    assert len(repository.results) == 3
