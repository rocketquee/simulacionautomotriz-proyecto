"""Immutable, validated schemas for inputs and application configuration.

Pydantic models are used at the boundary of the system. Once a request has been
validated it is safe to pass it across threads and processes without defensive
copies, because every model is frozen and forbids unknown fields.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SolverKind(StrEnum):
    """Supported SciPy Runge-Kutta / implicit integrators."""

    RK45 = "RK45"
    DOP853 = "DOP853"
    LSODA = "LSODA"
    RADAU = "Radau"


class RoadKind(StrEnum):
    """Road excitation families implemented by the platform."""

    SMOOTH_BUMP = "smooth_bump"
    SINUSOIDAL = "sinusoidal"
    STEP = "step"
    ISO8608 = "iso8608"


class PersistenceFormat(StrEnum):
    """Artifact layout written by the filesystem repository."""

    CSV_JSON = "csv_json"
    JSON_ONLY = "json_only"


class FrozenSchema(BaseModel):
    """Base schema with strict, immutable semantics."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        use_enum_values=False,
    )


class SuspensionParameters(FrozenSchema):
    """Physical parameters of a quarter-car suspension corner.

    The tyre is modelled as a linear spring referenced to the road elevation.
    Damping is linear and acts on the relative velocity across the suspension.
    """

    sprung_mass_kg: float = Field(default=300.0, gt=0.0, le=5_000.0)
    unsprung_mass_kg: float = Field(default=40.0, gt=0.0, le=2_000.0)
    spring_stiffness_n_per_m: float = Field(default=25_000.0, gt=0.0, le=2_000_000.0)
    damping_coefficient_n_s_per_m: float = Field(default=1_800.0, ge=0.0, le=500_000.0)
    tire_stiffness_n_per_m: float = Field(default=190_000.0, gt=0.0, le=5_000_000.0)

    @model_validator(mode="after")
    def _validate_mass_ratio(self) -> Self:
        if self.unsprung_mass_kg >= 0.5 * self.sprung_mass_kg:
            raise ValueError(
                "unsprung_mass_kg must be lower than half of sprung_mass_kg for a "
                "quarter-car model"
            )
        return self

    @property
    def ride_frequency_hz(self) -> float:
        """Undamped body-bounce natural frequency in hertz."""

        from math import pi, sqrt

        return sqrt(self.spring_stiffness_n_per_m / self.sprung_mass_kg) / (2.0 * pi)

    @property
    def damping_ratio(self) -> float:
        """Dimensionless damping ratio of the body-bounce mode."""

        from math import sqrt

        critical = 2.0 * sqrt(self.spring_stiffness_n_per_m * self.sprung_mass_kg)
        if critical <= 0.0:
            return 0.0
        return self.damping_coefficient_n_s_per_m / critical

    @property
    def wheel_hop_frequency_hz(self) -> float:
        """Approximate unsprung wheel-hop frequency in hertz."""

        from math import pi, sqrt

        return sqrt(
            (self.spring_stiffness_n_per_m + self.tire_stiffness_n_per_m)
            / self.unsprung_mass_kg
        ) / (2.0 * pi)

    @property
    def static_tire_load_n(self) -> float:
        """Static vertical load supported by one tyre (g = 9.80665 m/s²)."""

        return (self.sprung_mass_kg + self.unsprung_mass_kg) * 9.80665


class SimulationSettings(FrozenSchema):
    """Temporal grid and integrator tolerances."""

    duration_s: float = Field(default=4.0, gt=0.0, le=3_600.0)
    sample_rate_hz: float = Field(default=1_000.0, gt=0.0, le=50_000.0)
    solver: SolverKind = SolverKind.DOP853
    relative_tolerance: float = Field(default=1.0e-8, gt=0.0, le=1.0)
    absolute_tolerance: float = Field(default=1.0e-10, gt=0.0, le=1.0)
    max_step_s: float | None = Field(default=0.002, gt=0.0, le=1.0)
    initial_sprung_displacement_m: float = Field(default=0.0, ge=-1.0, le=1.0)
    initial_unsprung_displacement_m: float = Field(default=0.0, ge=-1.0, le=1.0)
    initial_sprung_velocity_m_per_s: float = Field(default=0.0, ge=-100.0, le=100.0)
    initial_unsprung_velocity_m_per_s: float = Field(default=0.0, ge=-100.0, le=100.0)

    @model_validator(mode="after")
    def _validate_grid_size(self) -> Self:
        samples = self.duration_s * self.sample_rate_hz
        if samples < 32.0:
            raise ValueError("duration_s * sample_rate_hz must produce at least 32 samples")
        if samples > 5_000_000.0:
            raise ValueError("requested time grid exceeds 5,000,000 samples")
        return self

    @property
    def sample_count(self) -> int:
        return round(self.duration_s * self.sample_rate_hz) + 1

    @property
    def sample_interval_s(self) -> float:
        return 1.0 / self.sample_rate_hz


