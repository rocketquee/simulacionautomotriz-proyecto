"""
Color palette and Qt Style Sheet (QSS) for Automotive Suspension Simulator.
Adheres strictly to sober engineering tool aesthetics:
  - Deep corporate blue: #1F3A5F
  - Neutral grays: #2B2D30, #3C3F41, #1E1F22
  - Subtle amber accent: #E5A93C
  - Light text: #E0E2E5
  - High-contrast trace colors for plotting.
"""

# Color Palette Constants
COLOR_BG_DARK = "#1E1F22"
COLOR_BG_PANEL = "#2B2D30"
COLOR_BG_INPUT = "#35383C"
COLOR_BORDER = "#4E5256"
COLOR_PRIMARY = "#1F3A5F"
COLOR_PRIMARY_HOVER = "#2A4B7C"
COLOR_PRIMARY_ACTIVE = "#162B45"
COLOR_ACCENT = "#E5A93C"
COLOR_ACCENT_HOVER = "#F5BA4C"
COLOR_TEXT_PRIMARY = "#E0E2E5"
COLOR_TEXT_MUTED = "#8C9199"

# Trace colors for plots
PLOT_COLOR_ZS = "#4DA6FF"        # Light blue for sprung mass
PLOT_COLOR_ZU = "#FF8C42"        # Orange for unsprung mass
PLOT_COLOR_ZR = "#A0A5AA"        # Gray for road profile
PLOT_COLOR_ACCEL = "#FF5555"     # Soft red for acceleration
PLOT_COLOR_DEFLECTION = "#33CC99"# Soft green for deflection
PLOT_COLOR_TIRE_FORCE = "#E5A93C"# Amber for tire force

MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLOR_BG_DARK};
    color: {COLOR_TEXT_PRIMARY};
}}

QWidget {{
    background-color: {COLOR_BG_DARK};
    color: {COLOR_TEXT_PRIMARY};
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", sans-serif;
    font-size: 12px;
}}

QGroupBox {{
    background-color: {COLOR_BG_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    margin-top: 14px;
    padding-top: 10px;
    padding-bottom: 8px;
    padding-left: 8px;
    padding-right: 8px;
    font-weight: bold;
    color: {COLOR_ACCENT};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    background-color: {COLOR_BG_PANEL};
}}

QLabel {{
    background-color: transparent;
    color: {COLOR_TEXT_PRIMARY};
}}

QLabel#lbl_muted {{
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
}}

QLabel#lbl_header {{
    font-size: 14px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
}}

QPushButton {{
    background-color: {COLOR_PRIMARY};
    color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
}}

QPushButton:pressed {{
    background-color: {COLOR_PRIMARY_ACTIVE};
}}

QPushButton:disabled {{
    background-color: #383A3D;
    color: {COLOR_TEXT_MUTED};
    border-color: #45474A;
}}

QPushButton#btn_accent {{
    background-color: {COLOR_ACCENT};
    color: #1A1A1A;
    border: 1px solid #C48E2E;
}}

QPushButton#btn_accent:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QSlider::groove:horizontal {{
    border: 1px solid {COLOR_BORDER};
    height: 4px;
    background: {COLOR_BG_INPUT};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: {COLOR_PRIMARY};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {COLOR_ACCENT};
    border: 1px solid #99732B;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {COLOR_ACCENT_HOVER};
}}

QComboBox {{
    background-color: {COLOR_BG_INPUT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 3px;
    padding: 4px 8px;
    color: {COLOR_TEXT_PRIMARY};
}}

QComboBox:hover {{
    border: 1px solid {COLOR_ACCENT};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 18px;
    border-left: 1px solid {COLOR_BORDER};
}}

QComboBox QAbstractItemView {{
    background-color: {COLOR_BG_PANEL};
    border: 1px solid {COLOR_BORDER};
    selection-background-color: {COLOR_PRIMARY};
    selection-color: #FFFFFF;
    color: {COLOR_TEXT_PRIMARY};
}}

QCheckBox {{
    background-color: transparent;
    spacing: 6px;
    color: {COLOR_TEXT_PRIMARY};
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    background-color: {COLOR_BG_INPUT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 3px;
}}

QCheckBox::indicator:checked {{
    background-color: {COLOR_PRIMARY};
    border: 1px solid {COLOR_ACCENT};
}}

QDoubleSpinBox, QSpinBox, QLineEdit {{
    background-color: {COLOR_BG_INPUT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 3px;
    padding: 3px 6px;
    color: {COLOR_TEXT_PRIMARY};
}}

QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus {{
    border: 1px solid {COLOR_ACCENT};
}}

QScrollBar:vertical {{
    background: {COLOR_BG_DARK};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLOR_ACCENT};
}}

QStatusBar {{
    background-color: {COLOR_BG_PANEL};
    border-top: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
}}
"""
