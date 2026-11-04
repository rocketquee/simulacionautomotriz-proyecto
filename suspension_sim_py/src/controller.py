"""
Suspension controllers:
  - PassiveSuspension: baseline passive damper (u = 0).
  - SkyhookController: classic Karnopp skyhook semi-active control law.
Extensible architecture for future controllers (e.g., LQR, H-infinity, MPC).
"""

from abc import ABC, abstractmethod
import numpy as np


class SuspensionController(ABC):
    """Abstract base class for suspension force controllers."""

    @abstractmethod
    def compute_force(self, zs_dot: float, zu_dot: float,
                      zs: float = 0.0, zu: float = 0.0) -> float:
        """
        Compute additional active / semi-active control force u (N).
        Positive force exerts an upward push on sprung mass and downward push on wheel.
        """
        pass


class PassiveSuspension(SuspensionController):
    """Passive suspension: zero active control force."""

    def compute_force(self, zs_dot: float, zu_dot: float,
                      zs: float = 0.0, zu: float = 0.0) -> float:
        return 0.0


class SkyhookController(SuspensionController):
    """
    Karnopp 2-state / continuous Skyhook damper.
    The ideal skyhook damper is attached between the sprung mass and an inertial ceiling:
      F_sky = c_sky * zs_dot

    In a semi-active setup between sprung mass and unsprung mass, the force can only
    dissipate energy (relative velocity (zs_dot - zu_dot) opposite in sign to relative motion):
      If zs_dot * (zs_dot - zu_dot) >= 0:
          u = c_sky * zs_dot
      Else:
          u = 0  (semi-active passivity constraint)

    For pure active skyhook mode, u = c_sky * zs_dot continuously.
    """

    def __init__(self, sky_gain: float = 1200.0, semi_active_mode: bool = True):
        """
        :param sky_gain: Skyhook damping coefficient c_sky (N*s/m)
        :param semi_active_mode: Enforce passivity constraint if True
        """
        self.sky_gain = float(sky_gain)
        self.semi_active_mode = bool(semi_active_mode)

    def compute_force(self, zs_dot: float, zu_dot: float,
                      zs: float = 0.0, zu: float = 0.0) -> float:
        rel_vel = zs_dot - zu_dot
        if self.semi_active_mode:
            # Passivity condition
            if (zs_dot * rel_vel) >= 0.0:
                # Active damping opposing absolute sprung mass velocity
                return float(self.sky_gain * zs_dot)
            else:
                return 0.0
        else:
            return float(self.sky_gain * zs_dot)
