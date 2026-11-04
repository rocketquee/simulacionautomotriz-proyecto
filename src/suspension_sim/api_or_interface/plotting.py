"""Headless plotting and animation adapters built on Matplotlib."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from suspension_sim.core.entities import ExperimentReport, SimulationResult
from suspension_sim.core.exceptions import DomainValidationError

_MAX_ANIMATION_FRAMES = 320


def _figure() -> tuple[Figure, np.ndarray]:
    figure, axes = plt.subplots(3, 1, figsize=(11.0, 9.0), sharex=True)
    return figure, np.asarray(axes)


def _style_axis(axis: Axes, title: str, ylabel: str) -> None:
    axis.set_title(title, loc="left", fontsize=10, fontweight="bold")
    axis.set_ylabel(ylabel)
    axis.grid(visible=True, which="major", alpha=0.25)
    axis.legend(loc="upper right", fontsize=8, frameon=False)


def plot_simulation(
    result: SimulationResult,
    output_path: Path | str | None = None,
    *,
    show: bool = False,
) -> Path:
    """Render displacement, acceleration and packaging traces."""

    time = result.time_s
    if time.size < 2:
        raise DomainValidationError("cannot plot a trajectory with fewer than two samples")

    figure, axes = _figure()
    displacement_axis, acceleration_axis, travel_axis = axes

    displacement_axis.plot(time, result.road_displacement_m, label="Road", color="#8c8c8c")
    displacement_axis.plot(
        time, result.unsprung_displacement_m, label="Unsprung mass", color="#1f77b4"
    )
    displacement_axis.plot(
        time, result.sprung_displacement_m, label="Sprung mass", color="#d62728"
    )
    _style_axis(displacement_axis, "Displacement response", "Displacement [m]")

    acceleration_axis.plot(
        time, result.sprung_acceleration_m_s2, color="#d62728", label="Sprung mass"
    )
    _style_axis(acceleration_axis, "Vertical acceleration", "Acceleration [m/s²]")

    travel_axis.plot(time, result.suspension_travel_m, label="Suspension travel", color="#2ca02c")
    travel_axis.plot(time, result.tire_deflection_m, label="Tyre deflection", color="#9467bd")
    _style_axis(travel_axis, "Packaging and road holding", "Deflection [m]")
    travel_axis.set_xlabel("Time [s]")

    kpis = result.kpis
    figure.suptitle(
        f"{result.label} | road={result.road_settings.kind.value} | "
        f"RMS accel={kpis.rms_sprung_acceleration_m_s2:.3f} m/s² | "
        f"peak={kpis.peak_sprung_acceleration_m_s2:.3f} m/s²",
        fontsize=11,
        fontweight="bold",
    )
    figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))

    target = Path(output_path) if output_path is not None else Path(
        f"artifacts/{result.label.replace(' ', '_')}_response.png"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(target, dpi=160)
    if show:
        plt.show()
    plt.close(figure)
    return target


def plot_sweep(
    report: ExperimentReport,
    output_path: Path | str | None = None,
    *,
    metric: str = "rms_sprung_acceleration_m_s2",
    show: bool = False,
) -> Path:
    """Plot a KPI against damping coefficient for every stiffness level."""

    if not report.results:
        raise DomainValidationError("cannot plot an empty experiment report")

    figure, axis = plt.subplots(figsize=(9.5, 5.7))
    stiffness_levels = sorted({item.spring_stiffness_n_per_m for item in report.results})
    for stiffness in stiffness_levels:
        subset = sorted(
            (item for item in report.results if item.spring_stiffness_n_per_m == stiffness),
            key=lambda item: item.damping_coefficient_n_s_per_m,
        )
        axis.plot(
            [item.damping_coefficient_n_s_per_m for item in subset],
            [float(getattr(item.kpis, metric)) for item in subset],
            marker="o",
            linewidth=1.8,
            label=f"k = {stiffness:,.0f} N/m",
        )

    axis.set_xlabel("Damping coefficient [N·s/m]")
    axis.set_ylabel(metric.replace("_", " "))
    axis.set_title(
        f"Parameter sweep | {report.road.kind.value} road | {report.case_count} cases",
        loc="left",
        fontweight="bold",
    )
    axis.grid(visible=True, alpha=0.25)
    axis.legend(frameon=False, fontsize=8)
    figure.tight_layout()

    target = Path(output_path) if output_path is not None else Path("artifacts/sweep.png")
    target.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(target, dpi=160)
    if show:
        plt.show()
    plt.close(figure)
    return target


def animate_suspension(
    result: SimulationResult,
    output_path: Path | str = Path("artifacts/suspension.gif"),
    *,
    fps: int = 30,
) -> Path:
    """Render a two-dimensional quarter-car animation.

    Displacements are exaggerated by a data-driven scale so that millimetre
    motion remains visible. The road, wheel and body are three independently
    updated artists; the spring is redrawn as a zig-zag polyline every frame.
    """

    if result.sample_count < 2:
        raise DomainValidationError("cannot animate a trajectory with fewer than two samples")
    if fps <= 0:
        raise DomainValidationError("fps must be positive")

    stride = max(1, result.sample_count // _MAX_ANIMATION_FRAMES)
    indices = np.arange(0, result.sample_count, stride)
    amplitude = float(
        max(
            np.max(np.abs(result.sprung_displacement_m)),
            np.max(np.abs(result.unsprung_displacement_m)),
            np.max(np.abs(result.road_displacement_m)),
            0.01,
        )
    )
    scale = 0.22 / amplitude

    figure, axis = plt.subplots(figsize=(7.0, 6.0))
    axis.set_xlim(-2.2, 2.2)
    axis.set_ylim(-0.35, 2.0)
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title(result.label, fontsize=11, fontweight="bold")

    body_width = 2.4
    body_height = 0.45
    wheel_radius = 0.32
    body = plt.Rectangle(
        (-body_width / 2.0, 1.05), body_width, body_height, color="#263238", zorder=3
    )
    wheel = plt.Circle((0.0, wheel_radius), wheel_radius, color="#37474f", zorder=3)
    road, = axis.plot([], [], color="#8d6e63", linewidth=4.0, zorder=1)
    spring, = axis.plot([], [], color="#f9a825", linewidth=2.0, zorder=2)
    damper, = axis.plot([], [], color="#1e88e5", linewidth=2.5, zorder=2)
    axis.add_patch(body)
    axis.add_patch(wheel)

    road_x = np.linspace(-2.2, 2.2, 240)

    def update(frame_index: int) -> tuple[object, ...]:
        sample = int(indices[frame_index])
        road_height = float(result.road_displacement_m[sample]) * scale
        body_height_position = 1.05 + float(result.sprung_displacement_m[sample]) * scale
        wheel_center = road_height + wheel_radius + 0.05

        body.set_y(body_height_position)
        wheel.set_center((0.0, wheel_center))

        local_road_x = road_x * 0.6
        road.set_data(local_road_x, road_height + 0.02 * np.sin(local_road_x * 2.4))
        top = body_height_position
        bottom = wheel_center + wheel_radius * 1.45
        spring_y = np.linspace(top, bottom, 13)
        zigzag = np.where(np.arange(spring_y.size) % 2 == 0, -0.13, 0.13)
        zigzag[0] = 0.0
        zigzag[-1] = 0.0
        spring.set_data(zigzag, spring_y)
        damper.set_data([0.38, 0.38], [top, bottom])
        return body, wheel, road, spring, damper

    animation = FuncAnimation(
        figure,
        update,
        frames=indices.size,
        interval=1000.0 / fps,
        blit=False,
        repeat=False,
    )

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix.lower() in {".gif", ".png"}:
        writer = PillowWriter(fps=fps)
    else:
        writer = FFMpegWriter(fps=fps, bitrate=2400)
    animation.save(target, writer=writer, dpi=120)
    plt.close(figure)
    return target
