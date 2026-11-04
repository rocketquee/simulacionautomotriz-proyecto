"""Ride comfort and road-holding KPI computation.

The frequency-weighted RMS is a band-limited approximation of the ISO 2631-1
vertical weighting: a fourth-order Butterworth band-pass between the configured
comfort limits. It is not a certified ISO 2631 implementation, but it removes
the quasi-static DC component and high-frequency numerical noise, which makes
it a consistent comparative indicator across parameter sweeps.
"""

from __future__ import annotations

from math import sqrt

import numpy as np
from numpy.typing import NDArray
from scipy.signal import butter, sosfiltfilt

from suspension_sim.core.entities import KpiSummary
from suspension_sim.core.exceptions import DomainValidationError
from suspension_sim.core.ports import KpiCalculator
from suspension_sim.core.schemas import KpiSettings, SuspensionParameters

FloatArray = NDArray[np.float64]
_MIN_FILTER_SAMPLES = 64


def _validate_series(name: str, values: FloatArray, expected: int) -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise DomainValidationError(f"{name} must be one-dimensional")
    if array.size != expected:
        raise DomainValidationError(
            f"{name} has {array.size} samples but the time grid has {expected}"
        )
    if not np.all(np.isfinite(array)):
        raise DomainValidationError(f"{name} contains non-finite values")
    return array


def frequency_weighted_rms(
    acceleration_m_s2: FloatArray,
    sample_rate_hz: float,
    *,
    low_hz: float,
    high_hz: float,
) -> float:
    """Band-pass RMS used as a comparable comfort indicator."""

    signal = np.asarray(acceleration_m_s2, dtype=np.float64)
    if signal.size < _MIN_FILTER_SAMPLES:
        return float(np.sqrt(np.mean(np.square(signal))))

    nyquist = 0.5 * sample_rate_hz
    upper = min(high_hz, 0.45 * sample_rate_hz)
    lower = max(low_hz, 1.0e-6)
    if lower >= upper or upper >= nyquist:
        return float(np.sqrt(np.mean(np.square(signal))))

    try:
        sos = butter(2, [lower, upper], btype="bandpass", fs=sample_rate_hz, output="sos")
        filtered = sosfiltfilt(sos, signal)
    except ValueError:
        return float(np.sqrt(np.mean(np.square(signal))))
    return float(np.sqrt(np.mean(np.square(filtered))))


class DefaultKpiCalculator(KpiCalculator):
    """Deterministic KPI extractor for quarter-car trajectories."""

    def compute(
        self,
        *,
        time_s: FloatArray,
        sprung_acceleration_m_s2: FloatArray,
        suspension_travel_m: FloatArray,
        tire_deflection_m: FloatArray,
        parameters: SuspensionParameters,
        settings: KpiSettings,
    ) -> KpiSummary:
        time = np.asarray(time_s, dtype=np.float64)
        if time.ndim != 1 or time.size < 2:
            raise DomainValidationError("time_s must contain at least two samples")
        if not np.all(np.isfinite(time)):
            raise DomainValidationError("time_s contains non-finite values")
        if not np.all(np.diff(time) > 0.0):
            raise DomainValidationError("time_s must be strictly increasing")

        count = time.size
        acceleration = _validate_series("sprung_acceleration_m_s2", sprung_acceleration_m_s2, count)
        travel = _validate_series("suspension_travel_m", suspension_travel_m, count)
        deflection = _validate_series("tire_deflection_m", tire_deflection_m, count)

        sample_rate = 1.0 / float(np.median(np.diff(time)))
        rms_acceleration = float(np.sqrt(np.mean(np.square(acceleration))))
        peak_acceleration = float(np.max(np.abs(acceleration)))
        weighted = frequency_weighted_rms(
            acceleration,
            sample_rate,
            low_hz=settings.comfort_low_hz,
            high_hz=settings.comfort_high_hz,
        )
        crest_factor = peak_acceleration / rms_acceleration if rms_acceleration > 1.0e-12 else 0.0

        max_travel = float(np.max(np.abs(travel)))
        max_deflection = float(np.max(np.abs(deflection)))
        dynamic_load = parameters.tire_stiffness_n_per_m * max_deflection
        static_load = parameters.static_tire_load_n
        load_factor = 1.0 + dynamic_load / static_load if static_load > 0.0 else 1.0

        return KpiSummary(
            rms_sprung_acceleration_m_s2=rms_acceleration,
            peak_sprung_acceleration_m_s2=peak_acceleration,
            rms_weighted_acceleration_m_s2=weighted,
            crest_factor=crest_factor,
            max_suspension_travel_m=max_travel,
            max_tire_deflection_m=max_deflection,
            max_tire_load_factor=load_factor,
            settling_time_s=self._settling_time(
                time, acceleration, settings.settling_threshold_ratio
            ),
            ride_frequency_hz=parameters.ride_frequency_hz,
            damping_ratio=parameters.damping_ratio,
            wheel_hop_frequency_hz=parameters.wheel_hop_frequency_hz,
        )

    @staticmethod
    def _settling_time(
        time_s: FloatArray,
        acceleration: FloatArray,
        threshold_ratio: float,
    ) -> float | None:
        peak = float(np.max(np.abs(acceleration)))
        if peak <= 1.0e-12:
            return 0.0
        threshold = threshold_ratio * peak
        above = np.flatnonzero(np.abs(acceleration) > threshold)
        if above.size == 0:
            return 0.0
        last = int(above[-1])
        if last >= time_s.size - 1:
            return None
        return float(time_s[last])


def rms(signal: FloatArray) -> float:
    """Root mean square of a finite signal."""

    values = np.asarray(signal, dtype=np.float64)
    if values.size == 0:
        raise DomainValidationError("cannot compute RMS of an empty signal")
    return float(sqrt(np.mean(np.square(values))))
