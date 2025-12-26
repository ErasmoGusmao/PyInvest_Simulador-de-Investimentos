"""Módulo core do PyInvest."""
from .calculation import (
    calculate_compound_interest, 
    format_currency, 
    SimulationResult,
    SimulationAnalysis,
    YearlyProjection,
    InvestmentCalculator,
    SensitivityMetrics,
    ParameterRange,
    SimulationParameters,
    MonteCarloResult,
    run_full_simulation,
    run_monte_carlo_simulation
)
from .events import (
    ExtraordinaryEvent,
    EventsManager,
    InsolvencyEvent,
    apply_events_to_simulation
)
from .statistics import (
    ProjectData,
    ParameterSet,
    HistoricalReturn,
    MonteCarloConfig,
    PercentileStats,
    ImplicitParameters,
    RiskMetrics,
    save_project,
    load_project,
    calculate_percentiles,
    extract_implicit_parameters,
    calculate_risk_metrics,
    find_implicit_rate,
    bootstrap_returns,
    normal_returns,
    t_student_returns
)

__all__ = [
    # Calculation
    "calculate_compound_interest", 
    "format_currency", 
    "SimulationResult",
    "SimulationAnalysis",
    "YearlyProjection",
    "InvestmentCalculator",
    "SensitivityMetrics",
    # Monte Carlo
    "ParameterRange",
    "SimulationParameters",
    "MonteCarloResult",
    "run_full_simulation",
    "run_monte_carlo_simulation",
    # Events
    "ExtraordinaryEvent",
    "EventsManager",
    "InsolvencyEvent",
    "apply_events_to_simulation",
    # Statistics
    "ProjectData",
    "ParameterSet",
    "HistoricalReturn",
    "MonteCarloConfig",
    "PercentileStats",
    "ImplicitParameters",
    "RiskMetrics",
    "save_project",
    "load_project",
    "calculate_percentiles",
    "extract_implicit_parameters",
    "calculate_risk_metrics",
    "find_implicit_rate",
    "bootstrap_returns",
    "normal_returns",
    "t_student_returns"
]
