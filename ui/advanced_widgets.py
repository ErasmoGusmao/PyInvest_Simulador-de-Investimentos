"""
PyInvest - Widgets Avançados de Estatísticas e Risco
Cards, Tabelas e Gráficos para o Módulo Estatístico.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout,
    QPushButton, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWebEngineWidgets import QWebEngineView

from typing import List, Optional, Dict, Any
import json

from core.statistics import (
    PercentileStats, ImplicitParameters, RiskMetrics,
    calculate_percentiles, extract_implicit_parameters, calculate_risk_metrics
)
from core.calculation import format_currency


class MetricCard(QFrame):
    """Card individual para exibir uma métrica."""
    
    def __init__(
        self, 
        title: str, 
        value: str, 
        description: str = "",
        color: str = "#10B981",
        parent=None
    ):
        super().__init__(parent)
        self._setup_ui(title, value, description, color)
    
    def _setup_ui(self, title: str, value: str, description: str, color: str):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                border-left: 4px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #6B7280; font-weight: 500;")
        layout.addWidget(title_label)
        
        # Valor
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"font-size: 24px; color: {color}; font-weight: bold;")
        layout.addWidget(self.value_label)
        
        # Descrição
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("font-size: 11px; color: #9CA3AF;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        self.setMinimumWidth(180)
        self.setMaximumHeight(130)
    
    def set_value(self, value: str):
        """Atualiza o valor exibido."""
        self.value_label.setText(value)


class RiskMetricsPanel(QWidget):
    """Painel com cards de métricas de risco."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Título
        title = QLabel("📊 Métricas de Risco")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F2937;")
        layout.addWidget(title)
        
        # Grid de cards
        grid = QGridLayout()
        grid.setSpacing(16)
        
        # Linha 1
        self.card_success = MetricCard(
            "Prob. Sucesso", "—%", 
            "Chance de atingir a meta",
            "#10B981"
        )
        grid.addWidget(self.card_success, 0, 0)
        
        self.card_ruin = MetricCard(
            "Prob. Ruína", "—%",
            "Chance de perder capital",
            "#EF4444"
        )
        grid.addWidget(self.card_ruin, 0, 1)
        
        self.card_var = MetricCard(
            "VaR 95%", "R$ —",
            "Perda máxima esperada (95%)",
            "#F59E0B"
        )
        grid.addWidget(self.card_var, 0, 2)
        
        # Linha 2
        self.card_volatility = MetricCard(
            "Volatilidade", "R$ —",
            "Desvio padrão dos resultados",
            "#8B5CF6"
        )
        grid.addWidget(self.card_volatility, 1, 0)
        
        self.card_ratio = MetricCard(
            "Risco/Retorno", "—",
            "VaR dividido pelo ganho esperado",
            "#EC4899"
        )
        grid.addWidget(self.card_ratio, 1, 1)
        
        self.card_sharpe = MetricCard(
            "Índice Sharpe", "—",
            "Retorno ajustado ao risco",
            "#06B6D4"
        )
        grid.addWidget(self.card_sharpe, 1, 2)
        
        layout.addLayout(grid)
    
    def update_metrics(self, metrics: RiskMetrics):
        """Atualiza os cards com novas métricas."""
        self.card_success.set_value(f"{metrics.prob_success:.1f}%")
        self.card_ruin.set_value(f"{metrics.prob_ruin:.1f}%")
        self.card_var.set_value(format_currency(metrics.var_95))
        self.card_volatility.set_value(format_currency(metrics.volatility))
        self.card_ratio.set_value(f"{metrics.risk_return_ratio:.2f}")
        self.card_sharpe.set_value(f"{metrics.sharpe_ratio:.2f}")


