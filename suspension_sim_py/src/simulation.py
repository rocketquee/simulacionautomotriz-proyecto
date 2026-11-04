"""
Numerical simulation engine for vehicle suspension models.
Integrates ODE using scipy.integrate.solve_ivp (RK45 / Radau) and runs in
a separate QThread to keep the PySide6 UI responsive at 60 FPS.
"""

from typing import Optional, Callable
import time
import numpy as np
from scipy.integrate import solve_ivp
from PySide6.QtCore import QThread, Signal, QObject

from .model import QuarterCar, QuarterCarParams
from .excitation import RoadExcitation
from .controller import SuspensionController, PassiveSuspension


class SimulationResult:
    """Encapsulates full time-series results of a completed or buffered simulation."""

    def __init__(self, time_arr: np.ndarray, state_arr: np.ndarray,
                 road_arr: np.ndarray, control_force_arr: np.ndarray,
                 params: QuarterCarParams):
        self.t = time_arr
        self.zs = state_arr[:, 0]
        self.zs_dot = state_arr[:, 1]
        self.zu = state_arr[:, 2]
        self.zu_dot = state_arr[:, 3]
        self.zr = road_arr
        self.u_control = control_force_arr
        self.params = params

        # Derived dynamic metrics
        self.susp_deflection = self.zs - self.zu
        self.susp_spring_force = params.ks * self.susp_deflection
        self.susp_damper_force = params.cs * (self.zs_dot - self.zu_dot)
        self.susp_total_force = (self.susp_spring_force + self.susp_damper_force +
                                 self.u_control)
        self.zs_ddot = -self.susp_total_force / params.ms

        self.tire_deflection = self.zu - self.zr
        self.tire_force = params.kt * self.tire_deflection
        self.zu_ddot = (self.susp_total_force - self.tire_force) / params.mu

    def __len__(self) -> int:
        return len(self.t)


def solve_quarter_car_ode(model: QuarterCar, road: RoadExcitation,
                          controller: SuspensionController,
                          t_span: tuple[float, float],
                          initial_state: Optional[np.ndarray] = None,
                          max_step: float = 0.002) -> SimulationResult:
    """
    Run complete batch numerical integration using RK45.
    """
    if initial_state is None:
        initial_state = np.zeros(4, dtype=np.float64)

    def ode_fun(t: float, x: np.ndarray) -> np.ndarray:
        zs_dot = x[1]
        zu_dot = x[3]
        u = controller.compute_force(zs_dot, zu_dot, x[0], x[2])
        return model.state_derivative(t, x, road, control_force=u)

    sol = solve_ivp(
        fun=ode_fun,
        t_span=t_span,
        y0=initial_state,
        method="RK45",
        max_step=max_step,
        rtol=1e-6,
        atol=1e-8
    )

    t_eval = sol.t
    states = sol.y.T  # Shape: (N, 4)
    n_points = len(t_eval)

    zr_eval = np.array([road.evaluate(ti) for ti in t_eval], dtype=np.float64)
    ctrl_eval = np.array([
        controller.compute_force(states[i, 1], states[i, 3], states[i, 0], states[i, 2])
        for i in range(n_points)
    ], dtype=np.float64)

    return SimulationResult(t_eval, states, zr_eval, ctrl_eval, model.params)


class SimulationRunner(QThread):
    """
    Thread that streams simulation playback frames at real-time rate (adjusted by speed_factor)
    emitting signals to PySide6 UI without blocking the GUI thread.
    """

    frame_ready = Signal(dict)       # Emits instantaneous frame dictionary
    finished_sim = Signal(object)    # Emits complete SimulationResult when finished

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.model: Optional[QuarterCar] = None
        self.road: Optional[RoadExcitation] = None
        self.controller: SuspensionController = PassiveSuspension()
        self.sim_duration: float = 5.0
        self.speed_factor: float = 1.0

        self._is_running: bool = False
        self._is_paused: bool = False
        self._restart_requested: bool = False
        self._cached_result: Optional[SimulationResult] = None
        self._current_index: int = 0

    def prepare(self, model: QuarterCar, road: RoadExcitation,
                controller: SuspensionController, duration: float,
                speed_factor: float = 1.0):
        """Prepare simulation data offline so streaming playback is 100% fluid."""
        self.model = model
        self.road = road
        self.controller = controller
        self.sim_duration = max(1.0, min(float(duration), 30.0))
        self.speed_factor = max(0.1, min(float(speed_factor), 10.0))
        self._cached_result = solve_quarter_car_ode(
            self.model, self.road, self.controller,
            t_span=(0.0, self.sim_duration)
        )
        self._current_index = 0

    def set_speed_factor(self, factor: float):
        self.speed_factor = max(0.1, min(float(factor), 10.0))

    def get_result(self) -> Optional[SimulationResult]:
        return self._cached_result

    def pause(self):
        self._is_paused = True

    def resume(self):
        self._is_paused = False

    def is_paused(self) -> bool:
        return self._is_paused

    def stop(self):
        self._is_running = False
        self.wait(2000)

    def reset_playback(self):
        self._current_index = 0

    def run(self):
        """Playback loop."""
        if self._cached_result is None:
            return

        self._is_running = True
        res = self._cached_result
        n_points = len(res.t)

        target_dt = 1.0 / 60.0  # target ~60 FPS display updates
        last_wall_time = time.perf_counter()

        while self._is_running and self._current_index < n_points:
            if self._is_paused:
                time.sleep(0.03)
                last_wall_time = time.perf_counter()
                continue

            now = time.perf_counter()
            elapsed_wall = now - last_wall_time
            last_wall_time = now

            # Advance simulation time according to speed_factor
            sim_dt_advance = elapsed_wall * self.speed_factor
            current_sim_time = res.t[self._current_index] + sim_dt_advance

            # Search next index corresponding to current_sim_time
            next_idx = np.searchsorted(res.t, current_sim_time)
            if next_idx >= n_points:
                self._current_index = n_points - 1
            else:
                self._current_index = max(self._current_index + 1, int(next_idx))

            idx = self._current_index

            frame_data = {
                "index": idx,
                "t": float(res.t[idx]),
                "zs": float(res.zs[idx]),
                "zs_dot": float(res.zs_dot[idx]),
                "zs_ddot": float(res.zs_ddot[idx]),
                "zu": float(res.zu[idx]),
                "zu_dot": float(res.zu_dot[idx]),
                "zu_ddot": float(res.zu_ddot[idx]),
                "zr": float(res.zr[idx]),
                "susp_deflection": float(res.susp_deflection[idx]),
                "tire_force": float(res.tire_force[idx]),
                "u_control": float(res.u_control[idx]),
                "total_points": n_points,
                "full_t": res.t[:idx + 1],
                "full_zs": res.zs[:idx + 1],
                "full_zu": res.zu[:idx + 1],
                "full_zs_ddot": res.zs_ddot[:idx + 1],
                "full_susp_deflection": res.susp_deflection[:idx + 1],
                "full_tire_force": res.tire_force[:idx + 1]
            }

            self.frame_ready.emit(frame_data)

            # Sleep to match ~60 FPS update pace
            render_elapsed = time.perf_counter() - now
            sleep_time = max(0.001, target_dt - render_elapsed)
            time.sleep(sleep_time)

            if self._current_index >= n_points - 1:
                break

        self._is_running = False
        self.finished_sim.emit(self._cached_result)
