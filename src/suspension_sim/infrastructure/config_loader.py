"""Configuration composition: YAML base, optional profile, environment overlay.

Precedence is deliberately explicit and identical in every environment::

    built-in defaults  <  config/base.yaml  <  config/profiles/<name>.yaml
                       <  .env / process environment

Environment variables use the ``SUSPENSION_SIM__`` prefix and ``__`` as the
nesting separator, for example::

    SUSPENSION_SIM__SIMULATION__DURATION_S=8.0

Every scalar is parsed with the YAML safe loader, so ``true`` becomes a boolean
and ``1.0e-8`` becomes a float before Pydantic validation runs.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from suspension_sim.core.exceptions import ConfigurationError
from suspension_sim.core.schemas import AppConfig
from suspension_sim.infrastructure.logging import get_logger

_LOGGER = get_logger(__name__)
_ENV_PREFIX = "SUSPENSION_SIM__"
_ENV_FILE = ".env"
_BASE_FILE = "base.yaml"
_PROFILE_DIRECTORY = "profiles"


def find_project_root(start: Path | None = None) -> Path:
    """Walk upwards until a ``pyproject.toml`` marker is found."""

    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return current


def _deep_merge(target: MutableMapping[str, Any], source: Mapping[str, Any]) -> None:
    for key, value in source.items():
        existing = target.get(key)
        if isinstance(existing, MutableMapping) and isinstance(value, Mapping):
            _deep_merge(existing, value)
        else:
            target[key] = value


def _parse_scalar(raw: str) -> Any:
    lowered = raw.strip().lower()
    if lowered in {"", "null", "none", "~"}:
        return None
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError:
        return raw


def apply_environment(
    data: MutableMapping[str, Any],
    environment: Mapping[str, str],
) -> MutableMapping[str, Any]:
    """Overlay ``SUSPENSION_SIM__`` variables onto a configuration mapping."""

    for key, raw_value in environment.items():
        if not key.startswith(_ENV_PREFIX):
            continue
        path = [segment.strip().lower() for segment in key[len(_ENV_PREFIX) :].split("__")]
        if not path or any(not segment for segment in path):
            raise ConfigurationError(f"invalid environment override key: {key}")

        cursor: MutableMapping[str, Any] = data
        for segment in path[:-1]:
            child = cursor.get(segment)
            if child is None:
                child = {}
                cursor[segment] = child
            if not isinstance(child, MutableMapping):
                raise ConfigurationError(
                    f"environment override {key} collides with a scalar value at {segment!r}"
                )
            cursor = child
        cursor[path[-1]] = _parse_scalar(raw_value)
    return data


def _read_yaml(path: Path, *, required: bool) -> dict[str, Any]:
    if not path.is_file():
        if required:
            raise ConfigurationError(f"configuration file not found: {path}")
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"could not read YAML file {path}: {exc}") from exc
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ConfigurationError(f"configuration root must be a mapping: {path}")
    return payload


def _load_dotenv(project_root: Path) -> None:
    dotenv_path = project_root / _ENV_FILE
    if not dotenv_path.is_file():
        return
    try:
        lines = dotenv_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ConfigurationError(f"could not read {dotenv_path}: {exc}") from exc

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        value = raw_value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def load_config(
    path: Path | str | None = None,
    *,
    profile: str | None = None,
    environment: Mapping[str, str] | None = None,
    project_root: Path | None = None,
    load_dotenv: bool = True,
) -> AppConfig:
    """Compose and validate the application configuration."""

    root = project_root or find_project_root()
    if load_dotenv and environment is None:
        _load_dotenv(root)

    if path is None:
        config_path = root / "config" / _BASE_FILE
        data = _read_yaml(config_path, required=False)
    else:
        candidate = Path(path)
        if candidate.is_dir():
            candidate = candidate / _BASE_FILE
        data = _read_yaml(candidate, required=True)

    if profile:
        profile_path = root / "config" / _PROFILE_DIRECTORY / f"{profile}.yaml"
        _deep_merge(data, _read_yaml(profile_path, required=True))

    effective_environment = environment if environment is not None else os.environ
    apply_environment(data, effective_environment)

    try:
        config = AppConfig.model_validate(data)
    except ValidationError as exc:
        raise ConfigurationError(f"invalid configuration:\n{exc}") from exc

    _LOGGER.debug(
        "configuration_loaded",
        extra={
            "path": str(path) if path is not None else str(root / "config" / _BASE_FILE),
            "profile": profile or "base",
        },
    )
    return config


def load_profile(
    name: str,
    *,
    project_root: Path | None = None,
    base_config: AppConfig | None = None,
) -> AppConfig:
    """Load a named vehicle profile merged on top of the base configuration."""

    root = project_root or find_project_root()
    base = base_config or load_config(project_root=root)
    profile_path = root / "config" / _PROFILE_DIRECTORY / f"{name}.yaml"
    overlay = _read_yaml(profile_path, required=True)
    data = base.model_dump(mode="python")
    _deep_merge(data, overlay)
    try:
        return AppConfig.model_validate(data)
    except ValidationError as exc:
        raise ConfigurationError(f"invalid vehicle profile {name!r}:\n{exc}") from exc


def available_profiles(project_root: Path | None = None) -> tuple[str, ...]:
    root = project_root or find_project_root()
    directory = root / "config" / _PROFILE_DIRECTORY
    if not directory.is_dir():
        return ()
    return tuple(sorted(path.stem for path in directory.glob("*.yaml")))
