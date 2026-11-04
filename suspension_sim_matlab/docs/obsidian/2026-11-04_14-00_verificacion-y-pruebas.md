---
tags: [suspension, validacion, pruebas, metricas, python, matlab]
estado: completado
version: 1.0.0
---

# Verificación, Validación Física y Control de Calidad

## Objetivo
Verificar la consistencia dimensional, estabilidad numérica y fidelidad de los modelos matemáticos en ambas plataformas.

## Resultados de Validación Modal
Con los parámetros nominales:
$m_s = 300\text{ kg}, \quad m_u = 40\text{ kg}, \quad k_s = 15000\text{ N/m}, \quad c_s = 1500\text{ N}\cdot\text{s/m}, \quad k_t = 200000\text{ N/m}$

1. **Modo 1 (Carrocería / Bounce):**
   - Fórmula aproximada: $\omega_{n1} \approx \sqrt{\frac{15000}{300}} = 7.071\text{ rad/s} \implies 1.125\text{ Hz}$
   - Autovalor exacto: $\omega_{n1} = 6.877\text{ rad/s} \implies 1.094\text{ Hz}$
   - Error relativo aproximación: $2.8\%$ (< 10% permitido).

2. **Modo 2 (Rueda / Wheel Hop):**
   - Fórmula aproximada: $\omega_{n2} \approx \sqrt{\frac{15000 + 200000}{40}} = 73.314\text{ rad/s} \implies 11.668\text{ Hz}$
   - Autovalor exacto: $\omega_{n2} = 73.407\text{ rad/s} \implies 11.683\text{ Hz}$
   - Error relativo aproximación: $0.13\%$ (< 10% permitido).

Ambos motores (SciPy RK45 y MATLAB ODE45) reproducen con exactitud idéntica estas frecuencias.

## Matriz de Coherencia de Exportación
- **Python:** CSV generado con 10 columnas (`time`, `zs`, `zs_dot`, `zs_ddot`, `zu`, `zu_dot`, `zr`, `susp_deflection`, `tire_force`, `u_control`) con encabezados estandarizados.
- **MATLAB:** Archivos sincronizados `.mat` y `.csv` utilizando `writetable`.
