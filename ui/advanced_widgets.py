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
import numpy as np
import plotly.graph_objects as go

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
    
    def __init__(self, parent=None, show_title: bool = True):
        super().__init__(parent)
        self._show_title = show_title
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Título (opcional)
        if self._show_title:
            title = QLabel("📈 Estatísticas dos Saldos Finais")
            title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F2937;")
            layout.addWidget(title)
        
        # Frame com estatísticas
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #FAFAFA;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(8, 8, 8, 8)
        
        self.stats_label = QLabel("Execute uma simulação para ver estatísticas")
        self.stats_label.setStyleSheet("font-size: 13px; color: #374151; background: transparent;")
        self.stats_label.setTextFormat(Qt.RichText)
        self.stats_label.setWordWrap(True)
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
    """
    Gráfico de distribuição (histograma) dos saldos finais.
    
    Usa plotly.graph_objects para garantir carregamento correto do Plotly.js
    (mesmo padrão dos outros gráficos que funcionam).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.chart_view = QWebEngineView()
        self.chart_view.setMinimumHeight(350)
        self.chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.chart_view)
        
        self._show_empty()
    
    def _show_empty(self):
        """Mostra estado vazio."""
        html = """
        <div style="display:flex;justify-content:center;align-items:center;height:100%;
                    color:#9CA3AF;font-family:sans-serif;font-size:14px;">
            Execute uma simulação Monte Carlo para ver a distribuição
        </div>
        """
        self.chart_view.setHtml(html)
    
    def _show_deterministic_message(self, balance: float):
        """
        Mostra mensagem quando em modo determinístico (sem Monte Carlo).
        """
        html = f"""
        <div style="display:flex;flex-direction:column;justify-content:center;align-items:center;
                    height:100%;color:#6B7280;font-family:sans-serif;text-align:center;padding:20px;">
            <div style="font-size:48px;margin-bottom:16px;">📊</div>
            <div style="font-size:16px;font-weight:600;color:#374151;margin-bottom:8px;">
                Modo Determinístico
            </div>
            <div style="font-size:14px;color:#6B7280;margin-bottom:16px;">
                Sem simulação Monte Carlo, o saldo final é único:
            </div>
            <div style="font-size:24px;font-weight:700;color:#10B981;">
                {format_currency(balance)}
            </div>
            <div style="font-size:12px;color:#9CA3AF;margin-top:16px;">
                Ative Monte Carlo (ranges) ou Modo Expert para ver a distribuição de cenários
            </div>
        </div>
        """
        self.chart_view.setHtml(html)
    
    def _render_figure(self, fig: go.Figure):
        """Renderiza figura Plotly no WebView (mesmo padrão dos outros gráficos)."""
        html = fig.to_html(
            include_plotlyjs='cdn',
            full_html=True,
            config={
                'displayModeBar': True,
                'modeBarButtonsToRemove': [
                    'select2d', 'lasso2d', 'autoScale2d',
                    'hoverClosestCartesian', 'hoverCompareCartesian',
                    'toggleSpikelines'
                ],
                'displaylogo': False,
                'responsive': True
            }
        )
        self.chart_view.setHtml(html)
    
    def update_chart(
        self, 
        final_balances,
        stats: PercentileStats,
        meta: float,
        deterministic: Optional[float] = None,
        simulation_method: Optional[str] = None
    ):
        """
        Atualiza histograma usando plotly.graph_objects.
        
        Mantém todas as correções anteriores:
        - Verificação correta para arrays vazios
        - Bins dinâmicos (Regra de Sturges)
        - Verificação meta > 0
        - Linhas P5, P50, P95
        - Título dinâmico com método
        """
        # Verificação para arrays/listas
        if final_balances is None:
            self._show_empty()
            return
        
        # Converter para array numpy se necessário
        if isinstance(final_balances, list):
            final_balances = np.array(final_balances)
        
        # Verificar se tem dados
        if len(final_balances) == 0:
            self._show_empty()
            return
        
        # Verificar se tem variância (não é array de valores iguais)
        if len(final_balances) == 1 or np.std(final_balances) < 1:
            self._show_deterministic_message(float(final_balances[0]))
            return
        
        # Bins dinâmicos (Regra de Sturges)
        n = len(final_balances)
        n_bins = min(max(int(np.ceil(np.log2(n) + 1)), 10), 50)
        
        # Converter para milhões para melhor visualização
        final_balances_m = final_balances / 1_000_000
        p5_m = stats.p5 / 1_000_000
        p50_m = stats.p50 / 1_000_000
        p95_m = stats.p95 / 1_000_000
        det_m = deterministic / 1_000_000 if deterministic else None
        meta_m = meta / 1_000_000 if meta and meta > 0 else None
        
        # Título dinâmico com método de simulação
        method_labels = {
            'bootstrap': '(Bootstrap Histórico)',
            'normal': '(Distribuição Normal)',
            't_student': '(t-Student)',
            'parameter_range': '(Monte Carlo)'
        }
        method_suffix = method_labels.get(simulation_method, '')
        chart_title = f'Distribuição dos Saldos Finais {method_suffix}'.strip()
        
        # Criar figura Plotly
        fig = go.Figure()
        
        # Adicionar histograma
        fig.add_trace(go.Histogram(
            x=final_balances_m,
            nbinsx=n_bins,
            marker_color='rgba(59, 130, 246, 0.7)',
            marker_line_color='rgba(59, 130, 246, 1)',
            marker_line_width=1,
            hovertemplate='Faixa: R$ %{x:.2f}M<br>Frequência: %{y}<extra></extra>',
            name='Distribuição'
        ))
        
        # Adicionar linha P5 (Pessimista) - Vermelho
        fig.add_vline(
            x=p5_m,
            line_dash="dot",
            line_color="#DC2626",
            line_width=2,
            annotation_text="P5",
            annotation_position="top",
            annotation_font_color="#DC2626",
            annotation_font_size=11
        )
        
        # Adicionar linha P50 (Mediana) - Azul
        fig.add_vline(
            x=p50_m,
            line_dash="dash",
            line_color="#3B82F6",
            line_width=2,
            annotation_text="P50 (Mediana)",
            annotation_position="top",
            annotation_font_color="#3B82F6",
            annotation_font_size=11
        )
        
        # Adicionar linha P95 (Otimista) - Verde
        fig.add_vline(
            x=p95_m,
            line_dash="dot",
            line_color="#10B981",
            line_width=2,
            annotation_text="P95",
            annotation_position="top",
            annotation_font_color="#10B981",
            annotation_font_size=11
        )
        
        # Adicionar linha Meta (se > 0) - Laranja
        if meta_m:
            fig.add_vline(
                x=meta_m,
                line_color="#F59E0B",
                line_width=3,
                annotation_text="🎯 Meta",
                annotation_position="top",
                annotation_font_color="#F59E0B",
                annotation_font_size=11
            )
        
        # Adicionar linha Determinístico (se disponível) - Roxo
        if det_m:
            fig.add_vline(
                x=det_m,
                line_color="#7C3AED",
                line_width=2,
                annotation_text="Det.",
                annotation_position="bottom",
                annotation_font_color="#7C3AED",
                annotation_font_size=11
            )
        
        # Configurar layout
        fig.update_layout(
            title=dict(
                text=chart_title,
                font=dict(size=14)
            ),
            xaxis=dict(
                title='Saldo Final (R$ Milhões)',
                gridcolor='#E5E7EB'
            ),
            yaxis=dict(
                title='Frequência',
                gridcolor='#E5E7EB'
            ),
            margin=dict(l=60, r=30, t=80, b=50),
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=False,
            bargap=0.05
        )
        
        # Renderizar usando o método padrão (que funciona)
        self._render_figure(fig)



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
