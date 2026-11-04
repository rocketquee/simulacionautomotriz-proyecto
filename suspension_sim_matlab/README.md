# Automotive Suspension Simulator (Quarter-Car 2-DOF) — MATLAB Edition

Simulador profesional de dinámica de suspensión vehicular desarrollado para **MATLAB R2023a o superior**, incluyendo una aplicación gráfica completa en **App Designer** (`SuspensionApp.mlapp`) y un flujo de scripts desacoplados para ejecución en consola o entornos CI/CD (`run_simulation.m`).

---

## 1. Requisitos de Software
- **MATLAB:** Versión R2023a, R2023b, R2024a o superior.
- **Toolboxes requeridos:**
  - *MATLAB Base* (incluye `ode45`, `eig`, `exportgraphics`, `writetable`).
  - *No requiere Simscape ni Control System Toolbox obligatoriamente*: la formulación matricial de autovalores y ecuaciones diferenciales está desarrollada de forma nativa para máxima portabilidad.

---

## 2. Instrucciones de Ejecución

### Opción A: Aplicación Gráfica (App Designer)
1. Inicie MATLAB y navegue hasta el directorio:
   ```matlab
   cd('suspension_sim_matlab')
   ```
2. Ejecute la aplicación con el comando:
   ```matlab
   SuspensionApp
   ```
   O haga doble clic en el archivo `SuspensionApp.mlapp` desde el explorador de archivos de MATLAB.
3. Desde la interfaz:
   - Modifique los sliders físicos (`ms`, `mu`, `ks`, `cs`, `kt`).
   - Seleccione el tipo de carretera (Resalto, Senoidal o Perfil estocástico ISO 8608 clases A–E).
   - Active o desactive el amortiguador semi-activo Skyhook.
   - Presione **Iniciar Simulación**.
   - Interactúe con el modelo 3D usando el ratón (rotar, zoom, pan).
   - Use los botones de exportación para generar archivos `.mat`, `.csv` y captura `.png`.

### Opción B: Ejecución por Scripts (Consola o Modo Batch)
Para simulaciones automatizadas o barridos paramétricos sin interfaz gráfica:
```matlab
cd('suspension_sim_matlab')

% 1. Parámetros del cuarto de vehículo
params = struct('ms', 300, 'mu', 40, 'ks', 15000, 'cs', 1500, 'kt', 200000);

% 2. Opciones de carretera
road_opts = struct('amplitude', 0.05, 'start_time', 0.5, 'duration', 0.2);

% 3. Opciones de control
ctrl_opts = struct('active', false, 'sky_gain', 1200);

% 4. Ejecutar simulación
results = run_simulation(params, 'bump', road_opts, ctrl_opts, [0, 5.0]);

% 5. Graficar resultados
plot_results(results);

% 6. Exportar reporte y datos
export_report(results, 'reporte_suspension');
```

---

## 3. Estructura de Archivos
```text
suspension_sim_matlab/
├── SuspensionApp.mlapp         # Aplicación App Designer con UI 3D interactiva y 4 gráficas
├── run_simulation.m           # Motor de integración numérica ODE45
├── quarter_car_model.m        # Ecuaciones diferenciales del modelo de 2 GDL
├── excitation_profiles.m      # Generador de perfiles de carretera (Bump, Seno, ISO 8608)
├── plot_results.m             # Generación de la figura 2x2 con tema sobrio de ingeniería
├── export_report.m            # Exportador de MAT, CSV, PNG e informe Markdown
├── README.md                  # Este manual de usuario y especificación técnica
└── docs/
    └── obsidian/              # Notas técnicas para Obsidian con enlaces wiki
```

---

## 4. Validación de Frecuencias Naturales
Tanto en la aplicación como en `run_simulation.m`, se realiza el cálculo comparativo entre:
- **Aproximación analítica desacoplada:**
  $$\omega_{n1} \approx \sqrt{\frac{k_s}{m_s}}, \quad \omega_{n2} \approx \sqrt{\frac{k_s + k_t}{m_u}}$$
- **Autovalores exactos del sistema matricial:**
  $$\det(K - \omega^2 M) = 0$$
  donde $M = \begin{bmatrix} m_s & 0 \\ 0 & m_u \end{bmatrix}$ y $K = \begin{bmatrix} k_s & -k_s \\ -k_s & k_s + k_t \end{bmatrix}$.

Los valores típicos para los parámetros nominales se sitúan en:
- Modo 1 (carrocería): $\sim 1.09$ Hz.
- Modo 2 (rueda): $\sim 11.68$ Hz.
El error relativo de la aproximación desacoplada respecto a la solución exacta es inferior al 3 %.
