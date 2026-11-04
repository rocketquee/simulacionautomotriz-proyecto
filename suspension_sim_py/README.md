# Automotive Suspension Simulator (Quarter-Car 2-DOF) — Python Edition

Simulador profesional de dinámica vertical de suspensión vehicular desarrollado en Python con interfaz gráfica nativa en PySide6, gráficos 2D de alta tasa de refresco con PyQtGraph y renderizado 3D paramétrico e interactivo con PyVista.

---

## 1. Requisitos del Sistema
- **Sistema Operativo:** Windows 10/11, Linux (Ubuntu 20.04+ / Debian 11+), macOS (12+).
- **Python:** 3.10 o superior (probado en 3.10, 3.11 y 3.12).
- **Hardware gráfico:** Compatibilidad con OpenGL 3.2+ (para PyVista / VTK).

---

## 2. Instalación en Entorno Virtual

### Windows (PowerShell / CMD)
```powershell
cd suspension_sim_py
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Linux / macOS (Bash / Zsh)
```bash
cd suspension_sim_py
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Ejecución
Con el entorno virtual activado:
```bash
python main.py
```

---

## 4. Estructura del Código
```text
suspension_sim_py/
├── main.py                     # Punto de entrada de la aplicación
├── requirements.txt           # Dependencias exactas con restricciones de versión
├── README.md                  # Manual de instalación y operación
├── src/
│   ├── __init__.py            # Inicializador de paquete
│   ├── model.py               # VehicleModel (ABC), QuarterCar (2-DOF), HalfCar (4-DOF)
│   ├── excitation.py          # StepBump, Sinusoidal, ISO8608Profile (clases A-E)
│   ├── simulation.py          # Integrador ODE (SciPy solve_ivp RK45) y QThread Runner
│   ├── controller.py          # PassiveSuspension y Skyhook semi-activo
│   ├── ui_main.py             # Ventana principal QMainWindow y panel de control
│   ├── ui_3d.py               # Viewport 3D PyVistaQt con resortes helicoidales dinámicos
│   ├── ui_plots.py            # Cuadrícula 2x2 de gráficas pyqtgraph en tiempo real
│   ├── ui_theme.py            # Paleta de color sobria de ingeniería (#1F3A5F) y QSS
│   ├── io_export.py           # Exportador CSV y generador de informe técnico Markdown
│   └── utils.py               # FFT espectral y estimación experimental de frecuencias
└── docs/
    └── obsidian/              # Documentación técnica estructurada en Markdown/Obsidian
```

---

## 5. Características Principales
1. **Modelo Físico Cuarto de Vehículo (2 GDL):**
   - Masa suspendida $m_s$: 200–600 kg.
   - Masa no suspendida $m_u$: 20–80 kg.
   - Rigidez de resorte $k_s$: 8,000–30,000 N/m.
   - Amortiguador $c_s$: 200–5,000 N·s/m.
   - Rigidez de neumático $k_t$: 100,000–400,000 N/m.
2. **Excitaciones de Carretera:**
   - Resalto suave (Smooth Step Bump).
   - Senoidal continua armónica con amplitud y frecuencia regulables.
   - Perfil estocástico normalizado según **ISO 8608** (Clases A, B, C, D y E) dependiente de la velocidad de avance del vehículo.
3. **Controlador:**
   - Amortiguamiento pasivo nominal.
   - Control semi-activo de **Skyhook (Karnopp)** activable con ajuste de ganancia $c_{sky}$.
4. **Visualización 3D Interactiva:**
   - Cámara libre con rotación, paneo y zoom con ratón.
   - Resorte helicoidal 3D que se deforma volumétricamente en tiempo real según la deflexión $z_s - z_u$.
   - Amortiguador telescópico de dos cuerpos.
   - Rueda con deflexión dinámica sobre plano de rodadura.
5. **Gráficas en Tiempo Real:**
   - Desplazamientos verticales: $z_s(t)$, $z_u(t)$, $z_r(t)$.
   - Aceleración de carrocería $\ddot{z}_s(t)$.
   - Deflexión de trabajo de la suspensión $z_s(t) - z_u(t)$.
   - Fuerza dinámica vertical del neumático $k_t \cdot (z_u - z_r)$.
6. **Exportación e Informes:**
   - Exportación de series temporales en formato CSV.
   - Captura de pantalla de la escena 3D en PNG de alta resolución.
   - Informe técnico consolidado en Markdown con análisis modal analítico vs. numérico.
