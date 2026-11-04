"""
Real-time 2D plotting widgets using pyqtgraph.
Four dedicated subplots:
  1. Vertical displacements: zs(t), zu(t), and road zr(t)
  2. Sprung mass vertical acceleration: zs_ddot(t)
  3. Suspension working deflection: zs(t) - zu(t)
  4. Dynamic tire force: kt * (zu(t) - zr(t))
"""

from typing import Dict, Any, Optional
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout
import pyqtgraph as pg

from .ui_theme import (
    COLOR_BG_PANEL, COLOR_BORDER, COLOR_TEXT_MUTED,
    PLOT_COLOR_ZS, PLOT_COLOR_ZU, PLOT_COLOR_ZR,
    PLOT_COLOR_ACCEL, PLOT_COLOR_DEFLECTION, PLOT_COLOR_TIRE_FORCE
)


class SuspensionPlotPanel(QWidget):
    """Grid of 4 live-updating engineering plots."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Global pyqtgraph options for dark engineering aesthetic
        pg.setConfigOption("background", COLOR_BG_PANEL)
        pg.setConfigOption("foreground", COLOR_TEXT_MUTED)
        pg.setConfigOptions(antialias=True)

        layout = QGridLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Plot 1: Displacements (zs, zu, zr)
        self.plot_disp = pg.PlotWidget(title="Desplazamientos Verticales")
        self.plot_disp.showGrid(x=True, y=True, alpha=0.3)
        self.plot_disp.setLabel("left", "Desplazamiento", units="m")
        self.plot_disp.setLabel("bottom", "Tiempo", units="s")
        self.plot_disp.addLegend(offset=(10, 10))

        self.curve_zr = self.plot_disp.plot(
            pen=pg.mkPen(color=PLOT_COLOR_ZR, width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine),
            name="zr (carretera)"
        )
        self.curve_zu = self.plot_disp.plot(
            pen=pg.mkPen(color=PLOT_COLOR_ZU, width=1.8),
            name="zu (rueda)"
        )
        self.curve_zs = self.plot_disp.plot(
            pen=pg.mkPen(color=PLOT_COLOR_ZS, width=2.0),
            name="zs (carrocería)"
        )

        # Plot 2: Body Acceleration (zs_ddot)
        self.plot_accel = pg.PlotWidget(title="Aceleración de Carrocería")
        self.plot_accel.showGrid(x=True, y=True, alpha=0.3)
        self.plot_accel.setLabel("left", "Aceleración", units="m/s²")
        self.plot_accel.setLabel("bottom", "Tiempo", units="s")
        self.curve_accel = self.plot_accel.plot(
            pen=pg.mkPen(color=PLOT_COLOR_ACCEL, width=1.8),
            name="zs_ddot"
        )

        # Plot 3: Suspension Deflection (zs - zu)
        self.plot_defl = pg.PlotWidget(title="Deflexión de Suspensión (zs - zu)")
        self.plot_defl.showGrid(x=True, y=True, alpha=0.3)
        self.plot_defl.setLabel("left", "Deflexión", units="m")
        self.plot_defl.setLabel("bottom", "Tiempo", units="s")
        self.curve_defl = self.plot_defl.plot(
            pen=pg.mkPen(color=PLOT_COLOR_DEFLECTION, width=1.8),
            name="zs - zu"
        )

        # Plot 4: Tire Dynamic Force (kt * (zu - zr))
        self.plot_force = pg.PlotWidget(title="Fuerza Dinámica de Neumático")
        self.plot_force.showGrid(x=True, y=True, alpha=0.3)
        self.plot_force.setLabel("left", "Fuerza", units="N")
        self.plot_force.setLabel("bottom", "Tiempo", units="s")
        self.curve_force = self.plot_force.plot(
            pen=pg.mkPen(color=PLOT_COLOR_TIRE_FORCE, width=1.8),
            name="kt*(zu - zr)"
        )

        # Layout arrangement: 2x2 grid
        layout.addWidget(self.plot_disp, 0, 0)
        layout.addWidget(self.plot_accel, 0, 1)
        layout.addWidget(self.plot_defl, 1, 0)
        layout.addWidget(self.plot_force, 1, 1)

    def update_frame(self, t_history: np.ndarray, zs_hist: np.ndarray,
                     zu_hist: np.ndarray, zr_hist: Optional[np.ndarray],
                     accel_hist: np.ndarray, defl_hist: np.ndarray,
                     force_hist: np.ndarray):
        """Update active plots with historical data up to current simulation time."""
        if len(t_history) == 0:
            return

        self.curve_zs.setData(t_history, zs_hist)
        self.curve_zu.setData(t_history, zu_hist)
        if zr_hist is not None and len(zr_hist) == len(t_history):
            self.curve_zr.setData(t_history, zr_hist)

        self.curve_accel.setData(t_history, accel_hist)
        self.curve_defl.setData(t_history, defl_hist)
        self.curve_force.setData(t_history, force_hist)

    def reset_plots(self):
        """Clear all active curves."""
        empty = np.array([], dtype=np.float64)
        self.curve_zs.setData(empty, empty)
        self.curve_zu.setData(empty, empty)
        self.curve_zr.setData(empty, empty)
        self.curve_accel.setData(empty, empty)
        self.curve_defl.setData(empty, empty)
        self.curve_force.setData(empty, empty)
