"""
Interactive 3D suspension visualization using PyVista and PyVistaQt.
Embeds QtInteractor inside PySide6 with mouse controls (rotate, zoom, pan).
Renders:
  - Ground surface plane with road displacement zr
  - Wheel / tire assembly (cylinder + hub) moving with zu
  - Realistic helical coil spring that compresses/extends with zs - zu
  - Damper strut (outer cylinder + inner piston)
  - Sprung quarter-vehicle chassis block moving with zs
"""

from typing import Optional
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyvista as pv
from pyvistaqt import QtInteractor

from .ui_theme import COLOR_BG_DARK, COLOR_PRIMARY, COLOR_ACCENT


def create_helical_spring_mesh(radius: float, height: float, turns: int = 7,
                               n_points: int = 250, tube_radius: float = 0.015) -> pv.PolyData:
    """Generate a 3D tubular helical spring along the Z-axis."""
    t = np.linspace(0.0, 1.0, n_points)
    angle = 2.0 * np.pi * turns * t
    x = radius * np.cos(angle)
    y = radius * np.sin(angle)
    z = height * t

    points = np.column_stack([x, y, z])
    spline = pv.Spline(points, n_points)
    tube = spline.tube(radius=tube_radius, n_sides=12)
    return tube


class Suspension3DViewer(QWidget):
    """3D viewport embedded in Qt for Quarter-Car dynamic animation."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # PyVista Qt interactor
        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)

        # Scene configuration
        self.plotter.set_background(COLOR_BG_DARK)
        self.plotter.add_axes()
        self.plotter.enable_anti_aliasing()

        # Geometry nominal heights (m)
        self.nominal_ground = 0.0
        self.nominal_zu = 0.35      # Wheel center
        self.nominal_zs = 0.90      # Sprung mass center
        self.wheel_radius = 0.30
        self.wheel_width = 0.20

        # Actors storage
        self.actor_ground = None
        self.actor_wheel = None
        self.actor_spring = None
        self.actor_damper_body = None
        self.actor_damper_rod = None
        self.actor_chassis = None

        self._build_static_scene()
        self.reset_camera()

    def _build_static_scene(self):
        """Construct initial procedural 3D elements."""
        # 1. Ground plane (represents road input zr)
        ground_mesh = pv.Plane(
            center=(0.0, 0.0, self.nominal_ground),
            direction=(0.0, 0.0, 1.0),
            i_size=1.6, j_size=1.2
        )
        self.actor_ground = self.plotter.add_mesh(
            ground_mesh, color="#3A3D40", opacity=0.8, show_edges=True,
            edge_color="#555A60"
        )

        # 2. Wheel (cylinder oriented horizontally along Y axis)
        wheel_mesh = pv.Cylinder(
            center=(0.0, 0.0, self.nominal_zu),
            direction=(0.0, 1.0, 0.0),
            radius=self.wheel_radius,
            height=self.wheel_width,
            resolution=36
        )
        self.actor_wheel = self.plotter.add_mesh(
            wheel_mesh, color="#222225", smooth_shading=True
        )

        # 3. Helical Spring (offset to left: x = -0.08)
        spring_h = self.nominal_zs - self.nominal_zu
        spring_mesh = create_helical_spring_mesh(
            radius=0.06, height=spring_h, turns=6, tube_radius=0.012
        )
        spring_mesh.translate([-0.08, 0.0, self.nominal_zu], inplace=True)
        self.actor_spring = self.plotter.add_mesh(
            spring_mesh, color=COLOR_ACCENT, smooth_shading=True
        )

        # 4. Telescopic Damper (offset to right: x = +0.08)
        # Damper outer body attached to unsprung mass
        damper_body_mesh = pv.Cylinder(
            center=(0.08, 0.0, self.nominal_zu + 0.15),
            direction=(0.0, 0.0, 1.0),
            radius=0.035,
            height=0.30,
            resolution=24
        )
        self.actor_damper_body = self.plotter.add_mesh(
            damper_body_mesh, color="#1F3A5F", smooth_shading=True
        )

        # Damper piston rod attached to sprung mass
        damper_rod_mesh = pv.Cylinder(
            center=(0.08, 0.0, self.nominal_zs - 0.12),
            direction=(0.0, 0.0, 1.0),
            radius=0.015,
            height=0.25,
            resolution=20
        )
        self.actor_damper_rod = self.plotter.add_mesh(
            damper_rod_mesh, color="#C8CCD0", smooth_shading=True
        )

        # 5. Chassis / Sprung Mass block
        chassis_mesh = pv.Cube(
            center=(0.0, 0.0, self.nominal_zs + 0.15),
            x_length=0.70,
            y_length=0.45,
            z_length=0.25
        )
        self.actor_chassis = self.plotter.add_mesh(
            chassis_mesh, color=COLOR_PRIMARY, smooth_shading=True,
            show_edges=True, edge_color="#3B5A85"
        )

    def update_positions(self, zs: float, zu: float, zr: float):
        """
        Dynamically update 3D positions and geometries based on simulation state.
        :param zs: Vertical displacement of sprung mass (m)
        :param zu: Vertical displacement of unsprung mass (m)
        :param zr: Vertical displacement of road surface (m)
        """
        current_ground = self.nominal_ground + zr
        current_zu = self.nominal_zu + zu
        current_zs = self.nominal_zs + zs

        # 1. Update Road Ground
        new_ground = pv.Plane(
            center=(0.0, 0.0, current_ground),
            direction=(0.0, 0.0, 1.0),
            i_size=1.6, j_size=1.2
        )
        self.actor_ground.mapper.SetInputData(new_ground)

        # 2. Update Wheel
        new_wheel = pv.Cylinder(
            center=(0.0, 0.0, current_zu),
            direction=(0.0, 1.0, 0.0),
            radius=self.wheel_radius,
            height=self.wheel_width,
            resolution=36
        )
        self.actor_wheel.mapper.SetInputData(new_wheel)

        # 3. Update Spring (re-generated with compressed/expanded length)
        current_spring_h = max(0.08, current_zs - current_zu)
        new_spring = create_helical_spring_mesh(
            radius=0.06, height=current_spring_h, turns=6, tube_radius=0.012
        )
        new_spring.translate([-0.08, 0.0, current_zu], inplace=True)
        self.actor_spring.mapper.SetInputData(new_spring)

        # 4. Update Damper outer body (follows unsprung mass zu)
        new_damper_body = pv.Cylinder(
            center=(0.08, 0.0, current_zu + 0.15),
            direction=(0.0, 0.0, 1.0),
            radius=0.035,
            height=0.30,
            resolution=24
        )
        self.actor_damper_body.mapper.SetInputData(new_damper_body)

        # Update Damper piston rod (follows sprung mass zs)
        rod_bottom = current_zu + 0.15
        rod_top = current_zs
        rod_center = (rod_bottom + rod_top) / 2.0
        rod_length = max(0.05, rod_top - rod_bottom)
        new_damper_rod = pv.Cylinder(
            center=(0.08, 0.0, rod_center),
            direction=(0.0, 0.0, 1.0),
            radius=0.015,
            height=rod_length,
            resolution=20
        )
        self.actor_damper_rod.mapper.SetInputData(new_damper_rod)

        # 5. Update Chassis
        new_chassis = pv.Cube(
            center=(0.0, 0.0, current_zs + 0.15),
            x_length=0.70,
            y_length=0.45,
            z_length=0.25
        )
        self.actor_chassis.mapper.SetInputData(new_chassis)

        # Trigger redraw
        self.plotter.render()

    def reset_camera(self):
        """Set standard isometric engineering camera viewpoint."""
        self.plotter.camera_position = [
            (2.2, -2.4, 1.8),   # eye position
            (0.0, 0.0, 0.65),   # focal point
            (0.0, 0.0, 1.0)     # view up
        ]
        self.plotter.render()
