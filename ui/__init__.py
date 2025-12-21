"""Módulo de interface gráfica do PyInvest."""
from .window_modern import ModernMainWindow
from .styles_modern import get_modern_style, get_colors, apply_shadow
from .plotly_charts import EvolutionChartPlotly, CompositionChartPlotly
from .events_dialog import EventsDialog
from .widgets import (
    SummaryCard, GoalStatusCard, EvolutionChart,
    CompositionChart, ProjectionTable, AnalysisBox,
    SensitivityDashboard, InsightCard,
    RangeParameterInput
)

__all__ = [
    # Window
    "ModernMainWindow",
    # Styles
    "get_modern_style",
    "get_colors",
    "apply_shadow",
    # Plotly Charts
    "EvolutionChartPlotly",
    "CompositionChartPlotly",
    # Events
    "EventsDialog",
    # Widgets
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
