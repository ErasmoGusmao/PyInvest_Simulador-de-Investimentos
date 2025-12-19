"""Módulo de interface gráfica do PyInvest."""
from .window import MainWindow
from .styles import get_style, get_colors
from .widgets import (
    SummaryCard, GoalStatusCard, EvolutionChart,
    CompositionChart, ProjectionTable, AnalysisBox,
    SensitivityDashboard, InsightCard,
    RangeParameterInput
)

__all__ = [
    "MainWindow",
    "get_style",
    "get_colors",
    "SummaryCard",
    "GoalStatusCard", 
    "EvolutionChart",
    "CompositionChart",
    "ProjectionTable",
    "AnalysisBox",
    "SensitivityDashboard",
    "InsightCard",
    "RangeParameterInput"
]
