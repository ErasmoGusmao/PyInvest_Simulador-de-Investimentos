"""
PyInvest - Gráficos Plotly (v3.1.1)
Gráficos interativos usando Plotly renderizado em QWebEngineView.
CORRIGIDO: Sintaxe moderna do Plotly (sem titlefont obsoleto)
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt
import plotly.graph_objects as go
from typing import Optional
import numpy as np


class PlotlyChartWidget(QWidget):
    """Widget base para gráficos Plotly."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.web_view)
        
        self._show_empty()
    
    def _show_empty(self):
        """Mostra mensagem de aguardando."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #FFFFFF;
                    font-family: 'Segoe UI', sans-serif;
                }
                .message {
                    color: #9CA3AF;
                    font-size: 16px;
                    font-style: italic;
                }
            </style>
        </head>
        <body>
            <div class="message">Aguardando simulação...</div>
        </body>
        </html>
        """
        self.web_view.setHtml(html)
    
    def _render_figure(self, fig: go.Figure):
        """Renderiza uma figura Plotly no WebView."""
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
                'responsive': True,
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'pyinvest_chart',
                    'height': 600,
                    'width': 1200,
                    'scale': 2
                }
            }
        )
        self.web_view.setHtml(html)


class EvolutionChartPlotly(PlotlyChartWidget):
    """
    Gráfico de evolução do patrimônio com Plotly.
    Mostra túnel de confiança Monte Carlo e linhas determinística/média.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(400)
    
    def update_chart_monte_carlo(self, result):
        """
        Atualiza o gráfico com dados de Monte Carlo.
        
        Args:
            result: MonteCarloResult com todos os dados
        """
        fig = go.Figure()
        
        # Converter meses para anos
        years = result.months / 12
        max_years = int(years[-1])
        
        # Cores
        color_primary = '#10B981'      # Verde (determinístico)
        color_mean = '#EF4444'         # Vermelho (média MC)
        color_tunnel = 'rgba(59, 130, 246, 0.15)'  # Azul transparente
        color_tunnel_border = 'rgba(59, 130, 246, 0.4)'
        
        # === CAMADA 1: Túnel de Confiança (Min-Max) ===
        if result.has_monte_carlo:
            # Área superior (invisível, define o topo)
            fig.add_trace(go.Scatter(
                x=years,
                y=result.balances_max,
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip',
                name='_max'
            ))
            
            # Área inferior com preenchimento até a superior
            fig.add_trace(go.Scatter(
                x=years,
                y=result.balances_min,
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                fillcolor=color_tunnel,
                showlegend=True,
                name='Intervalo Min-Max',
                hoverinfo='skip'
            ))
            
            # Bordas do túnel (linhas finas)
            fig.add_trace(go.Scatter(
                x=years,
                y=result.balances_max,
                mode='lines',
                line=dict(color=color_tunnel_border, width=1, dash='dot'),
                showlegend=False,
                hovertemplate='Máximo: R$ %{y:,.2f}<extra></extra>',
                name='Máximo'
            ))
            
            fig.add_trace(go.Scatter(
                x=years,
                y=result.balances_min,
                mode='lines',
                line=dict(color=color_tunnel_border, width=1, dash='dot'),
                showlegend=False,
                hovertemplate='Mínimo: R$ %{y:,.2f}<extra></extra>',
                name='Mínimo'
            ))
            
            # === CAMADA 2: Linha Média Monte Carlo (tracejada) ===
            fig.add_trace(go.Scatter(
                x=years,
                y=result.balances_mean,
                mode='lines',
                line=dict(
                    color=color_mean,
                    width=3,
                    dash='dash'
                ),
                name=f'Média ({result.n_simulations:,} cenários)',
                hovertemplate='<b>Ano %{x:.0f}</b><br>Média: R$ %{y:,.2f}<extra></extra>'
            ))
        
        # === CAMADA 3: Linha Determinística (sólida com marcadores) ===
        # Pontos anuais
        annual_indices = [i for i in range(len(result.months)) if i % 12 == 0]
        annual_years = [years[i] for i in annual_indices]
        annual_balances = [result.balances_deterministic[i] for i in annual_indices]
        
        # Linha contínua
        fig.add_trace(go.Scatter(
            x=years,
            y=result.balances_deterministic,
            mode='lines',
            line=dict(
                color=color_primary,
                width=4
            ),
            showlegend=False,
            hoverinfo='skip',
            name='_det_line'
        ))
        
        # Marcadores nos pontos anuais
        fig.add_trace(go.Scatter(
            x=annual_years,
            y=annual_balances,
            mode='markers',
            marker=dict(
                size=10,
                color=color_primary,
                line=dict(color='white', width=2)
            ),
            name='Cenário Base',
            hovertemplate='<b>Ano %{x:.0f}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>'
        ))
        
        # === Layout (SINTAXE MODERNA - sem titlefont) ===
        fig.update_layout(
            # Geral
            title=None,
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='left',
                x=0,
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='#E5E7EB',
                borderwidth=1,
                font=dict(size=12)
            ),
            
            # Fundo
            paper_bgcolor='white',
            plot_bgcolor='white',
            
            # Margens
            margin=dict(l=80, r=30, t=50, b=60),
            
            # Hover
            hovermode='closest',
            hoverlabel=dict(
                bgcolor='#1F2937',
                font=dict(
                    size=13,
                    family='Segoe UI',
                    color='white'
                ),
                bordercolor='#1F2937'
            ),
            
            # Eixo X - SINTAXE CORRETA
            xaxis=dict(
                title=dict(
                    text='Período',
                    font=dict(size=13, color='#6B7280')
                ),
                tickfont=dict(size=11, color='#6B7280'),
                tickmode='linear',
                dtick=max(1, max_years // 10) if max_years > 0 else 1,
                showgrid=True,
                gridcolor='#F3F4F6',
                gridwidth=1,
                zeroline=False,
                showline=True,
                linecolor='#E5E7EB',
                linewidth=1
            ),
            
            # Eixo Y - SINTAXE CORRETA
            yaxis=dict(
                title=dict(
                    text='Patrimônio (R$)',
                    font=dict(size=13, color='#6B7280')
                ),
                tickfont=dict(size=11, color='#6B7280'),
                tickformat=',.0f',
                tickprefix='R$ ',
                showgrid=True,
                gridcolor='#F3F4F6',
                gridwidth=1,
                zeroline=False,
                showline=True,
                linecolor='#E5E7EB',
                linewidth=1,
                rangemode='tozero'
            )
        )
        
        self._render_figure(fig)
    
    def update_chart_simple(self, result):
        """
        Atualiza o gráfico com dados simples (sem Monte Carlo).
        Compatibilidade com SimulationResult antigo.
        """
        fig = go.Figure()
        
        # Converter meses para anos
        years = result.months / 12
        
        # Cor
        color_primary = '#10B981'
        
        # Pontos anuais
        annual_indices = [i for i in range(len(result.months)) if i % 12 == 0]
        annual_years = [years[i] for i in annual_indices]
        annual_balances = [result.balances[i] for i in annual_indices]
        
        # Área preenchida
        fig.add_trace(go.Scatter(
            x=years,
            y=result.balances,
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.1)',
            line=dict(color=color_primary, width=3),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Marcadores
        fig.add_trace(go.Scatter(
            x=annual_years,
            y=annual_balances,
            mode='markers',
            marker=dict(
                size=10,
                color=color_primary,
                line=dict(color='white', width=2)
            ),
            name='Patrimônio',
            hovertemplate='<b>Ano %{x:.0f}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>'
        ))
        
        # Layout - SINTAXE CORRETA
        fig.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            margin=dict(l=80, r=30, t=30, b=60),
            hovermode='closest',
            hoverlabel=dict(
                bgcolor='#1F2937',
                font=dict(
                    size=13,
                    family='Segoe UI',
                    color='white'
                )
            ),
            xaxis=dict(
                title=dict(
                    text='Período',
                    font=dict(size=13, color='#6B7280')
                ),
                showgrid=True,
                gridcolor='#F3F4F6',
                showline=True,
                linecolor='#E5E7EB'
            ),
            yaxis=dict(
                title=dict(
                    text='Patrimônio (R$)',
                    font=dict(size=13, color='#6B7280')
                ),
                tickformat=',.0f',
                tickprefix='R$ ',
                showgrid=True,
                gridcolor='#F3F4F6',
                showline=True,
                linecolor='#E5E7EB'
            )
        )
        
        self._render_figure(fig)


class CompositionChartPlotly(PlotlyChartWidget):
    """Gráfico de composição (donut) com Plotly."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(350)
    
    def update_chart(self, total_invested: float, total_interest: float):
        """Atualiza o gráfico de composição."""
        
        labels = ['Capital Investido', 'Lucro com Juros']
        values = [total_invested, total_interest]
        colors = ['#6B7280', '#10B981']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            marker=dict(
                colors=colors,
                line=dict(color='white', width=3)
            ),
            textinfo='percent',
            textfont=dict(size=14, color='white'),
            hovertemplate='<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>',
            hoverlabel=dict(
                bgcolor='#1F2937',
                font=dict(size=13, color='white')
            )
        )])
        
        # Texto central
        total = total_invested + total_interest
        fig.add_annotation(
            text=f'<b>Total</b><br>R$ {total:,.0f}'.replace(',', '.'),
            x=0.5, y=0.5,
            font=dict(size=16, color='#1F2937'),
            showarrow=False
        )
        
        fig.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            margin=dict(l=20, r=20, t=30, b=30),
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.15,
                xanchor='center',
                x=0.5,
                font=dict(size=12)
            )
        )
        
        self._render_figure(fig)
