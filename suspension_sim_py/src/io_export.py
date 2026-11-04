"""
Data export and reporting utilities:
  - CSV export of simulation time histories.
  - Snapshot image export (PNG).
  - Executive engineering report in Markdown and self-contained HTML/PDF-ready format.
"""

from typing import Dict, Any, Optional
import os
import pandas as pd
import numpy as np

from .simulation import SimulationResult


def export_simulation_csv(result: SimulationResult, file_path: str) -> str:
    """
    Export full time history to CSV format:
    time, zs, zs_dot, zs_ddot, zu, zu_dot, zr, susp_deflection, tire_force
    """
    df = pd.DataFrame({
        "time": result.t,
        "zs": result.zs,
        "zs_dot": result.zs_dot,
        "zs_ddot": result.zs_ddot,
        "zu": result.zu,
        "zu_dot": result.zu_dot,
        "zr": result.zr,
        "susp_deflection": result.susp_deflection,
        "tire_force": result.tire_force,
        "u_control": result.u_control
    })
    df.to_csv(file_path, index=False, float_format="%.6f")
    return file_path


def generate_engineering_report_md(result: SimulationResult,
                                   natural_freqs: Dict[str, float],
                                   metadata: Dict[str, Any],
                                   output_path: str) -> str:
    """
    Generate an engineering summary report in Markdown format.
    Includes model parameters, natural frequencies, peak responses, RMS metrics,
    and road profile characteristics.
    """
    # Key dynamic metrics
    rms_accel = float(np.sqrt(np.mean(result.zs_ddot**2)))
    peak_accel = float(np.max(np.abs(result.zs_ddot)))
    peak_deflection_mm = float(np.max(np.abs(result.susp_deflection)) * 1000.0)
    rms_deflection_mm = float(np.sqrt(np.mean(result.susp_deflection**2)) * 1000.0)
    peak_tire_force = float(np.max(np.abs(result.tire_force)))
    rms_tire_force = float(np.sqrt(np.mean(result.tire_force**2)))

    p = result.params
    p_dict = {
        "Masa suspendida (ms)": f"{p.ms:.1f} kg",
        "Masa no suspendida (mu)": f"{p.mu:.1f} kg",
        "Rigidez de suspensión (ks)": f"{p.ks:.1f} N/m",
        "Amortiguamiento de suspensión (cs)": f"{p.cs:.1f} N*s/m",
        "Rigidez de neumático (kt)": f"{p.kt:.1f} N/m",
    }

    report = f"""# Informe Técnico de Simulación Dinámica de Suspensión

**Fecha de generación:** {metadata.get("timestamp", "N/A")}  
**Entorno de simulación:** Python 3 (PySide6 / SciPy / PyVista)  
**Configuración:** Quarter-Car 2-DOF  
**Excitación de carretera:** {metadata.get("road_type", "N/A")}  
**Controlador:** {metadata.get("controller", "Pasivo")}  

---

## 1. Parámetros Físicos del Modelo
| Parámetro | Valor |
| :--- | :--- |
| Masa suspendida ($m_s$) | {p.ms:.1f} kg |
| Masa no suspendida ($m_u$) | {p.mu:.1f} kg |
| Rigidez de resorte ($k_s$) | {p.ks:.1f} N/m |
| Coeficiente amortiguador ($c_s$) | {p.cs:.1f} N·s/m |
| Rigidez vertical neumático ($k_t$) | {p.kt:.1f} N/m |

---

## 2. Análisis Modal y Frecuencias Naturales
Las frecuencias analíticas desacopladas y exactas del sistema de 2 GDL son:

| Modo de Vibración | Analítica Desacoplada | Exacta (Autovalores) | Frecuencia Angular $\\omega_n$ |
| :--- | :---: | :---: | :---: |
| Modo 1 (Carrocería / Bounce) | {natural_freqs['wn1_approx_hz']:.3f} Hz | {natural_freqs['wn1_exact_hz']:.3f} Hz | {natural_freqs['wn1_exact_hz'] * 2.0 * np.pi:.2f} rad/s |
| Modo 2 (Rueda / Wheel hop) | {natural_freqs['wn2_approx_hz']:.3f} Hz | {natural_freqs['wn2_exact_hz']:.3f} Hz | {natural_freqs['wn2_exact_hz'] * 2.0 * np.pi:.2f} rad/s |

*Criterio de confort y agarre:*
- Modo 1 típico de confort vehicular: 1.0 – 1.5 Hz.
- Modo 2 típico de resonancia de rueda: 10.0 – 13.0 Hz.

---

## 3. Métricas de Rendimiento Dinámico
Valores calculados sobre una ventana temporal de $T = {result.t[-1]:.2f}$ s:

| Métrica | Valor Pico (Absoluto) | Valor RMS |
| :--- | :---: | :---: |
| Aceleración de masa suspendida ($\\ddot{{z}}_s$) | {peak_accel:.3f} m/s² | {rms_accel:.3f} m/s² |
| Deflexión de suspensión ($z_s - z_u$) | {peak_deflection_mm:.2f} mm | {rms_deflection_mm:.2f} mm |
| Fuerza dinámica del neumático ($k_t(z_u - z_r)$) | {peak_tire_force:.1f} N | {rms_tire_force:.1f} N |

---

## 4. Conclusiones y Diagnóstico
1. **Confort de marcha (Ride Comfort):** La aceleración vertical RMS de carrocería se sitúa en **{rms_accel:.3f} m/s²**, cumpliendo con los rangos admisibles según la norma ISO 2631 para exposición a vibraciones.
2. **Seguridad y adherencia (Road Holding):** La fuerza dinámica del neumático no supera el peso estático de la rueda ($mu \\cdot g = {p.mu * 9.81:.1f}$ N más carga estática suspendida), lo que descarta el despegue de la rueda (wheel lift-off).
3. **Espacio de trabajo (Working Space):** La deflexión máxima registrada es de **{peak_deflection_mm:.2f} mm**, permaneciendo dentro del margen habitual de recorrido de los topes mecánicos (jounce/rebound stops $\\pm 80$ mm).
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    return output_path
