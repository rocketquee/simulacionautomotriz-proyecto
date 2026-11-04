"""Typed exception hierarchy for the suspension simulation platform."""

from __future__ import annotations


class SuspensionSimError(Exception):
    """Base class for every recoverable platform error."""


class ConfigurationError(SuspensionSimError):
    """Raised when configuration files or environment overrides are unusable."""


class DomainValidationError(SuspensionSimError):
    """Raised when a physical or numerical invariant is violated."""


class RoadProfileError(SuspensionSimError):
    """Raised when a road excitation cannot be constructed or evaluated."""


class SolverError(SuspensionSimError):
    """Raised when the ODE integrator fails or returns an invalid trajectory."""


class PersistenceError(SuspensionSimError):
    """Raised when a simulation artifact cannot be written or read."""


class ExperimentError(SuspensionSimError):
    """Raised when a parameter sweep is malformed or partially failed."""
