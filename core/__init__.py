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
from .worker import (
    SimulationWorker,
    SimulationSignals
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
    # Worker
    "SimulationWorker",
    "SimulationSignals"
]
