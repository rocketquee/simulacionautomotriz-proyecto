"""Command-line interface for simulation, sweeps and artifact generation."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from suspension_sim.api_or_interface.plotting import (
    animate_suspension,
    plot_simulation,
    plot_sweep,
)
from suspension_sim.core.entities import ExperimentReport
from suspension_sim.core.exceptions import ConfigurationError, SuspensionSimError
from suspension_sim.core.schemas import (
    AppConfig,
    ExperimentSettings,
    RoadKind,
    SimulationRequest,
    SolverKind,
    SweepRequest,
)
from suspension_sim.infrastructure.config_loader import (
    available_profiles,
    load_config,
    load_profile,
)
from suspension_sim.infrastructure.logging import configure_logging
from suspension_sim.infrastructure.repositories import FileSystemSimulationRepository
from suspension_sim.infrastructure.solvers import ScipyOdeSolver
from suspension_sim.services.experiment_service import ExperimentService
from suspension_sim.services.kpi_service import DefaultKpiCalculator
from suspension_sim.services.simulation_service import SimulationService

_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="suspension-sim",
        description="Quarter-car suspension dynamics simulator.",
    )
    parser.add_argument("--config", type=Path, default=None, help="YAML configuration file")
    parser.add_argument("--profile", default=None, help="Vehicle profile under config/profiles")
    parser.add_argument("--log-level", choices=_LOG_LEVELS, default=None)
    parser.add_argument(
        "--json",
        dest="json_output",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Emit structured JSON logs",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate = subparsers.add_parser("simulate", help="Run one deterministic simulation")
    simulate.add_argument("--label", default="quarter-car")
    simulate.add_argument("--road", choices=[kind.value for kind in RoadKind], default=None)
    simulate.add_argument("--duration", type=float, default=None)
    simulate.add_argument("--amplitude", type=float, default=None)
    simulate.add_argument("--speed", type=float, default=None)
    simulate.add_argument("--solver", choices=[kind.value for kind in SolverKind], default=None)
    simulate.add_argument("--output-dir", type=Path, default=None)
    simulate.add_argument("--no-save", action="store_true", default=False)
    simulate.add_argument(
        "--plot",
        nargs="?",
        const="artifacts/response.png",
        default=None,
        metavar="PATH",
    )
    simulate.add_argument(
        "--animate",
        nargs="?",
        const="artifacts/suspension.gif",
        default=None,
        metavar="PATH",
    )

    sweep = subparsers.add_parser("sweep", help="Run a stiffness/damping parameter sweep")
    sweep.add_argument("--spring-multipliers", default=None, help="Comma-separated floats")
    sweep.add_argument("--damping-multipliers", default=None, help="Comma-separated floats")
    sweep.add_argument("--workers", type=int, default=None)
    sweep.add_argument("--output", type=Path, default=Path("artifacts/sweep.csv"))
    sweep.add_argument("--no-save", action="store_true", default=False)
    sweep.add_argument(
        "--plot",
        nargs="?",
        const="artifacts/sweep.png",
        default=None,
        metavar="PATH",
    )

    subparsers.add_parser("profiles", help="List available vehicle profiles")
    return parser


def _replace_config(
    config: AppConfig,
    *,
    simulation: dict[str, Any] | None = None,
    road: dict[str, Any] | None = None,
    persistence: dict[str, Any] | None = None,
    logging: dict[str, Any] | None = None,
) -> AppConfig:
    payload = config.model_dump(mode="python")
    for key, updates in (
        ("simulation", simulation),
        ("road", road),
        ("persistence", persistence),
        ("logging", logging),
    ):
        if updates:
            payload[key].update(updates)
    try:
        return AppConfig.model_validate(payload)
    except ValidationError as exc:
        raise ConfigurationError(f"invalid command-line override:\n{exc}") from exc


def _configure_runtime(
    config: AppConfig,
    args: argparse.Namespace,
) -> AppConfig:
    logging_updates: dict[str, Any] = {}
    if args.log_level is not None:
        logging_updates["level"] = args.log_level
    if args.json_output is not None:
        logging_updates["json_output"] = bool(args.json_output)
    resolved = _replace_config(config, logging=logging_updates or None)
    configure_logging(resolved.logging)
    return resolved


def _build_repository(
    config: AppConfig,
) -> FileSystemSimulationRepository | None:
    if not config.persistence.enabled:
        return None
    return FileSystemSimulationRepository(
        config.persistence.output_dir,
        artifact_format=config.persistence.format,
    )


def _parse_multipliers(raw: str | None, fallback: list[float]) -> list[float]:
    if raw is None:
        return list(fallback)
    try:
        values = [float(part.strip()) for part in raw.split(",") if part.strip()]
    except ValueError as exc:
        raise ConfigurationError(f"invalid multiplier list: {raw!r}") from exc
    if not values:
        raise ConfigurationError("multiplier list cannot be empty")
    return values


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def _run_simulate(config: AppConfig, args: argparse.Namespace) -> int:
    simulation_updates: dict[str, Any] = {}
    if args.duration is not None:
        simulation_updates["duration_s"] = args.duration
    if args.solver is not None:
        simulation_updates["solver"] = SolverKind(args.solver)

    road_updates: dict[str, Any] = {}
    if args.road is not None:
        road_updates["kind"] = RoadKind(args.road)
    if args.amplitude is not None:
        road_updates["amplitude_m"] = args.amplitude
    if args.speed is not None:
        road_updates["speed_m_per_s"] = args.speed

    persistence_updates: dict[str, Any] = {}
    if args.output_dir is not None:
        persistence_updates["output_dir"] = args.output_dir
    if args.no_save:
        persistence_updates["enabled"] = False

    resolved = _replace_config(
        config,
        simulation=simulation_updates or None,
        road=road_updates or None,
        persistence=persistence_updates or None,
    )

    request = SimulationRequest(
        label=args.label,
        suspension=resolved.suspension,
        simulation=resolved.simulation,
        road=resolved.road,
    )
    repository = _build_repository(resolved)

    with SimulationService(
        ScipyOdeSolver(),
        DefaultKpiCalculator(),
        repository=repository,
        kpi_settings=resolved.kpi,
    ) as service:
        result = asyncio.run(service.execute(request))

    artifacts: dict[str, str] = {}
    if args.plot is not None:
        artifacts["plot"] = str(plot_simulation(result, args.plot))
    if args.animate is not None:
        artifacts["animation"] = str(animate_suspension(result, args.animate))

    _print(
        {
            "command": "simulate",
            "label": result.label,
            "samples": result.sample_count,
            "road": resolved.road.kind.value,
            "kpis": result.kpis.as_dict(),
            "artifacts": artifacts,
        }
    )
    return 0


def _write_report_csv(report: ExperimentReport, path: Path) -> None:
    rows = report.to_rows()
    if not rows:
        raise ConfigurationError("experiment report has no rows")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _run_sweep(config: AppConfig, args: argparse.Namespace) -> int:
    spring_multipliers = _parse_multipliers(
        args.spring_multipliers, config.experiment.spring_stiffness_multipliers
    )
    damping_multipliers = _parse_multipliers(
        args.damping_multipliers, config.experiment.damping_multipliers
    )
    workers = args.workers or config.experiment.max_workers
    if workers < 1:
        raise ConfigurationError("--workers must be at least 1")

    request = SweepRequest(
        base=config.suspension,
        simulation=config.simulation,
        road=config.road,
        spring_stiffness_multipliers=spring_multipliers,
        damping_multipliers=damping_multipliers,
    )
    settings = ExperimentSettings(max_workers=workers)
    report = asyncio.run(
        ExperimentService(settings, config.kpi).run(request)
    )

    artifacts: dict[str, str] = {}
    if not args.no_save:
        _write_report_csv(report, args.output)
        artifacts["csv"] = str(args.output)
    if args.plot is not None:
        artifacts["plot"] = str(plot_sweep(report, args.plot))

    best = report.best_by("rms_sprung_acceleration_m_s2")
    _print(
        {
            "command": "sweep",
            "cases": report.case_count,
            "road": config.road.kind.value,
            "best_case": best.label,
            "best_rms_acceleration_m_s2": best.kpis.rms_sprung_acceleration_m_s2,
            "artifacts": artifacts,
        }
    )
    return 0


def _run_profiles(config: AppConfig) -> int:
    names = available_profiles()
    entries: list[dict[str, Any]] = []
    for name in names:
        profile = load_profile(name, base_config=config)
        entries.append(
            {
                "name": name,
                "ride_frequency_hz": profile.suspension.ride_frequency_hz,
                "damping_ratio": profile.suspension.damping_ratio,
                "wheel_hop_frequency_hz": profile.suspension.wheel_hop_frequency_hz,
            }
        )
    _print({"command": "profiles", "profiles": entries})
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config, profile=args.profile)
        config = _configure_runtime(config, args)
        if args.command == "simulate":
            return _run_simulate(config, args)
        if args.command == "sweep":
            return _run_sweep(config, args)
        if args.command == "profiles":
            return _run_profiles(config)
        parser.error(f"unknown command: {args.command}")
    except SuspensionSimError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
