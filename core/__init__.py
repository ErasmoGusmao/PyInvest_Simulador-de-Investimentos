"""Módulo core do PyInvest."""
from .calculation import (
    calculate_compound_interest, 
    format_currency, 
    SimulationResult,
    SimulationAnalysis,
    YearlyProjection,
    InvestmentCalculator,
    SensitivityMetrics
)

__all__ = [
    "calculate_compound_interest", 
    "format_currency", 
    "SimulationResult",
    "SimulationAnalysis",
    "YearlyProjection",
    "InvestmentCalculator",
    "SensitivityMetrics"
]
