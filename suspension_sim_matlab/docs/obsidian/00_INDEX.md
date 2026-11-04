---
title: Índice de Documentación Técnica - Simuladores de Suspensión
tags: [suspension, simulacion, python, matlab, obsidian]
estado: completado
version: 1.0.0
fecha: 2026-11-04
---

# Centro de Documentación Técnica: Dinámica de Suspensión Vehicular

Bienvenido al índice maestro de especificaciones de ingeniería, formulaciones matemáticas y manuales de arquitectura para los dos simuladores desarrollados:

1. **Simulador Científico en Python** (PySide6, PyQtGraph, PyVista 3D, SciPy).
2. **Simulador en MATLAB** (App Designer, ODE45, Análisis Matricial).

---

## 1. Fundamentos Teóricos y Modelado Físico
- [[2026-11-04_10-00_modelo-quarter-car]]: Ecuaciones de movimiento del sistema 2 GDL, formulación de estados y deducción de frecuencias naturales analíticas vs. exactas.
- [[2026-11-04_10-15_excitaciones-carretera]]: Generación de perfiles de carretera: Bump suave C1, ondas senoidales y síntesis espectral según la norma **ISO 8608** (Clases A a E).
- [[2026-11-04_10-30_controlador-skyhook]]: Ley de control semi-activo de Karnopp (Skyhook) y condición de pasividad.

---

## 2. Arquitectura de Software — Simulador Python
- [[2026-11-04_11-00_python-architecture]]: Diseño de módulos, interfaz abstracta `VehicleModel`, modelo extensible `HalfCar` de 4 GDL.
- [[2026-11-04_11-15_python-simulation-engine]]: Integración numérica en `QThread`, despacho de señales a 60 FPS y control de velocidad temporal.
- [[2026-11-04_11-30_python-ui-3d]]: Geometría procedural interactiva con PyVista/VTK, resortes helicoidales de compresión dinámica y amortiguador coaxial.
- [[2026-11-04_11-45_python-ui-plots]]: Cuadrícula de gráficas en tiempo real con PyQtGraph y estilo visual de ingeniería.
- [[2026-11-04_12-00_python-export]]: Formatos de exportación CSV, capturas PNG y generador de informe técnico en Markdown.

---

## 3. Arquitectura de Software — Simulador MATLAB
- [[2026-11-04_13-00_matlab-architecture]]: Arquitectura desacoplada en MATLAB, compatibilidad con App Designer y soporte para ejecución por línea de comandos/CI.
- [[2026-11-04_13-15_matlab-simulation-engine]]: Función vectorial de estados `quarter_car_model.m` y resolvedor `run_simulation.m` con `ode45`.
- [[2026-11-04_13-30_matlab-app-designer]]: Diseño de interfaz `.mlapp`, vista 3D con parches poligonales y callbacks sincronizados.

---

## 4. Verificación, Validación y Métricas
- [[2026-11-04_14-00_verificacion-y-pruebas]]: Validación modal cruzada (teoría vs. cálculo matricial vs. simulación numérica) y tabla de verificación de calidad de entrega.
