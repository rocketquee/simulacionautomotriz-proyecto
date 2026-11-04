"""SciPy-backed ODE integrator adapter.

The solver receives only the narrow ``DynamicalSystem`` port, so the same
adapter can integrate the quarter-car model, a future full-car model or any
other state-space plant that honours the contract.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

from suspension_sim.core.entities import SolverOutput
from suspension_sim.core.exceptions import SolverError
from suspension_sim.core.ports import DynamicalSystem, OdeSolver
from suspension_sim.core.schemas import SimulationSettings, SolverKind
from suspension_sim.infrastructure.logging import get_logger

FloatArray = NDArray[np.float64]
_LOGGER = get_logger(__name__)


class ScipyOdeSolver(OdeSolver):
    """Runge-Kutta and implicit integrators exposed through a uniform port."""

    _SUPPORTED = frozenset(kind.value for kind in SolverKind)

    def solve(
        self,
        system: DynamicalSystem,
        settings: SimulationSettings,
        initial_state: FloatArray,
    ) -> SolverOutput:
        if settings.solver.value not in self._SUPPORTED:
            raise SolverError(f"unsupported solver: {settings.solver.value}")

        time_grid = np.linspace(
            0.0,
            settings.duration_s,
            num=settings.sample_count,
            dtype=np.float64,
        )
        options: dict[str, Any] = {}
        if settings.max_step_s is not None:
            options["max_step"] = settings.max_step_s

        try:
            solution = solve_ivp(
                fun=system.derivatives,
                t_span=(0.0, settings.duration_s),
                y0=np.asarray(initial_state, dtype=np.float64),
                method=settings.solver.value,
                t_eval=time_grid,
                rtol=settings.relative_tolerance,
                atol=settings.absolute_tolerance,
                dense_output=False,
                **options,
            )
        except (ValueError, RuntimeError, FloatingPointError) as exc:
            raise SolverError(f"integrator {settings.solver.value} failed: {exc}") from exc

        if not solution.success:
            raise SolverError(
                f"integrator {settings.solver.value} reported failure: {solution.message}"
            )
        if solution.y.shape != (4, time_grid.size):
            raise SolverError(
                "integrator returned an unexpected state shape: "
                f"{solution.y.shape} instead of {(4, time_grid.size)}"
            )
        if not np.all(np.isfinite(solution.y)):
            raise SolverError("integrator produced non-finite states")

        _LOGGER.debug(
            "integration_finished",
            extra={
                "solver": settings.solver.value,
                "samples": int(time_grid.size),
                "function_evaluations": int(solution.nfev),
                "jacobian_evaluations": int(getattr(solution, "njev", 0) or 0),
                "linear_solver_evaluations": int(getattr(solution, "nlu", 0) or 0),
            },
        )

        return SolverOutput(
            time_s=time_grid,
            states=solution.y.T.astype(np.float64, copy=False),
            success=True,
            message=str(solution.message),
            function_evaluations=int(solution.nfev),
            jacobian_evaluations=int(getattr(solution, "njev", 0) or 0),
            linear_solver_evaluations=int(getattr(solution, "nlu", 0) or 0),
        )
