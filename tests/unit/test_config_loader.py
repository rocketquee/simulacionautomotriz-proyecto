from __future__ import annotations

from pathlib import Path

import pytest

from suspension_sim.core.exceptions import ConfigurationError
from suspension_sim.core.schemas import RoadKind, SolverKind
from suspension_sim.infrastructure.config_loader import (
    apply_environment,
    available_profiles,
    load_config,
    load_profile,
)


def _project(tmp_path: Path, base_yaml: str) -> Path:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
    config_dir = tmp_path / "config"
    (config_dir / "profiles").mkdir(parents=True)
    (config_dir / "base.yaml").write_text(base_yaml, encoding="utf-8")
    return tmp_path


def test_environment_overlay_is_typed() -> None:
    data: dict[str, object] = {"simulation": {"duration_s": 4.0}}
    apply_environment(
        data,
        {
            "SUSPENSION_SIM__SIMULATION__DURATION_S": "8.5",
            "SUSPENSION_SIM__ROAD__KIND": "iso8608",
            "SUSPENSION_SIM__LOGGING__JSON_OUTPUT": "false",
        },
    )
    simulation = data["simulation"]
    road = data["road"]
    logging = data["logging"]
    assert isinstance(simulation, dict)
    assert isinstance(road, dict)
    assert isinstance(logging, dict)
    assert simulation["duration_s"] == 8.5
    assert road["kind"] == "iso8608"
    assert logging["json_output"] is False


def test_load_config_merges_profile_and_environment(tmp_path: Path) -> None:
    root = _project(
        tmp_path,
        """
suspension:
  spring_stiffness_n_per_m: 25000
simulation:
  duration_s: 4.0
""",
    )
    (root / "config" / "profiles" / "sport.yaml").write_text(
        """
suspension:
  spring_stiffness_n_per_m: 38000
logging:
  level: DEBUG
""",
        encoding="utf-8",
    )

    config = load_config(
        project_root=root,
        profile="sport",
        environment={"SUSPENSION_SIM__SIMULATION__DURATION_S": "2.5"},
        load_dotenv=False,
    )

    assert config.suspension.spring_stiffness_n_per_m == pytest.approx(38_000.0)
    assert config.simulation.duration_s == pytest.approx(2.5)
    assert config.logging.level == "DEBUG"
    assert config.road.kind is RoadKind.SMOOTH_BUMP
    assert config.simulation.solver is SolverKind.DOP853


def test_invalid_configuration_is_wrapped(tmp_path: Path) -> None:
    root = _project(
        tmp_path,
        """
suspension:
  spring_stiffness_n_per_m: -1
""",
    )
    with pytest.raises(ConfigurationError, match="invalid configuration"):
        load_config(project_root=root, environment={}, load_dotenv=False)


def test_missing_explicit_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_config(tmp_path / "missing.yaml", environment={}, load_dotenv=False)


def test_named_profile_loading_and_listing(tmp_path: Path) -> None:
    root = _project(
        tmp_path,
        """
suspension:
  spring_stiffness_n_per_m: 25000
""",
    )
    (root / "config" / "profiles" / "comfort.yaml").write_text(
        "suspension:\n  damping_coefficient_n_s_per_m: 2500\n",
        encoding="utf-8",
    )

    assert available_profiles(root) == ("comfort",)
    profile = load_profile("comfort", project_root=root)
    assert profile.suspension.damping_coefficient_n_s_per_m == pytest.approx(2_500.0)


def test_environment_collision_is_reported() -> None:
    data: dict[str, object] = {"simulation": 3.0}
    with pytest.raises(ConfigurationError, match="collides"):
        apply_environment(data, {"SUSPENSION_SIM__SIMULATION__DURATION_S": "5"})