class PercentileStatsPanel(QWidget):
    """Painel com estatísticas de percentis."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Título
        title = QLabel("📈 Estatísticas dos Saldos Finais")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F2937;")
        layout.addWidget(title)
        
        # Frame com estatísticas
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        
        stats_layout = QVBoxLayout(stats_frame)
        
        self.stats_label = QLabel("Execute uma simulação para ver estatísticas")
        self.stats_label.setStyleSheet("font-size: 13px; color: #374151;")
        self.stats_label.setTextFormat(Qt.RichText)
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_frame)
    
    def update_stats(self, stats: PercentileStats, deterministic: Optional[float] = None):
        """Atualiza estatísticas."""
        html = f"""
        <table style="width:100%; border-collapse: collapse;">
            <tr style="background-color: #FEE2E2;">
                <td style="padding: 8px;"><b>Saldo Mínimo (P5):</b></td>
                <td style="padding: 8px; text-align: right; color: #DC2626;">{format_currency(stats.p5)}</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Saldo P25:</b></td>
                <td style="padding: 8px; text-align: right;">{format_currency(stats.p25)}</td>
            </tr>
            <tr style="background-color: #FEF3C7;">
                <td style="padding: 8px;"><b>Saldo Mediano (P50):</b></td>
                <td style="padding: 8px; text-align: right; color: #D97706; font-weight: bold;">{format_currency(stats.p50)}</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Saldo P75:</b></td>
                <td style="padding: 8px; text-align: right;">{format_currency(stats.p75)}</td>
            </tr>
            <tr style="background-color: #DCFCE7;">
                <td style="padding: 8px;"><b>Saldo Máximo (P95):</b></td>
                <td style="padding: 8px; text-align: right; color: #16A34A;">{format_currency(stats.p95)}</td>
            </tr>
        """
        
        if deterministic:
            html += f"""
            <tr style="background-color: #DBEAFE;">
                <td style="padding: 8px;"><b>Saldo Determinístico:</b></td>
                <td style="padding: 8px; text-align: right; color: #2563EB; font-weight: bold;">{format_currency(deterministic)}</td>
            </tr>
            """
        
        html += f"""
            <tr><td colspan="2" style="padding: 4px;"><hr style="border-color: #E5E7EB;"></td></tr>
            <tr>
                <td style="padding: 8px;"><b>Média:</b></td>
                <td style="padding: 8px; text-align: right;">{format_currency(stats.mean)}</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Moda:</b></td>
                <td style="padding: 8px; text-align: right;">{format_currency(stats.mode)}</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Desvio Padrão:</b></td>
                <td style="padding: 8px; text-align: right;">{format_currency(stats.std_dev)}</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Coef. Variação:</b></td>
                <td style="padding: 8px; text-align: right;">{stats.coef_variation:.1f}%</td>
            </tr>
        </table>
        """
        
        self.stats_label.setText(html)


class ImplicitParametersTable(QWidget):
    """Tabela de cenários reproduzíveis (parâmetros implícitos)."""
    
    scenario_clicked = Signal(dict)  # Emite parâmetros do cenário clicado
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[ImplicitParameters] = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🎯 Cenários Reproduzíveis")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F2937;")
        header.addWidget(title)
        
        header.addStretch()
        
        hint = QLabel("💡 Clique para carregar cenário")
        hint.setStyleSheet("font-size: 11px; color: #9CA3AF;")
        header.addWidget(hint)
        
        layout.addLayout(header)
        
        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            'Cenário', 'Percentil', 'Capital Inicial', 
            'Aporte Mensal', 'Rent. Anual', 'Saldo Final'
        ])
        
        header = self.table.horizontalHeader()
        for i in range(6):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
            QTableWidget::item:selected {
                background-color: #DBEAFE;
                color: #1E40AF;
            }
        """)
        
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        
        layout.addWidget(self.table)
    
    def update_data(self, params: List[ImplicitParameters]):
        """Atualiza tabela com parâmetros implícitos."""
        self._data = params
        self.table.setRowCount(len(params))
        
        colors = {
            'Worst Case': '#FEE2E2',
            'Conservador': '#FEF3C7',
            'Típico': '#DBEAFE',
            'Otimista': '#DCFCE7',
            'Best Case': '#D1FAE5',
            'Valor Esperado': '#F3E8FF',
            'Mais Frequente': '#FCE7F3'
        }
        
        for row, p in enumerate(params):
            bg_color = QColor(colors.get(p.scenario_type, '#FFFFFF'))
            
            items = [
                (p.scenario_name, Qt.AlignLeft),
                (p.percentile, Qt.AlignCenter),
                (format_currency(p.capital_inicial), Qt.AlignRight),
                (format_currency(p.aporte_mensal), Qt.AlignRight),
                (f"{p.rentabilidade_anual:.2f}%", Qt.AlignRight),
                (format_currency(p.saldo_final), Qt.AlignRight),
            ]
            
            for col, (text, align) in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align | Qt.AlignVCenter)
                item.setBackground(bg_color)
                self.table.setItem(row, col, item)
    
    def _on_row_double_clicked(self, row: int, col: int):
        """Emite parâmetros do cenário clicado."""
        if 0 <= row < len(self._data):
            p = self._data[row]
            self.scenario_clicked.emit({
                'capital_inicial': p.capital_inicial,
                'aporte_mensal': p.aporte_mensal,
                'rentabilidade_anual': p.rentabilidade_anual,
                'scenario_name': p.scenario_name
            })