class RoadProfileSettings(FrozenSchema):
    """Deterministic road excitation configuration.

    ``amplitude_m`` applies to bump, sinusoidal and step profiles. For the
    ISO 8608 stochastic profile, ``roughness_coefficient`` (Gd at n0 = 0.1
    cycles/m, units m³) controls the severity instead.
    """

    kind: RoadKind = RoadKind.SMOOTH_BUMP
    amplitude_m: float = Field(default=0.06, gt=0.0, le=0.5)
    bump_length_m: float = Field(default=1.2, gt=0.0, le=100.0)
    wavelength_m: float = Field(default=6.0, gt=0.1, le=200.0)
    speed_m_per_s: float = Field(default=15.0, gt=0.0, le=100.0)
    start_distance_m: float = Field(default=2.0, ge=0.0, le=10_000.0)
    roughness_coefficient_m3: float = Field(default=256.0e-6, gt=0.0, le=1.0)
    waviness: float = Field(default=2.0, ge=1.5, le=3.5)
    random_seed: int = Field(default=2026, ge=0, le=2**32 - 1)


class KpiSettings(FrozenSchema):
    """Thresholds used to derive comfort and settling indicators."""

    comfort_low_hz: float = Field(default=0.5, gt=0.0, le=20.0)
    comfort_high_hz: float = Field(default=80.0, gt=0.0, le=500.0)
    settling_threshold_ratio: float = Field(default=0.02, gt=0.0, lt=1.0)

    @model_validator(mode="after")
    def _validate_band(self) -> Self:
        if self.comfort_low_hz >= self.comfort_high_hz:
            raise ValueError("comfort_low_hz must be lower than comfort_high_hz")
        return self


class PersistenceSettings(FrozenSchema):
    """Artifact persistence configuration."""

    enabled: bool = True
    output_dir: Path = Field(default=Path("artifacts"))
    format: PersistenceFormat = PersistenceFormat.CSV_JSON

    @field_validator("output_dir")
    @classmethod
    def _validate_output_dir(cls, value: Path) -> Path:
        if not str(value).strip():
            raise ValueError("output_dir cannot be empty")
        return value


class LoggingSettings(FrozenSchema):
    """Structured logging configuration."""

    level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    json_output: bool = True
    include_timestamps: bool = True


class ExperimentSettings(FrozenSchema):
    """Default parameter sweep grid and parallelism."""

    spring_stiffness_multipliers: list[float] = Field(
        default_factory=lambda: [0.75, 1.0, 1.25], min_length=1, max_length=64
    )
    damping_multipliers: list[float] = Field(
        default_factory=lambda: [0.5, 1.0, 1.5], min_length=1, max_length=64
    )
    max_workers: int = Field(default=4, ge=1, le=64)

    @field_validator("spring_stiffness_multipliers", "damping_multipliers")
    @classmethod
    def _validate_multipliers(cls, value: list[float]) -> list[float]:
        if any(multiplier <= 0.0 or multiplier > 10.0 for multiplier in value):
            raise ValueError("every multiplier must be in the interval (0, 10]")
        return value


class AppConfig(FrozenSchema):
    """Root application configuration loaded from YAML plus environment."""

    suspension: SuspensionParameters = Field(default_factory=SuspensionParameters)
    simulation: SimulationSettings = Field(default_factory=SimulationSettings)
    road: RoadProfileSettings = Field(default_factory=RoadProfileSettings)
    kpi: KpiSettings = Field(default_factory=KpiSettings)
    persistence: PersistenceSettings = Field(default_factory=PersistenceSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    experiment: ExperimentSettings = Field(default_factory=ExperimentSettings)


class SimulationRequest(FrozenSchema):
    """A single deterministic simulation request."""

    label: str = Field(default="quarter-car", min_length=1, max_length=120)
    suspension: SuspensionParameters = Field(default_factory=SuspensionParameters)
    simulation: SimulationSettings = Field(default_factory=SimulationSettings)
    road: RoadProfileSettings = Field(default_factory=RoadProfileSettings)


class SweepRequest(FrozenSchema):
    """A Cartesian sweep over spring stiffness and damping multipliers."""

    base: SuspensionParameters = Field(default_factory=SuspensionParameters)
    simulation: SimulationSettings = Field(default_factory=SimulationSettings)
    road: RoadProfileSettings = Field(default_factory=RoadProfileSettings)
    spring_stiffness_multipliers: list[float] = Field(min_length=1, max_length=64)
    damping_multipliers: list[float] = Field(min_length=1, max_length=64)
    label_prefix: str = Field(default="sweep", min_length=1, max_length=40)

    @field_validator("spring_stiffness_multipliers", "damping_multipliers")
    @classmethod
    def _validate_multipliers(cls, value: list[float]) -> list[float]:
        if any(multiplier <= 0.0 or multiplier > 10.0 for multiplier in value):
            raise ValueError("every multiplier must be in the interval (0, 10]")
        return value
