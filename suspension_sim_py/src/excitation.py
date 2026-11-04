"""
Road excitation profiles for vehicle suspension simulation.
Supports:
  - StepBump: Smooth rounded step or rectangular bump.
  - Sinusoidal: Harmonic road profile.
  - ISO8608Profile: Stochastic road roughness classes A through E based on ISO 8608 PSD.
"""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class RoadExcitation(ABC):
    """Abstract base class for road height excitations zr(t)."""

    @abstractmethod
    def evaluate(self, t: float) -> float:
        """Return ground vertical position zr (m) at time t (s)."""
        pass

    def __call__(self, t: float) -> float:
        return self.evaluate(t)


class StepBump(RoadExcitation):
    """
    Smooth cosine-ramped step bump or pothole.
    Uses a smooth C1 bump profile to avoid infinite derivative singularities in ODE solvers.
    """

    def __init__(self, amplitude: float = 0.05, start_time: float = 0.5,
                 duration: float = 0.2):
        """
        :param amplitude: Peak bump height (m) (positive=bump, negative=pothole)
        :param start_time: Time when bump begins (s)
        :param duration: Total bump width in seconds
        """
        self.amplitude = float(amplitude)
        self.start_time = float(start_time)
        self.duration = max(float(duration), 1e-4)

    def evaluate(self, t: float) -> float:
        if t < self.start_time or t > (self.start_time + self.duration):
            return 0.0
        # Half-sine bell shape: starts at 0, peaks at amplitude, returns to 0
        phase = (t - self.start_time) / self.duration
        return self.amplitude * np.sin(np.pi * phase)


class Sinusoidal(RoadExcitation):
    """Continuous sinusoidal road profile zr(t) = A * sin(2*pi*f*t)."""

    def __init__(self, amplitude: float = 0.03, frequency: float = 1.5,
                 phase_rad: float = 0.0):
        """
        :param amplitude: Amplitude in meters
        :param frequency: Frequency in Hz
        :param phase_rad: Initial phase in radians
        """
        self.amplitude = float(amplitude)
        self.frequency = float(frequency)
        self.phase_rad = float(phase_rad)

    def evaluate(self, t: float) -> float:
        return self.amplitude * np.sin(2.0 * np.pi * self.frequency * t + self.phase_rad)


class ISO8608Profile(RoadExcitation):
    """
    Standard ISO 8608 Road Roughness Profile.
    Generated via superposition of harmonic components from the power spectral density:
      G_d(n) = G_d(n0) * (n / n0)^(-w)
    where:
      n0 = 0.1 cycles/m
      w = 2 (standard waviness exponent)
    ISO Classes (mean G_d(n0) in 10^-6 m^3):
      Class A (Very good): 16e-6
      Class B (Good):      64e-6
      Class C (Average):   256e-6
      Class D (Poor):      1024e-6
      Class E (Very poor): 4096e-6
    """

    CLASS_PSD_N0 = {
        "A": 16.0e-6,
        "B": 64.0e-6,
        "C": 256.0e-6,
        "D": 1024.0e-6,
        "E": 4096.0e-6
    }

    def __init__(self, road_class: str = "B", vehicle_speed_kmh: float = 60.0,
                 n_harmonics: int = 200, random_seed: int = 42,
                 spatial_freq_min: float = 0.01, spatial_freq_max: float = 3.0):
        """
        :param road_class: 'A', 'B', 'C', 'D', or 'E'
        :param vehicle_speed_kmh: Vehicle forward speed in km/h
        :param n_harmonics: Number of harmonic sinusoids to superimpose
        :param random_seed: Reproducible random phase seed
        """
        self.road_class = road_class.upper()
        if self.road_class not in self.CLASS_PSD_N0:
            self.road_class = "B"

        self.speed_mps = max(float(vehicle_speed_kmh) / 3.6, 0.1)
        self.n0 = 0.1  # cycles / m
        self.w = 2.0   # waviness
        self.gd_n0 = self.CLASS_PSD_N0[self.road_class]

        # Discretize spatial frequency range [n_min, n_max] cycles/m
        self.n_harmonics = n_harmonics
        self.n_vals = np.linspace(spatial_freq_min, spatial_freq_max, n_harmonics)
        self.delta_n = (spatial_freq_max - spatial_freq_min) / n_harmonics

        # Amplitude for each band: A_i = sqrt(2 * G_d(n_i) * delta_n)
        psd_vals = self.gd_n0 * (self.n_vals / self.n0) ** (-self.w)
        self.amplitudes = np.sqrt(2.0 * psd_vals * self.delta_n)

        # Temporal frequencies omega_i = 2 * pi * n_i * V (rad/s)
        self.temporal_omegas = 2.0 * np.pi * self.n_vals * self.speed_mps

        # Random phase angles uniform in [0, 2*pi)
        rng = np.random.default_rng(random_seed)
        self.random_phases = rng.uniform(0.0, 2.0 * np.pi, size=n_harmonics)

    def evaluate(self, t: float) -> float:
        # Sum of sinusoids: sum( A_i * cos(omega_i * t + phi_i) )
        phases = self.temporal_omegas * t + self.random_phases
        return float(np.sum(self.amplitudes * np.cos(phases)))
