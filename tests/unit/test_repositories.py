from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from suspension_sim.core.entities import KpiSummary, SimulationResult
from suspension_sim.core.schemas import (
    PersistenceFormat,
    RoadProfileSettings,
    SuspensionParameters,
)
from suspension_sim.infrastructure.repositories import (
    FileSystemSimulationRepository,
    InMemorySimulationRepository,
)


def _result() -> SimulationResult:
    time = np.linspace(0.0, 1.0, 11)
    zeros = np.zeros_like(time)
    kpis = KpiSummary(
        rms_sprung_acceleration_m_s2=0.1,
        peak_sprung_acceleration_m_s2=0.2,
        rms_weighted_acceleration_m_s2=0.09,
        crest_factor=2.0,
        max_suspension_travel_m=0.01,
        max_tire_deflection_m=0.002,
        max_tire_load_factor=1.1,
        settling_time_s=0.5,
        ride_frequency_hz=1.45,
        damping_ratio=0.33,
        wheel_hop_frequency_hz=12.0,
    )
    return SimulationResult(
        label="Unit Test Run",
        time_s=time,
        sprung_displacement_m=zeros,
        unsprung_displacement_m=zeros,
        sprung_velocity_m_s=zeros,
        unsprung_velocity_m_s=zeros,
        sprung_acceleration_m_s2=zeros,
        road_displacement_m=zeros,
        suspension_travel_m=zeros,
        tire_deflection_m=zeros,
        kpis=kpis,
        parameters=SuspensionParameters(),
        road_settings=RoadProfileSettings(),
        metadata={"solver": "DOP853"},
    )


def test_csv_and_json_artifacts_are_written(tmp_path: Path) -> None:
    repository = FileSystemSimulationRepository(tmp_path)
    csv_path = repository.save(_result())

    assert csv_path.suffix == ".csv"
    assert csv_path.is_file()
    metadata_path = csv_path.with_suffix(".json")
    assert metadata_path.is_file()

    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 11
    assert rows[0]["time_s"] == "0.0"

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["label"] == "Unit Test Run"
    assert payload["kpis"]["damping_ratio"] == 0.33
    assert payload["parameters"]["sprung_mass_kg"] == 300.0


def test_json_only_artifact_contains_series(tmp_path: Path) -> None:
    repository = FileSystemSimulationRepository(
        tmp_path, artifact_format=PersistenceFormat.JSON_ONLY
    )
    path = repository.save(_result())

    assert path.suffix == ".json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert len(payload["series"]["time_s"]) == 11
    assert payload["series"]["time_s"][-1] == 1.0


def test_save_many_returns_every_path(tmp_path: Path) -> None:
    repository = FileSystemSimulationRepository(tmp_path)
    paths = repository.save_many((_result(), _result()))
    assert len(paths) == 2
    assert all(path.is_file() for path in paths)


def test_in_memory_repository_keeps_results() -> None:
    repository = InMemorySimulationRepository()
    path = repository.save(_result())

    assert path.name == "1"
    assert path.parent.name == "memory"
    assert len(repository.results) == 1
