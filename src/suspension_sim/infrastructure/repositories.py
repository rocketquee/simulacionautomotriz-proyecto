"""Simulation artifact persistence.

Writes are atomic: content is flushed to a temporary file in the destination
directory and then moved with ``os.replace``. A crashed process can therefore
leave a stray temporary file behind, but never a truncated artifact.
"""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from suspension_sim.core.entities import SimulationResult
from suspension_sim.core.exceptions import PersistenceError
from suspension_sim.core.ports import SimulationRepository
from suspension_sim.core.schemas import PersistenceFormat
from suspension_sim.infrastructure.logging import get_logger

_LOGGER = get_logger(__name__)
_SLUG_PATTERN = re.compile(r"[^a-zA-Z0-9_-]+")


def _slugify(label: str) -> str:
    slug = _SLUG_PATTERN.sub("-", label.strip()).strip("-_").lower()
    return slug or "run"


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8", newline="")
        os.replace(temporary, path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise PersistenceError(f"could not write {path}: {exc}") from exc


def _atomic_write_csv(path: Path, rows: list[dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            if not rows:
                return
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise PersistenceError(f"could not write {path}: {exc}") from exc


class FileSystemSimulationRepository(SimulationRepository):
    """Persist trajectories as CSV plus JSON metadata, or as a single JSON file."""

    def __init__(
        self,
        output_dir: Path | str = Path("artifacts"),
        *,
        artifact_format: PersistenceFormat = PersistenceFormat.CSV_JSON,
    ) -> None:
        self._output_dir = Path(output_dir)
        self._format = artifact_format
        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise PersistenceError(f"could not create output directory: {exc}") from exc

    @property
    def output_dir(self) -> Path:
        return self._output_dir

    def save(self, result: SimulationResult) -> Path:
        stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S")
        stem = f"{stamp}_{_slugify(result.label)}_{uuid4().hex[:8]}"
        metadata = result.metadata_dict()
        metadata["generated_at"] = datetime.now(tz=UTC).isoformat()

        if self._format is PersistenceFormat.JSON_ONLY:
            payload = {**metadata, "series": self._series(result)}
            target = self._output_dir / f"{stem}.json"
            _atomic_write_text(target, json.dumps(payload, indent=2, ensure_ascii=False))
            _LOGGER.info("simulation_persisted", extra={"path": str(target)})
            return target

        csv_target = self._output_dir / f"{stem}.csv"
        json_target = self._output_dir / f"{stem}.json"
        rows = list(result.as_rows())
        _atomic_write_csv(csv_target, rows)
        _atomic_write_text(
            json_target,
            json.dumps(metadata, indent=2, ensure_ascii=False),
        )
        _LOGGER.info(
            "simulation_persisted",
            extra={"csv_path": str(csv_target), "metadata_path": str(json_target)},
        )
        return csv_target

    def save_many(self, results: tuple[SimulationResult, ...]) -> tuple[Path, ...]:
        return tuple(self.save(result) for result in results)

    @staticmethod
    def _series(result: SimulationResult) -> dict[str, list[float]]:
        return {
            "time_s": result.time_s.tolist(),
            "sprung_displacement_m": result.sprung_displacement_m.tolist(),
            "unsprung_displacement_m": result.unsprung_displacement_m.tolist(),
            "sprung_velocity_m_s": result.sprung_velocity_m_s.tolist(),
            "unsprung_velocity_m_s": result.unsprung_velocity_m_s.tolist(),
            "sprung_acceleration_m_s2": result.sprung_acceleration_m_s2.tolist(),
            "road_displacement_m": result.road_displacement_m.tolist(),
            "suspension_travel_m": result.suspension_travel_m.tolist(),
            "tire_deflection_m": result.tire_deflection_m.tolist(),
        }


class InMemorySimulationRepository(SimulationRepository):
    """Test double that keeps results in process memory."""

    def __init__(self) -> None:
        self._saved: list[SimulationResult] = []

    @property
    def results(self) -> tuple[SimulationResult, ...]:
        return tuple(self._saved)

    def save(self, result: SimulationResult) -> Path:
        self._saved.append(result)
        return Path(f"/memory/{len(self._saved)}")

    def save_many(self, results: tuple[SimulationResult, ...]) -> tuple[Path, ...]:
        return tuple(self.save(result) for result in results)
