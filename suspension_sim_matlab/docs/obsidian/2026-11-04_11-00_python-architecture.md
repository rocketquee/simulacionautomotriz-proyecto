---
tags: [suspension, arquitectura, python, pyside6, pyvista]
estado: completado
version: 1.0.0
---

# Arquitectura del Simulador Científico en Python

## Objetivo
Estructurar una aplicación modular, desacoplada y orientada a objetos en Python 3.10+ capaz de mantener una interfaz gráfica fluida a 60 FPS mientras se visualiza en 3D y se grafican variables dinámicas.

## Qué se hizo
Se dividió el sistema en módulos de responsabilidad única:
- `model.py`: Definición física y abstracta (`VehicleModel`).
- `excitation.py`: Generadores matemáticos de carretera.
- `controller.py`: Controladores de amortiguamiento activo/semi-activo.
- `simulation.py`: Resolvedor numérico SciPy y despachador de reproducción multi-hilo en `QThread`.
- `ui_3d.py`: Renderizador 3D basado en PyVistaQt embebido en Qt.
- `ui_plots.py`: Gestor de 4 subplots de alto rendimiento con PyQtGraph.
- `ui_theme.py`: Estilo visual corporativo sobrio (#1F3A5F).
- `io_export.py`: Exportación a CSV e informes ejecutivos Markdown.
- `utils.py`: Procesamiento espectral FFT y validación cruzada.

## Decisiones de ingeniería
- **Separación de hilos (Threading):** La integración ODE se calcula mediante `scipy.integrate.solve_ivp` (método RK45) de forma vectorizada y luego un hilo `QThread` transmite los fotogramas temporizados a la interfaz para garantizar estabilidad absoluta sin congelamiento de la ventana gráfica.
- **Geometría procedural reactiva:** En lugar de cargar archivos CAD estáticos pesados, se generan mallas paramétricas ligeras (resortes helicoidales con `pv.Spline.tube`) que se regeneran y reposicionan en cada frame.

## Archivos afectados
- [[suspension_sim_py/src/model.py]]
- [[suspension_sim_py/src/simulation.py]]
- [[suspension_sim_py/src/ui_main.py]]

## Cómo probarlo
Lanzar la suite completa desde la raíz de Python:
```bash
python main.py
```
Modificar los parámetros en vivo y verificar la ausencia de retrasos perceptibles en la UI.
