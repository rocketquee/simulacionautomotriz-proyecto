#!/usr/bin/env python3
"""
Entry point for the Automotive Suspension Simulator (Python/PySide6/PyVista/PyQtGraph).

Usage:
    python main.py
"""

import sys
import os

# Ensure package root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from src.ui_main import MainWindow


def main():
    # High DPI scaling configuration for modern multi-monitor workflows
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("AutomotiveSuspensionSimulator")
    app.setOrganizationName("VehicleDynamicsEngineering")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
