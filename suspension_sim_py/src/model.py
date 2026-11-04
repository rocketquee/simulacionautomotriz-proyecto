"""
Mathematical and physical vehicle suspension models.
Implements VehicleModel abstract base class, QuarterCar (2-DOF), and HalfCar (4-DOF).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Tuple, Any, Optional
import numpy as np


@dataclass
class QuarterCarParams:
    """Quarter-car physical parameter container."""
    ms: float = 300.0        # Sprung mass (kg)
    mu: float = 40.0         # Unsprung mass (kg)
    ks: float = 15000.0      # Suspension stiffness (N/m)
    cs: float = 1500.0       # Suspension damping coefficient (N*s/m)
    kt: float = 200000.0     # Tire vertical stiffness (N/m)


@dataclass
class HalfCarParams:
    """Half-car pitch-bounce physical parameter container."""
    ms: float = 600.0        # Sprung mass (kg)
    iy: float = 800.0        # Pitch moment of inertia about CG (kg*m^2)
    muf: float = 40.0        # Front unsprung mass (kg)
    mur: float = 40.0        # Rear unsprung mass (kg)
    ksf: float = 16000.0     # Front suspension stiffness (N/m)
    ksr: float = 17000.0     # Rear suspension stiffness (N/m)
    csf: float = 1600.0      # Front suspension damping (N*s/m)
    csr: float = 1700.0      # Rear suspension damping (N*s/m)
    ktf: float = 200000.0    # Front tire stiffness (N/m)
    ktr: float = 200000.0    # Rear tire stiffness (N/m)
    a: float = 1.2           # CG distance to front axle (m)
    b: float = 1.4           # CG distance to rear axle (m)


class VehicleModel(ABC):
    """Abstract base class for lumped-parameter vehicle suspension models."""

    @abstractmethod
    def state_derivative(self, t: float, state: np.ndarray, road_input: Any,
                         control_force: float = 0.0) -> np.ndarray:
        """
        Compute dx/dt for the ODE solver.
        :param t: Current time (s)
        :param state: State vector x
        :param road_input: Road profile evaluation function or scalar
        :param control_force: Active/semi-active control force (N)
        :return: State derivative vector dx/dt
        """
        pass

    @abstractmethod
    def compute_natural_frequencies(self) -> Dict[str, float]:
        """Compute theoretical natural frequencies in Hz."""
        pass

    @abstractmethod
    def state_names(self) -> list[str]:
        """Return human-readable names of state variables."""
        pass


class QuarterCar(VehicleModel):
    """
    Quarter-car 2-DOF linear suspension model.

    Equations of motion:
      ms * zs_ddot = -ks * (zs - zu) - cs * (zs_dot - zu_dot) + u_control
      mu * zu_ddot =  ks * (zs - zu) + cs * (zs_dot - zu_dot) - kt * (zu - zr) - u_control

    State vector:
      x[0] = zs     (Sprung mass vertical displacement, m)
      x[1] = zs_dot (Sprung mass vertical velocity, m/s)
      x[2] = zu     (Unsprung mass vertical displacement, m)
      x[3] = zu_dot (Unsprung mass vertical velocity, m/s)
    """

    def __init__(self, params: Optional[QuarterCarParams] = None):
        self.params = params if params is not None else QuarterCarParams()

    def state_names(self) -> list[str]:
        return ["zs", "zs_dot", "zu", "zu_dot"]

    def state_derivative(self, t: float, state: np.ndarray, road_input: Any,
                         control_force: float = 0.0) -> np.ndarray:
        p = self.params
        zs = state[0]
        zs_dot = state[1]
        zu = state[2]
        zu_dot = state[3]

        if callable(road_input):
            zr = float(road_input(t))
        else:
            zr = float(road_input)

        # Passive suspension forces
        susp_spring_force = p.ks * (zs - zu)
        susp_damper_force = p.cs * (zs_dot - zu_dot)
        susp_total_force = susp_spring_force + susp_damper_force + control_force
        tire_force = p.kt * (zu - zr)

        # Accelerations
        zs_ddot = -susp_total_force / p.ms
        zu_ddot = (susp_total_force - tire_force) / p.mu

        return np.array([zs_dot, zs_ddot, zu_dot, zu_ddot], dtype=np.float64)

    def compute_natural_frequencies(self) -> Dict[str, float]:
        """
        Calculate analytical decoupled approximations and exact linear state-space eigenvalues.
        wn1 approx = sqrt(ks / ms) / (2*pi)
        wn2 approx = sqrt((ks + kt) / mu) / (2*pi)
        """
        p = self.params

        # Approximate decoupled natural frequencies (Hz)
        wn1_approx = np.sqrt(p.ks / p.ms) / (2.0 * np.pi)
        wn2_approx = np.sqrt((p.ks + p.kt) / p.mu) / (2.0 * np.pi)

        # Undamped exact system matrix: M * q_ddot + K * q = 0
        m_mat = np.array([[p.ms, 0.0],
                          [0.0, p.mu]], dtype=np.float64)
        k_mat = np.array([[p.ks, -p.ks],
                          [-p.ks, p.ks + p.kt]], dtype=np.float64)

        # Generalized eigenvalue problem: det(K - omega^2 * M) = 0
        minv_k = np.linalg.inv(m_mat) @ k_mat
        eigvals = np.linalg.eigvals(minv_k)
        omegas = np.sort(np.sqrt(np.maximum(eigvals, 0.0)))
        wn_exact = omegas / (2.0 * np.pi)

        return {
            "wn1_approx_hz": float(wn1_approx),
            "wn2_approx_hz": float(wn2_approx),
            "wn1_exact_hz": float(wn_exact[0]),
            "wn2_exact_hz": float(wn_exact[1])
        }

    def compute_derived_metrics(self, state: np.ndarray, road_profile: float,
                                control_force: float = 0.0) -> Dict[str, float]:
        """Compute secondary kinematic and dynamic quantities at a given instant."""
        p = self.params
        zs, zs_dot, zu, zu_dot = state[0], state[1], state[2], state[3]
        zr = road_profile

        susp_deflection = zs - zu
        tire_deflection = zu - zr
        tire_force = p.kt * tire_deflection
        susp_spring_force = p.ks * susp_deflection
        susp_damper_force = p.cs * (zs_dot - zu_dot)
        susp_total_force = susp_spring_force + susp_damper_force + control_force
        zs_ddot = -susp_total_force / p.ms
        zu_ddot = (susp_total_force - tire_force) / p.mu

        return {
            "zs": float(zs),
            "zs_dot": float(zs_dot),
            "zs_ddot": float(zs_ddot),
            "zu": float(zu),
            "zu_dot": float(zu_dot),
            "zu_ddot": float(zu_ddot),
            "zr": float(zr),
            "susp_deflection": float(susp_deflection),
            "tire_force": float(tire_force),
            "control_force": float(control_force)
        }


class HalfCar(VehicleModel):
    """
    Half-car 4-DOF pitch and bounce model (architectural extension).

    Coordinates:
      z: Sprung mass bounce at CG
      theta: Sprung mass pitch angle
      zuf: Front unsprung mass displacement
      zur: Rear unsprung mass displacement
    State vector (8 states): [z, z_dot, theta, theta_dot, zuf, zuf_dot, zur, zur_dot]
    """

    def __init__(self, params: Optional[HalfCarParams] = None):
        self.params = params if params is not None else HalfCarParams()

    def state_names(self) -> list[str]:
        return [
            "z", "z_dot", "theta", "theta_dot",
            "zuf", "zuf_dot", "zur", "zur_dot"
        ]

    def state_derivative(self, t: float, state: np.ndarray, road_input: Any,
                         control_force: float = 0.0) -> np.ndarray:
        p = self.params
        z, z_dot = state[0], state[1]
        theta, theta_dot = state[2], state[3]
        zuf, zuf_dot = state[4], state[5]
        zur, zur_dot = state[6], state[7]

        # Axle road elevations (allow road_input to be tuple/callable)
        if callable(road_input):
            zrf = float(road_input(t, axle="front"))
            zrr = float(road_input(t, axle="rear"))
        elif isinstance(road_input, (tuple, list)):
            zrf, zrr = float(road_input[0]), float(road_input[1])
        else:
            zrf = float(road_input)
            zrr = float(road_input)

        # Kinematics at front and rear suspension attachment points
        zsf = z - p.a * theta
        zsf_dot = z_dot - p.a * theta_dot
        zsr = z + p.b * theta
        zsr_dot = z_dot + p.b * theta_dot

        # Forces
        fsf = p.ksf * (zsf - zuf) + p.csf * (zsf_dot - zuf_dot)
        fsr = p.ksr * (zsr - zur) + p.csr * (zsr_dot - zur_dot)
        ftf = p.ktf * (zuf - zrf)
        ftr = p.ktr * (zur - zrr)

        # Equations of motion
        z_ddot = (-fsf - fsr) / p.ms
        theta_ddot = (fsf * p.a - fsr * p.b) / p.iy
        zuf_ddot = (fsf - ftf) / p.muf
        zur_ddot = (fsr - ftr) / p.mur

        return np.array([
            z_dot, z_ddot, theta_dot, theta_ddot,
            zuf_dot, zuf_ddot, zur_dot, zur_ddot
        ], dtype=np.float64)

    def compute_natural_frequencies(self) -> Dict[str, float]:
        """Computes undamped natural frequencies of the half-car system."""
        p = self.params
        m_mat = np.diag([p.ms, p.iy, p.muf, p.mur])
        k_mat = np.zeros((4, 4), dtype=np.float64)

        k_mat[0, 0] = p.ksf + p.ksr
        k_mat[0, 1] = -p.a * p.ksf + p.b * p.ksr
        k_mat[0, 2] = -p.ksf
        k_mat[0, 3] = -p.ksr

        k_mat[1, 0] = -p.a * p.ksf + p.b * p.ksr
        k_mat[1, 1] = p.a**2 * p.ksf + p.b**2 * p.ksr
        k_mat[1, 2] = p.a * p.ksf
        k_mat[1, 3] = -p.b * p.ksr

        k_mat[2, 0] = -p.ksf
        k_mat[2, 1] = p.a * p.ksf
        k_mat[2, 2] = p.ksf + p.ktf

        k_mat[3, 0] = -p.ksr
        k_mat[3, 1] = -p.b * p.ksr
        k_mat[3, 3] = p.ksr + p.ktr

        minv_k = np.linalg.inv(m_mat) @ k_mat
        eigvals = np.linalg.eigvals(minv_k)
        omegas = np.sort(np.sqrt(np.maximum(np.real(eigvals), 0.0)))
        wn = omegas / (2.0 * np.pi)

        return {
            "bounce_hz": float(wn[0]),
            "pitch_hz": float(wn[1]),
            "front_wheel_hz": float(wn[2]),
            "rear_wheel_hz": float(wn[3])
        }
