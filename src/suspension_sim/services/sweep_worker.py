"""Process-safe unit of work for parameter sweeps.

The function ``execute_case`` is module-level and accepts only picklable
dataclasses and Pydantic models. That contract is what allows the experiment
service to distribute cases over a ``ProcessPoolExecutor`` on every platform,
including the ``spawn`` start method used by Windows and macOS.
"""

from __future__ import annotations

from dataclasses import dataclass

from suspension_sim.core.entities import SweepResult
from suspension_sim.core.physics import QuarterCarModel
from suspension_sim.core.schemas import (
    KpiSettings,
    RoadProfileSettings,
    SimulationSettings,
    SuspensionParameters,
)
from suspension_sim.infrastructure.road_profiles import RoadProfileFactory
from suspension_sim.infrastructure.solvers import ScipyOdeSolver
from suspension_sim.services.kpi_service import DefaultKpiCalculator


@dataclass(frozen=True, slots=True)
class SweepCase:
    """One fully specified sweep evaluation."""

    label: str
    spring_multiplier: float
    damping_multiplier: float
    base: SuspensionParameters
    simulation: SimulationSettings
    road: RoadProfileSettings
    kpi_settings: KpiSettings

    def parameters(self) -> SuspensionParameters:
        return SuspensionParameters(
            sprung_mass_kg=self.base.sprung_mass_kg,
            unsprung_mass_kg=self.base.unsprung_mass_kg,
            spring_stiffness_n_per_m=(
                self.base.spring_stiffness_n_per_m * self.spring_multiplier
            ),
            damping_coefficient_n_s_per_m=(
                self.base.damping_coefficient_n_s_per_m * self.damping_multiplier
            ),
            tire_stiffness_n_per_m=self.base.tire_stiffness_n_per_m,
        )


def execute_case(case: SweepCase) -> SweepResult:
    """Solve one case and return its KPIs. Safe to call in a subprocess."""

    parameters = case.parameters()
    road = RoadProfileFactory.create(case.road)
    model = QuarterCarModel(parameters=parameters, road_profile=road)

    solver = ScipyOdeSolver()
    solution = solver.solve(model, case.simulation, model.initial_state(case.simulation))
    road_displacement = road.elevation_array(solution.time_s)
    sprung_acceleration, _ = model.accelerations(solution.states, road_displacement)

    kpis = DefaultKpiCalculator().compute(
        time_s=solution.time_s,
        sprung_acceleration_m_s2=sprung_acceleration,
        suspension_travel_m=model.suspension_travel(solution.states),
        tire_deflection_m=model.tire_deflection(solution.states, road_displacement),
        parameters=parameters,
        settings=case.kpi_settings,
    )

    return SweepResult(
        label=case.label,
        spring_stiffness_n_per_m=parameters.spring_stiffness_n_per_m,
        damping_coefficient_n_s_per_m=parameters.damping_coefficient_n_s_per_m,
        kpis=kpis,
    )
