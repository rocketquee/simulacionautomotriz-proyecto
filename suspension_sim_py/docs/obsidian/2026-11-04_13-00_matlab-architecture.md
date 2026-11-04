---
tags: [suspension, arquitectura, matlab, appdesigner]
estado: completado
version: 1.0.0
---

# Arquitectura del Simulador en MATLAB

## Objetivo
Proveer un simulador equivalente en el ecosistema MATLAB que combine una aplicación moderna en App Designer con rutinas modulares en formato `.m` estándar para fácil automatización.

## Qué se hizo
Se diseñó una arquitectura dual:
1. **Modo Gráfico App Designer (`SuspensionApp.mlapp`):** Interfaz rica con controles táctiles/sliders, visualización 3D mediante primitivas `patch`/`surf` con `rotate3d on`, y temporizador interno de refresco dinámico.
2. **Modo Scripts (`run_simulation.m`):** Función de entrada desacoplada que no depende de la GUI, permitiendo barridos de Monte Carlo, optimización de parámetros o ejecución sin entorno gráfico en servidores.

## Decisiones de ingeniería
- **Independencia de Toolboxes comerciales:** El motor numérico utiliza `ode45` nativo y cálculo de autovalores con `eig(K, M)`. No se forzó el uso obligatorio de *Control System Toolbox* ni *Simscape*, asegurando compatibilidad con cualquier instalación base de MATLAB.
- **Visualización 3D:** Implementada sobre un `UIAxes` con iluminación suave, rotación orbital 3D habilitada por defecto y animación paramétrica del resorte helicoidal.

## Archivos afectados
- [[suspension_sim_matlab/SuspensionApp.mlapp]]
- [[suspension_sim_matlab/run_simulation.m]]
- [[suspension_sim_matlab/plot_results.m]]
- [[suspension_sim_matlab/export_report.m]]

## Cómo probarlo
En MATLAB:
```matlab
results = run_simulation([], 'bump');
plot_results(results);
```
