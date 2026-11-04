"""
Main User Interface window for Automotive Suspension Simulator (PySide6).
Consolidates parameter controls, live 3D visualization, 4 real-time plots,
and file export capabilities.
"""

import sys
import os
import datetime
from typing import Optional
import numpy as np

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QSlider, QComboBox, QCheckBox, QPushButton,
    QDoubleSpinBox, QFileDialog, QMessageBox, QStatusBar, QSplitter
)
from PySide6.QtCore import Qt, QTimer

from .model import QuarterCar, QuarterCarParams
from .excitation import StepBump, Sinusoidal, ISO8608Profile, RoadExcitation
from .controller import PassiveSuspension, SkyhookController, SuspensionController
from .simulation import SimulationRunner, SimulationResult
from .ui_3d import Suspension3DViewer
from .ui_plots import SuspensionPlotPanel
from .io_export import export_simulation_csv, generate_engineering_report_md
from .ui_theme import MAIN_STYLESHEET, COLOR_ACCENT


class MainWindow(QMainWindow):
    """Primary GUI Application Window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Dinámica de Suspensión Vehicular — Quarter-Car 2-DOF")
        self.resize(1500, 920)
        self.setStyleSheet(MAIN_STYLESHEET)

        # Simulation engine thread
        self.sim_runner = SimulationRunner(self)
        self.sim_runner.frame_ready.connect(self._on_frame_ready)
        self.sim_runner.finished_sim.connect(self._on_sim_finished)

        # Default model and configuration
        self.current_params = QuarterCarParams()
        self.current_model = QuarterCar(self.current_params)
        self.latest_result: Optional[SimulationResult] = None

        self._build_ui()
        self._update_natural_freq_labels()
        self._prepare_and_run_simulation(auto_start=False)

    def _build_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Main horizontal splitter: Left = Controls, Right = 3D & Plots
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        # Left Control Panel (Fixed Width)
        control_panel = QWidget()
        control_panel.setFixedWidth(380)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(4, 4, 4, 4)
        control_layout.setSpacing(6)

        # 1. Physical Parameters Group
        grp_params = self._create_params_group()
        control_layout.addWidget(grp_params)

        # 2. Excitation & Road Group
        grp_road = self._create_road_group()
        control_layout.addWidget(grp_road)

        # 3. Control Mode Group (Passive / Skyhook)
        grp_ctrl = self._create_control_group()
        control_layout.addWidget(grp_ctrl)

        # 4. Simulation Playback Controls
        grp_sim = self._create_simulation_controls_group()
        control_layout.addWidget(grp_sim)

        # 5. Export and Reporting Group
        grp_export = self._create_export_group()
        control_layout.addWidget(grp_export)

        # 6. Natural Frequencies & Validation Display
        grp_validation = self._create_validation_group()
        control_layout.addWidget(grp_validation)

        control_layout.addStretch()
        main_splitter.addWidget(control_panel)

        # Right Display Area: Splitter Vertical (Top = 3D, Bottom = Plots)
        display_splitter = QSplitter(Qt.Orientation.Vertical)

        # 3D Viewer Widget
        self.viewer_3d = Suspension3DViewer(self)
        display_splitter.addWidget(self.viewer_3d)

        # 4-Plot Panel
        self.plot_panel = SuspensionPlotPanel(self)
        display_splitter.addWidget(self.plot_panel)

        display_splitter.setSizes([450, 450])
        main_splitter.addWidget(display_splitter)
        main_splitter.setSizes([380, 1100])

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo. Configure parámetros y pulse 'Iniciar / Actualizar'.")

    def _create_params_group(self) -> QGroupBox:
        grp = QGroupBox("Parámetros Físicos del Modelo")
        layout = QGridLayout(grp)
        layout.setSpacing(5)

        # Helper to create label + slider + spinbox
        def add_param_row(row, name, min_val, max_val, default_val, unit, step=1.0):
            lbl = QLabel(f"{name} ({unit}):")
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(int(min_val), int(max_val))
            slider.setValue(int(default_val))

            spin = QDoubleSpinBox()
            spin.setRange(float(min_val), float(max_val))
            spin.setSingleStep(step)
            spin.setValue(float(default_val))
            spin.setFixedWidth(75)

            # Sync slider and spin
            slider.valueChanged.connect(lambda val: spin.setValue(float(val)))
            spin.valueChanged.connect(lambda val: slider.setValue(int(val)))
            spin.valueChanged.connect(self._on_param_changed)

            layout.addWidget(lbl, row, 0)
            layout.addWidget(slider, row, 1)
            layout.addWidget(spin, row, 2)
            return spin

        self.spin_ms = add_param_row(0, "Masa suspendida (ms)", 200, 600, 300, "kg")
        self.spin_mu = add_param_row(1, "Masa no suspendida (mu)", 20, 80, 40, "kg")
        self.spin_ks = add_param_row(2, "Rigidez resorte (ks)", 8000, 30000, 15000, "N/m", 500)
        self.spin_cs = add_param_row(3, "Amortiguador (cs)", 200, 5000, 1500, "N·s/m", 50)
        self.spin_kt = add_param_row(4, "Rigidez neumático (kt)", 100000, 400000, 200000, "N/m", 5000)

        btn_default = QPushButton("Restaurar valores por defecto")
        btn_default.clicked.connect(self._reset_defaults)
        layout.addWidget(btn_default, 5, 0, 1, 3)

        return grp

    def _create_road_group(self) -> QGroupBox:
        grp = QGroupBox("Excitación de Carretera")
        layout = QGridLayout(grp)
        layout.setSpacing(5)

        layout.addWidget(QLabel("Tipo de excitación:"), 0, 0)
        self.combo_road_type = QComboBox()
        self.combo_road_type.addItems(["Escalón (Bump suave)", "Senoidal continua", "Perfil Real ISO 8608"])
        self.combo_road_type.currentIndexChanged.connect(self._on_road_type_changed)
        layout.addWidget(self.combo_road_type, 0, 1, 1, 2)

        # Amplitude
        self.lbl_amp = QLabel("Amplitud (m):")
        self.spin_amp = QDoubleSpinBox()
        self.spin_amp.setRange(0.005, 0.20)
        self.spin_amp.setSingleStep(0.005)
        self.spin_amp.setValue(0.05)
        layout.addWidget(self.lbl_amp, 1, 0)
        layout.addWidget(self.spin_amp, 1, 1, 1, 2)

        # Frequency / Duration
        self.lbl_freq = QLabel("Frecuencia (Hz):")
        self.spin_freq = QDoubleSpinBox()
        self.spin_freq.setRange(0.2, 20.0)
        self.spin_freq.setSingleStep(0.2)
        self.spin_freq.setValue(1.5)
        layout.addWidget(self.lbl_freq, 2, 0)
        layout.addWidget(self.spin_freq, 2, 1, 1, 2)

        # ISO Class dropdown
        self.lbl_iso = QLabel("Clase ISO 8608:")
        self.combo_iso_class = QComboBox()
        self.combo_iso_class.addItems(["A (Muy buena)", "B (Buena)", "C (Media)", "D (Mala)", "E (Muy mala)"])
        self.combo_iso_class.setCurrentIndex(1)  # Class B default
        layout.addWidget(self.lbl_iso, 3, 0)
        layout.addWidget(self.combo_iso_class, 3, 1, 1, 2)

        # Vehicle Speed for ISO (km/h)
        self.lbl_speed = QLabel("Velocidad avance (km/h):")
        self.spin_speed = QDoubleSpinBox()
        self.spin_speed.setRange(10.0, 160.0)
        self.spin_speed.setValue(60.0)
        layout.addWidget(self.lbl_speed, 4, 0)
        layout.addWidget(self.spin_speed, 4, 1, 1, 2)

        self._on_road_type_changed(0)
        return grp

    def _create_control_group(self) -> QGroupBox:
        grp = QGroupBox("Estrategia de Control")
        layout = QGridLayout(grp)
        layout.setSpacing(5)

        self.chk_skyhook = QCheckBox("Activar Control Skyhook")
        self.chk_skyhook.setChecked(False)
        self.chk_skyhook.toggled.connect(self._on_control_toggled)
        layout.addWidget(self.chk_skyhook, 0, 0, 1, 3)

        self.lbl_sky_gain = QLabel("Ganancia Skyhook (c_sky):")
        self.spin_sky_gain = QDoubleSpinBox()
        self.spin_sky_gain.setRange(100.0, 8000.0)
        self.spin_sky_gain.setSingleStep(100.0)
        self.spin_sky_gain.setValue(1200.0)
        self.spin_sky_gain.setEnabled(False)
        layout.addWidget(self.lbl_sky_gain, 1, 0)
        layout.addWidget(self.spin_sky_gain, 1, 1, 1, 2)

        return grp

    def _create_simulation_controls_group(self) -> QGroupBox:
        grp = QGroupBox("Control de Simulación")
        layout = QGridLayout(grp)
        layout.setSpacing(5)

        layout.addWidget(QLabel("Duración total (s):"), 0, 0)
        self.spin_duration = QDoubleSpinBox()
        self.spin_duration.setRange(1.0, 20.0)
        self.spin_duration.setValue(5.0)
        layout.addWidget(self.spin_duration, 0, 1)

        layout.addWidget(QLabel("Velocidad repr.:"), 0, 2)
        self.combo_speed = QComboBox()
        self.combo_speed.addItems(["0.25x", "0.5x", "1.0x", "2.0x", "4.0x"])
        self.combo_speed.setCurrentText("1.0x")
        self.combo_speed.currentTextChanged.connect(self._on_speed_changed)
        layout.addWidget(self.combo_speed, 0, 3)

        # Buttons
        self.btn_play = QPushButton("Iniciar / Play")
        self.btn_play.setObjectName("btn_accent")
        self.btn_play.clicked.connect(self._toggle_play_pause)
        layout.addWidget(self.btn_play, 1, 0, 1, 2)

        self.btn_reset = QPushButton("Reiniciar")
        self.btn_reset.clicked.connect(self._on_reset_clicked)
        layout.addWidget(self.btn_reset, 1, 2, 1, 2)

        return grp

    def _create_export_group(self) -> QGroupBox:
        grp = QGroupBox("Exportación e Informes")
        layout = QHBoxLayout(grp)

        self.btn_export_csv = QPushButton("Exportar CSV")
        self.btn_export_csv.clicked.connect(self._export_csv)
        layout.addWidget(self.btn_export_csv)

        self.btn_export_png = QPushButton("Captura PNG")
        self.btn_export_png.clicked.connect(self._export_png)
        layout.addWidget(self.btn_export_png)

        self.btn_export_report = QPushButton("Exportar Informe")
        self.btn_export_report.clicked.connect(self._export_report)
        layout.addWidget(self.btn_export_report)

        return grp

    def _create_validation_group(self) -> QGroupBox:
        grp = QGroupBox("Validación Física (Frecuencias)")
        layout = QVBoxLayout(grp)

        self.lbl_freq_body = QLabel("Carrocería: wn1 = -- Hz")
        self.lbl_freq_wheel = QLabel("Rueda: wn2 = -- Hz")
        self.lbl_freq_exact = QLabel("Exactas (autovalores): wn1=-- Hz, wn2=-- Hz")

        layout.addWidget(self.lbl_freq_body)
        layout.addWidget(self.lbl_freq_wheel)
        layout.addWidget(self.lbl_freq_exact)
        return grp

    # Callback slots
    def _on_param_changed(self):
        self.current_params.ms = self.spin_ms.value()
        self.current_params.mu = self.spin_mu.value()
        self.current_params.ks = self.spin_ks.value()
        self.current_params.cs = self.spin_cs.value()
        self.current_params.kt = self.spin_kt.value()
        self.current_model = QuarterCar(self.current_params)
        self._update_natural_freq_labels()

    def _on_road_type_changed(self, idx: int):
        # 0: StepBump, 1: Sinusoidal, 2: ISO 8608
        if idx == 0:
            self.lbl_amp.setVisible(True)
            self.spin_amp.setVisible(True)
            self.lbl_freq.setText("Duración bump (s):")
            self.spin_freq.setValue(0.2)
            self.lbl_iso.setVisible(False)
            self.combo_iso_class.setVisible(False)
            self.lbl_speed.setVisible(False)
            self.spin_speed.setVisible(False)
        elif idx == 1:
            self.lbl_amp.setVisible(True)
            self.spin_amp.setVisible(True)
            self.lbl_freq.setText("Frecuencia (Hz):")
            self.spin_freq.setValue(1.5)
            self.lbl_iso.setVisible(False)
            self.combo_iso_class.setVisible(False)
            self.lbl_speed.setVisible(False)
            self.spin_speed.setVisible(False)
        else:
            self.lbl_amp.setVisible(False)
            self.spin_amp.setVisible(False)
            self.lbl_freq.setVisible(False)
            self.spin_freq.setVisible(False)
            self.lbl_iso.setVisible(True)
            self.combo_iso_class.setVisible(True)
            self.lbl_speed.setVisible(True)
            self.spin_speed.setVisible(True)

    def _on_control_toggled(self, checked: bool):
        self.spin_sky_gain.setEnabled(checked)

    def _on_speed_changed(self, text: str):
        factor = float(text.replace("x", ""))
        self.sim_runner.set_speed_factor(factor)

    def _reset_defaults(self):
        self.spin_ms.setValue(300.0)
        self.spin_mu.setValue(40.0)
        self.spin_ks.setValue(15000.0)
        self.spin_cs.setValue(1500.0)
        self.spin_kt.setValue(200000.0)
        self.combo_road_type.setCurrentIndex(0)
        self.chk_skyhook.setChecked(False)
        self.spin_duration.setValue(5.0)
        self.combo_speed.setCurrentText("1.0x")
        self.status_bar.showMessage("Valores restaurados a configuración de fábrica.")

    def _update_natural_freq_labels(self):
        freqs = self.current_model.compute_natural_frequencies()
        self.lbl_freq_body.setText(
            f"Carrocería (wn1 desacoplada): {freqs['wn1_approx_hz']:.2f} Hz"
        )
        self.lbl_freq_wheel.setText(
            f"Rueda (wn2 desacoplada): {freqs['wn2_approx_hz']:.2f} Hz"
        )
        self.lbl_freq_exact.setText(
            f"Exactas (eig): wn1 = {freqs['wn1_exact_hz']:.2f} Hz | wn2 = {freqs['wn2_exact_hz']:.2f} Hz"
        )

    def _build_current_road(self) -> RoadExcitation:
        idx = self.combo_road_type.currentIndex()
        if idx == 0:
            return StepBump(
                amplitude=self.spin_amp.value(),
                start_time=0.5,
                duration=self.spin_freq.value()
            )
        elif idx == 1:
            return Sinusoidal(
                amplitude=self.spin_amp.value(),
                frequency=self.spin_freq.value()
            )
        else:
            iso_class_letter = self.combo_iso_class.currentText()[0]
            return ISO8608Profile(
                road_class=iso_class_letter,
                vehicle_speed_kmh=self.spin_speed.value()
            )

    def _build_current_controller(self) -> SuspensionController:
        if self.chk_skyhook.isChecked():
            return SkyhookController(sky_gain=self.spin_sky_gain.value())
        return PassiveSuspension()

    def _prepare_and_run_simulation(self, auto_start: bool = True):
        self._on_param_changed()
        road = self._build_current_road()
        ctrl = self._build_current_controller()
        dur = self.spin_duration.value()
        speed = float(self.combo_speed.currentText().replace("x", ""))

        self.sim_runner.stop()
        self.sim_runner.prepare(self.current_model, road, ctrl, dur, speed)
        self.latest_result = self.sim_runner.get_result()
        self.plot_panel.reset_plots()

        if auto_start:
            self.sim_runner.start()
            self.btn_play.setText("Pausa")
            self.status_bar.showMessage("Simulación en curso...")
        else:
            self.btn_play.setText("Iniciar / Play")
            self.status_bar.showMessage("Simulación calculada y lista para reproducción.")

    def _toggle_play_pause(self):
        if self.sim_runner.isRunning():
            if self.sim_runner.is_paused():
                self.sim_runner.resume()
                self.btn_play.setText("Pausa")
                self.status_bar.showMessage("Simulación reanudada.")
            else:
                self.sim_runner.pause()
                self.btn_play.setText("Reanudar")
                self.status_bar.showMessage("Simulación pausada.")
        else:
            # Need fresh run
            self._prepare_and_run_simulation(auto_start=True)

    def _on_reset_clicked(self):
        self.sim_runner.stop()
        self.plot_panel.reset_plots()
        self.viewer_3d.update_positions(zs=0.0, zu=0.0, zr=0.0)
        self.btn_play.setText("Iniciar / Play")
        self.status_bar.showMessage("Simulación reiniciada.")

    def _on_frame_ready(self, frame: dict):
        # Update 3D visualization
        self.viewer_3d.update_positions(
            zs=frame["zs"],
            zu=frame["zu"],
            zr=frame["zr"]
        )

        # Update 4 plots
        self.plot_panel.update_frame(
            t_history=frame["full_t"],
            zs_hist=frame["full_zs"],
            zu_hist=frame["full_zu"],
            zr_hist=None,
            accel_hist=frame["full_zs_ddot"],
            defl_hist=frame["full_susp_deflection"],
            force_hist=frame["full_tire_force"]
        )

        self.status_bar.showMessage(
            f"Tiempo: {frame['t']:.2f} s | zs: {frame['zs']*1000.0:+.1f} mm | "
            f"zu: {frame['zu']*1000.0:+.1f} mm | Acel: {frame['zs_ddot']:+.2f} m/s²"
        )

    def _on_sim_finished(self, result: SimulationResult):
        self.btn_play.setText("Reiniciar y Ejecutar")
        self.status_bar.showMessage("Simulación completada con éxito.")

    def _export_csv(self):
        if self.latest_result is None:
            QMessageBox.warning(self, "Aviso", "No hay simulación ejecutada para exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Datos de Simulación a CSV",
            "suspension_simulation_results.csv",
            "Archivos CSV (*.csv)"
        )
        if file_path:
            export_simulation_csv(self.latest_result, file_path)
            QMessageBox.information(self, "Exportación Exitosa", f"Archivo guardado en:\n{file_path}")

    def _export_png(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Captura de Pantalla",
            "suspension_3d_snapshot.png",
            "Imágenes PNG (*.png)"
        )
        if file_path:
            self.viewer_3d.plotter.screenshot(file_path)
            QMessageBox.information(self, "Captura Guardada", f"Captura 3D guardada en:\n{file_path}")

    def _export_report(self):
        if self.latest_result is None:
            QMessageBox.warning(self, "Aviso", "No hay simulación para generar informe.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Informe Técnico",
            "informe_suspension.md",
            "Markdown (*.md)"
        )
        if file_path:
            freqs = self.current_model.compute_natural_frequencies()
            metadata = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "road_type": self.combo_road_type.currentText(),
                "controller": "Skyhook Semi-Activo" if self.chk_skyhook.isChecked() else "Pasivo"
            }
            generate_engineering_report_md(self.latest_result, freqs, metadata, file_path)
            QMessageBox.information(self, "Informe Generado", f"Informe técnico guardado en:\n{file_path}")

    def closeEvent(self, event):
        self.sim_runner.stop()
        super().closeEvent(event)