class DistributionChart(QWidget):
    """Gráfico de distribuição (histograma) dos saldos finais."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.chart_view = QWebEngineView()
        self.chart_view.setMinimumHeight(400)
        layout.addWidget(self.chart_view)
        
        self._show_empty()
    
    def _show_empty(self):
        """Mostra estado vazio."""
        html = """
        <div style="display:flex;justify-content:center;align-items:center;height:100%;
                    color:#9CA3AF;font-family:sans-serif;">
            Execute uma simulação Monte Carlo para ver a distribuição
        </div>
        """
        self.chart_view.setHtml(html)
    
    def update_chart(
        self, 
        final_balances: list,
        stats: PercentileStats,
        meta: float,
        deterministic: Optional[float] = None
    ):
        """Atualiza histograma."""
        import numpy as np
        
        # Calcular histograma
        hist, bins = np.histogram(final_balances, bins=30)
        bin_centers = [(bins[i] + bins[i+1]) / 2 for i in range(len(bins)-1)]
        
        # Converter para milhões para melhor visualização
        bin_centers_m = [b / 1_000_000 for b in bin_centers]
        meta_m = meta / 1_000_000
        p50_m = stats.p50 / 1_000_000
        det_m = deterministic / 1_000_000 if deterministic else None
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
            <style>body {{ margin: 0; font-family: sans-serif; }}</style>
        </head>
        <body>
            <div id="chart" style="width:100%;height:400px;"></div>
            <script>
                var data = [{{
                    x: {bin_centers_m},
                    y: {list(hist)},
                    type: 'bar',
                    marker: {{
                        color: 'rgba(59, 130, 246, 0.7)',
                        line: {{ color: 'rgba(59, 130, 246, 1)', width: 1 }}
                    }},
                    hovertemplate: 'Faixa: R$ %{{x:.2f}}M<br>Frequência: %{{y}}<extra></extra>'
                }}];
                
                var layout = {{
                    title: 'Distribuição dos Saldos Finais',
                    xaxis: {{ title: 'Saldo Final (R$ Milhões)' }},
                    yaxis: {{ title: 'Frequência (nº cenários)' }},
                    shapes: [
                        // Meta
                        {{
                            type: 'line',
                            x0: {meta_m}, x1: {meta_m},
                            y0: 0, y1: 1, yref: 'paper',
                            line: {{ color: '#F59E0B', width: 3 }}
                        }},
                        // Mediana
                        {{
                            type: 'line',
                            x0: {p50_m}, x1: {p50_m},
                            y0: 0, y1: 1, yref: 'paper',
                            line: {{ color: '#EF4444', width: 2, dash: 'dash' }}
                        }}
                        {"," + f'''{{
                            type: 'line',
                            x0: {det_m}, x1: {det_m},
                            y0: 0, y1: 1, yref: 'paper',
                            line: {{ color: '#10B981', width: 2 }}
                        }}''' if det_m else ""}
                    ],
                    annotations: [
                        {{
                            x: {meta_m}, y: 1, yref: 'paper',
                            text: 'Meta', showarrow: false,
                            font: {{ color: '#F59E0B' }},
                            yanchor: 'bottom'
                        }},
                        {{
                            x: {p50_m}, y: 0.9, yref: 'paper',
                            text: 'Mediana (P50)', showarrow: false,
                            font: {{ color: '#EF4444' }},
                            yanchor: 'bottom'
                        }}
                        {"," + f'''{{
                            x: {det_m}, y: 0.8, yref: 'paper',
                            text: 'Determinístico', showarrow: false,
                            font: {{ color: '#10B981' }},
                            yanchor: 'bottom'
                        }}''' if det_m else ""}
                    ],
                    margin: {{ l: 60, r: 30, t: 50, b: 50 }},
                    paper_bgcolor: 'white',
                    plot_bgcolor: 'white'
                }};
                
                Plotly.newPlot('chart', data, layout, {{responsive: true}});
            </script>
        </body>
        </html>
        """
        
        self.chart_view.setHtml(html)


