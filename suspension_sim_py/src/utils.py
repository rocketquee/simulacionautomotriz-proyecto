"""
Auxiliary utilities: physical validation, unit conversions, signal processing.
"""

from typing import Tuple
import numpy as np


def compute_spectral_fft(time_arr: np.ndarray, signal_arr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute single-sided Fast Fourier Transform (FFT) spectrum.
    Returns: (frequencies_hz, amplitudes)
    """
    n = len(time_arr)
    if n < 4:
        return np.array([]), np.array([])

    dt = float(np.mean(np.diff(time_arr)))
    if dt <= 0:
        return np.array([]), np.array([])

    fs = 1.0 / dt
    fft_vals = np.fft.rfft(signal_arr - np.mean(signal_arr))
    freqs = np.fft.rfftfreq(n, d=dt)
    amplitudes = (2.0 / n) * np.abs(fft_vals)
    return freqs, amplitudes


def estimate_dominant_frequencies(time_arr: np.ndarray, zs_arr: np.ndarray,
                                  zu_arr: np.ndarray) -> Tuple[float, float]:
    """
    Estimate experimental natural frequencies from simulated transient responses.
    """
    freqs_s, amp_s = compute_spectral_fft(time_arr, zs_arr)
    freqs_u, amp_u = compute_spectral_fft(time_arr, zu_arr)

    # Focus body search in 0.5 - 4 Hz band
    mask_s = (freqs_s >= 0.4) & (freqs_s <= 4.0)
    if np.any(mask_s):
        idx_peak_s = np.argmax(amp_s[mask_s])
        f_body_measured = freqs_s[mask_s][idx_peak_s]
    else:
        f_body_measured = 0.0

    # Focus wheel search in 6 - 20 Hz band
    mask_u = (freqs_u >= 5.0) & (freqs_u <= 25.0)
    if np.any(mask_u):
        idx_peak_u = np.argmax(amp_u[mask_u])
        f_wheel_measured = freqs_u[mask_u][idx_peak_u]
    else:
        f_wheel_measured = 0.0

    return float(f_body_measured), float(f_wheel_measured)
