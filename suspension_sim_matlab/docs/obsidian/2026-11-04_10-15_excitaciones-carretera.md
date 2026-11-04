---
tags: [suspension, simulacion, python, carreteras, iso8608]
estado: completado
version: 1.0.0
---

# Excitaciones de Carretera y Perfil Estocástico ISO 8608

## Objetivo
Modelar con fidelidad física las irregularidades de la vía que inducen excitación en la base del neumático $z_r(t)$.

## Qué se hizo
Se implementaron tres tipologías complementarias de excitación:
1. **Resalto Suave (Step Bump):** Perfil de medio seno suave de clase $C^1$ para evitar discontinuidades abruptas en los resolvedores Runge-Kutta.
2. **Senoidal Continua (Sinusoidal):** Excitación armónica pura parametrizable en amplitud y frecuencia, ideal para pruebas de resonancia.
3. **Perfil Normalizado ISO 8608:** Síntesis estocástica basada en la Densidad Espectral de Potencia (PSD):
   $$G_d(n) = G_d(n_0) \cdot \left(\frac{n}{n_0}\right)^{-w}$$
   donde $n_0 = 0.1 \text{ ciclos/m}$ y $w = 2.0$.

Se definieron los coeficientes normalizados para las 5 clases de rugosidad:
- **Clase A (Excelente):** $G_d(n_0) = 16 \times 10^{-6} \text{ m}^3$
- **Clase B (Buena):** $G_d(n_0) = 64 \times 10^{-6} \text{ m}^3$
- **Clase C (Aceptable):** $G_d(n_0) = 256 \times 10^{-6} \text{ m}^3$
- **Clase D (Mala):** $G_d(n_0) = 1024 \times 10^{-6} \text{ m}^3$
- **Clase E (Muy mala):** $G_d(n_0) = 4096 \times 10^{-6} \text{ m}^3$

## Decisiones de ingeniería
- **Conversión espacial a temporal:** Dado que la carretera se describe en frecuencia espacial $n$ (ciclos/m), la frecuencia angular temporal percibida por el vehículo a velocidad $V$ (m/s) es $\omega_i = 2 \pi n_i V$.
- **Superposición armónica:** Se discretizan 200 bandas de frecuencia armónica con fases aleatorias uniformes $\phi_i \in [0, 2\pi)$ con semilla reproducible.

## Archivos afectados
- [[suspension_sim_py/src/excitation.py]]
- [[suspension_sim_matlab/excitation_profiles.m]]

## Cómo probarlo
```python
from src.excitation import ISO8608Profile
road = ISO8608Profile(road_class='B', vehicle_speed_kmh=60.0)
z_val = [road.evaluate(t) for t in [0.0, 0.5, 1.0, 2.0]]
print("Valores de perfil:", z_val)
```

## Pendientes / Notas
- La clase queda lista para admitir perfiles de carretera grabados en disco (archivos CSV o CRG) en futuras versiones.
