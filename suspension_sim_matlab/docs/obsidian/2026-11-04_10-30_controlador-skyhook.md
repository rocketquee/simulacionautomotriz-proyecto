---
tags: [suspension, control, skyhook, karnopp, python, matlab]
estado: completado
version: 1.0.0
---

# Estrategia de Control Semi-Activo Skyhook

## Objetivo
Implementar la ley de control clásica de Karnopp (Skyhook) para reducción de aceleraciones verticales de carrocería sin degradar el agarre del neumático.

## Qué se hizo
Se modeló el comportamiento del amortiguador semi-activo en el que la fuerza de control emula un amortiguador conectado idealmente a un techo inercial ficticio:
$$F_{sky} = c_{sky} \dot{z}_s$$

Bajo la condición de pasividad energética del elemento semi-activo (el actuador no puede inyectar energía neta al sistema, sólo disiparla):
$$u = \begin{cases} c_{sky} \dot{z}_s & \text{si } \dot{z}_s (\dot{z}_s - \dot{z}_u) \ge 0 \\ 0 & \text{si } \dot{z}_s (\dot{z}_s - \dot{z}_u) < 0 \end{cases}$$

## Decisiones de ingeniería
- Se implementó la interfaz `SuspensionController` con implementaciones concretas `PassiveSuspension` y `SkyhookController`.
- Se añadió un parámetro de ganancia $c_{sky}$ ajustable desde la UI (rango 100 a 8000 N·s/m, nominal 1200 N·s/m).
- Se preserva el punto de extensión para futuros controladores de estado óptimo (LQR / $H_\infty$).

## Archivos afectados
- [[suspension_sim_py/src/controller.py]]
- [[suspension_sim_matlab/run_simulation.m]]

## Cómo probarlo
Comparar la aceleración RMS de carrocería entre modo pasivo ($c_{sky} = 0$) y Skyhook activo ($c_{sky} = 1500$ N·s/m). Debe observarse una reducción de entre 15% y 30% en $\ddot{z}_{s, RMS}$.
