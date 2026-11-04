---
tags: [suspension, simulacion, python, dinamica-vehicular]
estado: completado
version: 1.0.0
---

# Modelo Físico Quarter-Car (2 GDL)

## Objetivo
Establecer la formulación matemática y física rigurosa para el modelo de un cuarto de vehículo de dos grados de libertad con el fin de evaluar confort y adherencia vertical.

## Qué se hizo
Se derivaron las ecuaciones diferenciales ordinarias lineales de segundo orden y se formularon en espacio de estados de primer orden $\dot{x} = f(t, x, z_r, u)$.

Las ecuaciones de movimiento corresponden a:
$$m_s \ddot{z}_s = -k_s(z_s - z_u) - c_s(\dot{z}_s - \dot{z}_u) + u$$
$$m_u \ddot{z}_u = k_s(z_s - z_u) + c_s(\dot{z}_s - \dot{z}_u) - k_t(z_u - z_r) - u$$

Definiendo el vector de estados $x = [z_s, \dot{z}_s, z_u, \dot{z}_u]^T$:
$$\dot{x}_1 = x_2$$
$$\dot{x}_2 = -\frac{k_s}{m_s}(x_1 - x_3) - \frac{c_s}{m_s}(x_2 - x_4) + \frac{u}{m_s}$$
$$\dot{x}_3 = x_4$$
$$\dot{x}_4 = \frac{k_s}{m_u}(x_1 - x_3) + \frac{c_s}{m_u}(x_2 - x_4) - \frac{k_t}{m_u}(x_3 - z_r) - \frac{u}{m_u}$$

## Decisiones de ingeniería
1. **Convención de signos:** $z$ positivo hacia arriba. Una deflexión positiva $z_s - z_u > 0$ genera tensión en el resorte y jounce en la rueda.
2. **Amortiguamiento del neumático:** Se omitió $c_t$ en concordancia con la práctica habitual de dinámica vehicular, dado que el neumático tiene una amortiguación histerética muy baja ($\zeta < 0.02$) comparada con la suspensión principal.
3. **Cálculo de frecuencias naturales:** Se calculan tanto las frecuencias aproximadas desacopladas:
   $$\omega_{n1} \approx \sqrt{\frac{k_s}{m_s}}, \quad \omega_{n2} \approx \sqrt{\frac{k_s + k_t}{m_u}}$$
   como las frecuencias exactas mediante autovalores del problema matricial $\det(K - \omega^2 M) = 0$.

## Archivos afectados
- [[suspension_sim_py/src/model.py]]
- [[suspension_sim_matlab/quarter_car_model.m]]
- [[suspension_sim_matlab/run_simulation.m]]

## Cómo probarlo
Ejecutar la suite matemática en Python:
```bash
python -c "from src.model import QuarterCar; m = QuarterCar(); print(m.compute_natural_frequencies())"
```
Verificar que la frecuencia de carrocería se sitúe entre 1.0 y 1.2 Hz y la de rueda entre 11 y 12.5 Hz.

## Pendientes / Notas
- La interfaz abstracta `VehicleModel` ya deja implementada la clase `HalfCar` para extender a 4 GDL (rebote + cabeceo).