class ProjectionChartExpert(QWidget):
    """Gráfico de projeção no Modo Expert (P5/P50/P95)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.chart_view = QWebEngineView()
        self.chart_view.setMinimumHeight(450)
        layout.addWidget(self.chart_view)
        
        self._show_empty()
    
    def _show_empty(self):
        """Mostra estado vazio."""
        html = """
        <div style="display:flex;justify-content:center;align-items:center;height:100%;
                    color:#9CA3AF;font-family:sans-serif;">
            Execute uma simulação para ver a projeção
        </div>
        """
        self.chart_view.setHtml(html)
    
    def update_chart(
        self,
        years: list,
        p5: list,
        p50: list,
        p95: list,
        deterministic: Optional[list] = None,
        meta: Optional[float] = None
    ):
        """
        Atualiza gráfico com dados do Modo Expert.
        
        Args:
            years: Lista de anos [0, 1, 2, ..., N]
            p5: Saldos P5 por ano
            p50: Saldos P50 (mediana) por ano
            p95: Saldos P95 por ano
            deterministic: Saldos determinísticos (opcional)
            meta: Linha de meta (opcional)
        """
        # Converter para milhões
        p5_m = [v / 1_000_000 for v in p5]
        p50_m = [v / 1_000_000 for v in p50]
        p95_m = [v / 1_000_000 for v in p95]
        det_m = [v / 1_000_000 for v in deterministic] if deterministic else None
        meta_m = meta / 1_000_000 if meta else None
        
        traces = []
        
        # Área de confiança P5-P95
        traces.append(f"""{{
            x: {years},
            y: {p95_m},
            fill: 'none',
            mode: 'lines',
            line: {{ color: 'rgba(0,0,0,0)' }},
            showlegend: false,
            hoverinfo: 'skip'
        }}""")
        
        traces.append(f"""{{
            x: {years},
            y: {p5_m},
            fill: 'tonexty',
            fillcolor: 'rgba(59, 130, 246, 0.15)',
            mode: 'lines',
            line: {{ color: 'rgba(0,0,0,0)' }},
            name: 'Intervalo 95% (P5-P95)'
        }}""")
        
        # Linha P50 (Mediana) - destaque
        traces.append(f"""{{
            x: {years},
            y: {p50_m},
            mode: 'lines',
            line: {{ color: '#DC2626', width: 3 }},
            name: 'Mediana (P50)'
        }}""")
        
        # Linhas P5 e P95 tracejadas
        traces.append(f"""{{
            x: {years},
            y: {p5_m},
            mode: 'lines',
            line: {{ color: '#DC2626', width: 1, dash: 'dash' }},
            name: 'Pessimista (P5)',
            opacity: 0.5
        }}""")
        
        traces.append(f"""{{
            x: {years},
            y: {p95_m},
            mode: 'lines',
            line: {{ color: '#16A34A', width: 1, dash: 'dash' }},
            name: 'Otimista (P95)',
            opacity: 0.5
        }}""")
        
        # Determinístico (se existir)
        if det_m:
            traces.append(f"""{{
                x: {years},
                y: {det_m},
                mode: 'lines+markers',
                line: {{ color: '#10B981', width: 3 }},
                marker: {{ size: 8, color: '#10B981' }},
                name: 'Cenário Base (Determinístico)'
            }}""")
        
        # Meta (linha horizontal)
        shapes = ""
        annotations = ""
        if meta_m:
            shapes = f"""
            shapes: [{{
                type: 'line',
                x0: 0, x1: {max(years)},
                y0: {meta_m}, y1: {meta_m},
                line: {{ color: '#F59E0B', width: 2, dash: 'dash' }}
            }}],
            """
            annotations = f"""
            annotations: [{{
                x: {max(years)}, y: {meta_m},
                text: 'Meta: R$ {meta_m:.2f}M',
                showarrow: false,
                font: {{ color: '#F59E0B', size: 12 }},
                xanchor: 'right',
                yanchor: 'bottom'
            }}],
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
            <style>body {{ margin: 0; }}</style>
        </head>
        <body>
            <div id="chart" style="width:100%;height:450px;"></div>
            <script>
                var data = [{','.join(traces)}];
                
                var layout = {{
                    title: 'Evolução do Patrimônio - Análise Probabilística',
                    xaxis: {{ 
                        title: 'Período (Anos)',
                        dtick: 1,
                        showspikes: true,
                        spikemode: 'across',
                        spikethickness: 1,
                        spikecolor: '#9CA3AF',
                        spikedash: 'dash'
                    }},
                    yaxis: {{ 
                        title: 'Patrimônio (R$ Milhões)',
                        showspikes: true,
                        spikemode: 'across',
                        spikethickness: 1,
                        spikecolor: '#9CA3AF',
                        spikedash: 'dash'
                    }},
                    {shapes}
                    {annotations}
                    legend: {{
                        orientation: 'h',
                        yanchor: 'top',
                        y: -0.15,
                        xanchor: 'center',
                        x: 0.5
                    }},
                    hovermode: 'x unified',
                    margin: {{ l: 70, r: 30, t: 50, b: 100 }},
                    paper_bgcolor: 'white',
                    plot_bgcolor: 'white'
                }};
                
                Plotly.newPlot('chart', data, layout, {{responsive: true}});
            </script>
        </body>
        </html>
        """
        
        self.chart_view.setHtml(html)
