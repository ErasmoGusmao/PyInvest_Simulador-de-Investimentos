"""
PyInvest - Widgets Personalizados
Componentes reutilizáveis da interface.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QWidget, QSizePolicy, QLineEdit, QGridLayout,
    QSpinBox, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDoubleValidator

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from core.calculation import format_currency, SimulationResult
from core.monte_carlo import MonteCarloResult, ParameterRange, YearlyProjectionMC
from ui.styles import get_colors


# =============================================================================
# WIDGET DE PARÂMETRO COM RANGE (Min/Det/Max)
# =============================================================================

class RangeParameterInput(QFrame):
    """
    Widget para entrada de parâmetro com range de incerteza.
    Contém 3 campos: Mínimo, Determinístico, Máximo.
    """
    
    valueChanged = Signal()  # Emitido quando qualquer valor muda
    
    def __init__(self, label: str, suffix: str = "", decimals: int = 2, parent=None):
        super().__init__(parent)
        
        self.label_text = label
        self.suffix = suffix
        self.decimals = decimals
        
        self._setup_ui()
        self._setup_style()
    
    def _setup_ui(self):
        """Configura a interface do widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(6)
        
        # Label principal
        title = QLabel(self.label_text)
        title.setStyleSheet("""
            font-size: 13px;
            font-weight: 500;
            color: #2c3e50;
        """)
        layout.addWidget(title)
        
        # Grid para os 3 campos
        grid = QGridLayout()
        grid.setSpacing(8)
        
        # Campo Mínimo
        min_label = QLabel("Mín")
        min_label.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        self.input_min = QLineEdit()
        self.input_min.setPlaceholderText("Mínimo")
        self.input_min.textChanged.connect(self._on_value_changed)
        
        # Campo Determinístico (central, destacado)
        det_label = QLabel("Base")
        det_label.setStyleSheet("font-size: 10px; color: #16a085; font-weight: bold;")
        self.input_det = QLineEdit()
        self.input_det.setPlaceholderText("Valor Base")
        self.input_det.textChanged.connect(self._on_value_changed)
        
        # Campo Máximo
        max_label = QLabel("Máx")
        max_label.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        self.input_max = QLineEdit()
        self.input_max.setPlaceholderText("Máximo")
        self.input_max.textChanged.connect(self._on_value_changed)
        
        # Adicionar ao grid
        grid.addWidget(min_label, 0, 0)
        grid.addWidget(det_label, 0, 1)
        grid.addWidget(max_label, 0, 2)
        grid.addWidget(self.input_min, 1, 0)
        grid.addWidget(self.input_det, 1, 1)
        grid.addWidget(self.input_max, 1, 2)
        
        layout.addLayout(grid)
        
        # Sufixo (se houver)
        if self.suffix:
            suffix_label = QLabel(self.suffix)
            suffix_label.setStyleSheet("font-size: 10px; color: #95a5a6; margin-top: -5px;")
            layout.addWidget(suffix_label)
    
    def _setup_style(self):
        """Configura estilos dos campos."""
        base_style = """
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 13px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #16a085;
            }
            QLineEdit::placeholder {
                color: #bdc3c7;
            }
        """
        
        self.input_min.setStyleSheet(base_style)
        self.input_max.setStyleSheet(base_style)
        
        # Campo determinístico com destaque
        det_style = """
            QLineEdit {
                background-color: #f0fdf9;
                border: 2px solid #16a085;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 13px;
                font-weight: bold;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #0d7d6c;
                background-color: #e8faf5;
            }
            QLineEdit::placeholder {
                color: #7fb8ac;
                font-weight: normal;
            }
        """
        self.input_det.setStyleSheet(det_style)
    
    def _on_value_changed(self):
        """Handler para mudança de valor."""
        self.valueChanged.emit()
    
    def _parse_value(self, text: str) -> float:
        """Converte texto para float."""
        if not text.strip():
            return None
        clean = text.replace("R$", "").replace("%", "").replace(" ", "").strip()
        if "," in clean and "." in clean:
            if clean.rfind(",") > clean.rfind("."):
                clean = clean.replace(".", "").replace(",", ".")
            else:
                clean = clean.replace(",", "")
        elif "," in clean:
            clean = clean.replace(",", ".")
        try:
            return float(clean)
        except ValueError:
            return None
    
    def get_parameter_range(self) -> ParameterRange:
        """
        Retorna um ParameterRange com os valores atuais.
        """
        return ParameterRange(
            min_value=self._parse_value(self.input_min.text()),
            deterministic=self._parse_value(self.input_det.text()),
            max_value=self._parse_value(self.input_max.text())
        )
    
    def get_deterministic_value(self) -> float:
        """Retorna apenas o valor determinístico (ou 0 se vazio)."""
        val = self._parse_value(self.input_det.text())
        return val if val is not None else 0.0
    
    def set_values(self, min_val=None, det_val=None, max_val=None):
        """Define os valores dos campos."""
        if min_val is not None:
            self.input_min.setText(str(min_val))
        if det_val is not None:
            self.input_det.setText(str(det_val))
        if max_val is not None:
            self.input_max.setText(str(max_val))
    
    def clear(self):
        """Limpa todos os campos."""
        self.input_min.clear()
        self.input_det.clear()
        self.input_max.clear()
    
    def is_probabilistic(self) -> bool:
        """Verifica se tem valores min/max preenchidos."""
        return (
            self._parse_value(self.input_min.text()) is not None and
            self._parse_value(self.input_max.text()) is not None
        )


class SummaryCard(QFrame):
    """Card de resumo colorido."""
    
    def __init__(
        self, 
        title: str, 
        value: str = "R$ 0,00", 
        card_type: str = "invested"
    ):
        super().__init__()
        
        # Define o object name baseado no tipo
        type_map = {
            "invested": "card_invested",
            "interest": "card_interest", 
            "final": "card_final",
            "goal": "card_goal"
        }
        self.setObjectName(type_map.get(card_type, "card"))
        self.setMinimumHeight(90)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        
        # Título
        self.title_label = QLabel(title)
        self.title_label.setObjectName("card_title")
        
        # Valor
        self.value_label = QLabel(value)
        self.value_label.setObjectName("card_value")
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()
    
    def set_value(self, value: str):
        """Atualiza o valor exibido."""
        self.value_label.setText(value)


class GoalStatusCard(QFrame):
    """Card especial para status da meta."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("card_goal")
        self.setMinimumHeight(90)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(4)
        
        # Título
        self.title_label = QLabel("STATUS DA META")
        self.title_label.setObjectName("card_title")
        
        # Status (✓ Atingido ou ✗ Não atingido)
        self.status_label = QLabel("—")
        self.status_label.setObjectName("card_value")
        self.status_label.setStyleSheet("font-size: 18px;")
        
        # Percentual
        self.percent_label = QLabel("")
        self.percent_label.setStyleSheet("color: white; font-size: 12px;")
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.percent_label)
        layout.addStretch()
    
    def update_status(self, achieved: bool, percentage: float):
        """Atualiza o status da meta."""
        if achieved:
            self.status_label.setText("✓ Atingido")
        else:
            self.status_label.setText("✗ Não atingido")
        
        self.percent_label.setText(f"{percentage:.1f}% da meta")


class EvolutionChart(FigureCanvas):
    """Gráfico de evolução do patrimônio com tooltip inteligente."""
    
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 4), facecolor='#ffffff', dpi=100)
        self.axes = self.fig.add_subplot(111)
        
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Dados para tooltip
        self.annual_data = None
        self.invested_data = None
        self.annotation = None
        self.highlight_point = None  # Ponto de destaque ao hover
        
        # Configurações do tooltip
        self.tooltip_offset = 12  # Distância do ponto em pixels
        self.tooltip_margin = 10  # Margem das bordas do gráfico
        
        self._setup_style()
        self._draw_empty()
        
        # Conectar evento de movimento do mouse
        self.mpl_connect('motion_notify_event', self._on_hover)
        self.mpl_connect('axes_leave_event', self._on_leave)
    
    def _setup_style(self):
        """Configura estilo do gráfico."""
        self.axes.set_facecolor('#ffffff')
        self.axes.tick_params(colors='#7f8c8d', labelsize=9)
        self.axes.spines['bottom'].set_color('#e0e0e0')
        self.axes.spines['left'].set_color('#e0e0e0')
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.grid(True, linestyle='-', alpha=0.3, color='#e0e0e0')
    
    def _draw_empty(self):
        """Desenha gráfico vazio."""
        self.axes.text(
            0.5, 0.5, 'Aguardando simulação...',
            transform=self.axes.transAxes,
            ha='center', va='center',
            fontsize=12, color='#95a5a6', style='italic'
        )
        self.fig.tight_layout()
        self.draw()
    
    def _on_leave(self, event):
        """Handler quando o mouse sai do gráfico."""
        if self.annotation:
            self.annotation.set_visible(False)
        if self.highlight_point:
            self.highlight_point.set_visible(False)
        self.draw_idle()
    
    def _calculate_smart_position(self, data_x, data_y):
        """
        Calcula posição inteligente do tooltip evitando cortes nas bordas.
        
        Returns:
            tuple: (offset_x, offset_y, ha, va) para posicionamento
        """
        # Obter limites do gráfico em coordenadas de dados
        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        
        # Calcular posição relativa do ponto (0 a 1)
        rel_x = (data_x - xlim[0]) / (xlim[1] - xlim[0])
        rel_y = (data_y - ylim[0]) / (ylim[1] - ylim[0])
        
        # Offset base mais próximo do ponto
        base_offset = 8
        
        # Determinar direção horizontal
        if rel_x > 0.85:  # Ponto muito à direita
            offset_x = -base_offset
            ha = 'right'
        elif rel_x < 0.15:  # Ponto muito à esquerda
            offset_x = base_offset
            ha = 'left'
        else:  # Centro - tooltip centralizado acima
            offset_x = 0
            ha = 'center'
        
        # Determinar direção vertical - PREFERÊNCIA: ACIMA do ponto
        if rel_y > 0.75:  # Ponto muito acima - tooltip abaixo
            offset_y = -base_offset - 35
            va = 'top'
        else:  # Padrão: tooltip acima do ponto
            offset_y = base_offset + 20
            va = 'bottom'
        
        return offset_x, offset_y, ha, va
    
    def _format_currency_tooltip(self, value):
        """Formata valor monetário para o tooltip."""
        if value >= 1_000_000:
            return f"R$ {value/1_000_000:,.2f}M".replace(",", "X").replace(".", ",").replace("X", ".")
        elif value >= 1_000:
            return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def _on_hover(self, event):
        """Handler para mostrar tooltip inteligente ao passar o mouse."""
        if event.inaxes != self.axes or self.annual_data is None:
            if self.annotation:
                self.annotation.set_visible(False)
            if self.highlight_point:
                self.highlight_point.set_visible(False)
            self.draw_idle()
            return
        
        # Encontrar o ponto mais próximo
        x = event.xdata
        if x is None:
            return
        
        # Encontrar o ano mais próximo
        year_idx = int(round(x))
        if not (0 <= year_idx < len(self.annual_data['years'])):
            return
        
        year = self.annual_data['years'][year_idx]
        balance = self.annual_data['balances'][year_idx]
        
        # Calcular posição inteligente do tooltip
        offset_x, offset_y, ha, va = self._calculate_smart_position(year, balance)
        
        # Criar annotation se não existir
        if self.annotation is None:
            self.annotation = self.axes.annotate(
                '',
                xy=(0, 0),
                xytext=(0, 0),
                textcoords='offset points',
                bbox=dict(
                    boxstyle='round,pad=0.5,rounding_size=0.2',
                    facecolor='#2c3e50',
                    edgecolor='none',
                    alpha=0.92
                ),
                fontsize=10,
                fontweight='normal',
                color='white',
                zorder=1000,
                # Seta minimalista integrada ao tooltip
                arrowprops=dict(
                    arrowstyle='wedge,tail_width=0.5,shrink_factor=0.5',
                    facecolor='#2c3e50',
                    edgecolor='none',
                    alpha=0.92,
                    shrinkA=0,
                    shrinkB=8,
                    patchA=None,
                    mutation_scale=8
                )
            )
        
        # Criar ponto de destaque se não existir
        if self.highlight_point is None:
            self.highlight_point, = self.axes.plot(
                [], [], 'o',
                markersize=12,
                markerfacecolor='#16a085',
                markeredgecolor='white',
                markeredgewidth=2,
                zorder=999,
                visible=False
            )
        
        # Formatar texto do tooltip
        balance_fmt = self._format_currency_tooltip(balance)
        
        # Construir texto (apenas Saldo Total para ficar mais limpo)
        tooltip_text = f"Ano {year}\nSaldo Total (R$): {balance:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Atualizar annotation
        self.annotation.set_text(tooltip_text)
        self.annotation.xy = (year, balance)
        self.annotation.xyann = (offset_x, offset_y)
        self.annotation.set_ha(ha)
        self.annotation.set_va(va)
        self.annotation.set_visible(True)
        
        # Atualizar ponto de destaque
        self.highlight_point.set_data([year], [balance])
        self.highlight_point.set_visible(True)
        
        self.draw_idle()
    
    def update_chart(self, result: SimulationResult):
        """Atualiza o gráfico com os dados da simulação."""
        self.axes.clear()
        self._setup_style()
        self.annotation = None
        self.highlight_point = None  # Resetar ponto de destaque
        
        colors = get_colors()
        
        # Converter meses para anos para o eixo X
        years = result.months / 12
        max_years = int(years[-1])
        
        # Calcular linha de capital inicial sem aportes (só juros compostos)
        # Fórmula: M = C * (1 + i)^n onde i é a taxa mensal
        initial = result.analysis.initial_investment
        monthly_rate = (1 + result.analysis.annual_rate / 100) ** (1/12) - 1
        capital_without_contributions = initial * ((1 + monthly_rate) ** result.months)
        
        # Área preenchida para saldo total
        self.axes.fill_between(
            years, result.balances, 
            alpha=0.15, color=colors['primary']
        )
        
        # Pontos anuais para interatividade
        annual_indices = [i for i in range(len(result.months)) if i % 12 == 0]
        annual_years = [int(years[i]) for i in annual_indices]
        annual_balances = [result.balances[i] for i in annual_indices]
        annual_capital_no_contrib = [capital_without_contributions[i] for i in annual_indices]
        
        # Guardar dados para tooltip
        self.annual_data = {
            'years': annual_years,
            'balances': annual_balances
        }
        self.invested_data = annual_capital_no_contrib
        
        # Linha do saldo total
        line1, = self.axes.plot(
            years, result.balances,
            color=colors['primary'], linewidth=2.5,
            label='Saldo Total (R$)'
        )
        
        # Marcadores apenas nos pontos anuais (saldo)
        self.axes.scatter(
            annual_years, annual_balances,
            color=colors['primary'], s=40, zorder=5,
            edgecolors='white', linewidths=1.5
        )
        
        # Linha do capital inicial sem aportes (tracejada)
        line2, = self.axes.plot(
            years, capital_without_contributions,
            color='#5d6d7e', linewidth=2, linestyle='--',
            label='Capital Inicial sem Aportes (R$)', alpha=0.8
        )
        
        # Legenda
        self.axes.legend(
            loc='upper left',
            frameon=True,
            facecolor='white',
            edgecolor='#e0e0e0',
            fontsize=9
        )
        
        # Formatação do eixo Y - valores monetários
        def format_currency_axis(x, p):
            if x >= 1000000:
                return f'R$ {x/1000000:.1f}M'
            elif x >= 1000:
                return f'R$ {x/1000:.0f}k'
            else:
                return f'R$ {x:.0f}'
        
        self.axes.yaxis.set_major_formatter(format_currency_axis)
        
        # Formatação do eixo X - CORREÇÃO: evitar sobreposição
        if max_years <= 10:
            tick_interval = 1
        elif max_years <= 20:
            tick_interval = 2
        elif max_years <= 30:
            tick_interval = 5
        else:
            tick_interval = 10
        
        tick_positions = list(range(0, max_years + 1, tick_interval))
        if max_years not in tick_positions:
            tick_positions.append(max_years)
        
        self.axes.set_xticks(tick_positions)
        self.axes.set_xticklabels([f'Ano {i}' for i in tick_positions], fontsize=8)
        
        if max_years > 15:
            self.axes.tick_params(axis='x', rotation=45)
        
        self.fig.tight_layout(pad=1.5)
        self.draw()
    
    def update_chart_monte_carlo(self, result: MonteCarloResult):
        """
        Atualiza o gráfico com dados de Monte Carlo.
        Mostra túnel de confiança, média probabilística e linha determinística.
        """
        self.axes.clear()
        self._setup_style()
        self.annotation = None
        self.highlight_point = None
        
        colors = get_colors()
        
        # Converter meses para anos
        years = result.months / 12
        max_years = int(years[-1])
        
        # === CAMADA 1: Túnel de Confiança (Monte Carlo) ===
        if result.has_monte_carlo:
            # Área entre P10 e P90 (túnel interno mais escuro)
            self.axes.fill_between(
                years, result.balances_p10, result.balances_p90,
                alpha=0.25, color='#3498db',
                label='Intervalo 80% (P10-P90)'
            )
            
            # Área entre Min e Max (túnel externo mais claro)
            self.axes.fill_between(
                years, result.balances_min, result.balances_max,
                alpha=0.10, color='#2980b9',
                label='Intervalo Total (Min-Max)'
            )
            
            # Bordas do túnel (linhas finas)
            self.axes.plot(
                years, result.balances_min,
                color='#3498db', linewidth=0.8, linestyle='-', alpha=0.5
            )
            self.axes.plot(
                years, result.balances_max,
                color='#3498db', linewidth=0.8, linestyle='-', alpha=0.5
            )
            
            # === CAMADA 2: Média Monte Carlo (tracejada) ===
            self.axes.plot(
                years, result.balances_mean,
                color='#e74c3c', linewidth=2.5, linestyle='--',
                label=f'Média Simulação ({result.n_simulations:,} cenários)'
            )
        
        # === CAMADA 3: Linha Determinística (sólida com marcadores) ===
        # Pontos anuais
        annual_indices = [i for i in range(len(result.months)) if i % 12 == 0]
        annual_years = [int(years[i]) for i in annual_indices]
        annual_balances_det = [result.balances_deterministic[i] for i in annual_indices]
        
        # Guardar dados para tooltip
        self.annual_data = {
            'years': annual_years,
            'balances': annual_balances_det
        }
        
        # Se tiver Monte Carlo, adicionar dados extras ao tooltip
        if result.has_monte_carlo:
            self.annual_data['balances_mean'] = [result.balances_mean[i] for i in annual_indices]
            self.annual_data['balances_min'] = [result.balances_min[i] for i in annual_indices]
            self.annual_data['balances_max'] = [result.balances_max[i] for i in annual_indices]
        
        # Linha determinística
        self.axes.plot(
            years, result.balances_deterministic,
            color=colors['primary'], linewidth=3,
            label='Cenário Base (Determinístico)', solid_capstyle='round'
        )
        
        # Marcadores nos pontos anuais
        self.axes.scatter(
            annual_years, annual_balances_det,
            color=colors['primary'], s=50, zorder=10,
            edgecolors='white', linewidths=2
        )
        
        # === Legenda ===
        self.axes.legend(
            loc='upper left',
            frameon=True,
            facecolor='white',
            edgecolor='#e0e0e0',
            fontsize=8,
            framealpha=0.95
        )
        
        # === Formatação dos Eixos ===
        def format_currency_axis(x, p):
            if x >= 1000000:
                return f'R$ {x/1000000:.1f}M'
            elif x >= 1000:
                return f'R$ {x/1000:.0f}k'
            else:
                return f'R$ {x:.0f}'
        
        self.axes.yaxis.set_major_formatter(format_currency_axis)
        
        # Eixo X
        if max_years <= 10:
            tick_interval = 1
        elif max_years <= 20:
            tick_interval = 2
        elif max_years <= 30:
            tick_interval = 5
        else:
            tick_interval = 10
        
        tick_positions = list(range(0, max_years + 1, tick_interval))
        if max_years not in tick_positions:
            tick_positions.append(max_years)
        
        self.axes.set_xticks(tick_positions)
        self.axes.set_xticklabels([f'Ano {i}' for i in tick_positions], fontsize=8)
        
        if max_years > 15:
            self.axes.tick_params(axis='x', rotation=45)
        
        self.fig.tight_layout(pad=1.5)
        self.draw()


class CompositionChart(FigureCanvas):
    """Gráfico de rosca mostrando composição do saldo final com interatividade."""
    
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(4, 4), facecolor='#ffffff', dpi=100)
        self.axes = self.fig.add_subplot(111)
        
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Dados para tooltip
        self.wedges = None
        self.values = None
        self.labels = None
        self.annotation = None
        
        self._draw_empty()
        
        # Conectar evento de movimento do mouse
        self.mpl_connect('motion_notify_event', self._on_hover)
    
    def _draw_empty(self):
        """Desenha gráfico vazio."""
        self.axes.clear()
        self.axes.text(
            0.5, 0.5, 'Aguardando\nsimulação...',
            transform=self.axes.transAxes,
            ha='center', va='center',
            fontsize=11, color='#95a5a6', style='italic'
        )
        self.axes.axis('off')
        self.fig.tight_layout()
        self.draw()
    
    def _on_hover(self, event):
        """Handler para mostrar tooltip ao passar o mouse."""
        if event.inaxes != self.axes or self.wedges is None:
            if self.annotation:
                self.annotation.set_visible(False)
                self.draw_idle()
            return
        
        # Verificar se o mouse está sobre algum wedge
        for i, wedge in enumerate(self.wedges):
            if wedge.contains_point([event.x, event.y]):
                # Criar ou atualizar annotation
                if self.annotation is None:
                    self.annotation = self.axes.annotate(
                        '',
                        xy=(0, 0),
                        xytext=(0, 0),
                        bbox=dict(
                            boxstyle='round,pad=0.6,rounding_size=0.3',
                            facecolor='#2c3e50',
                            edgecolor='#1a252f',
                            linewidth=1,
                            alpha=0.95
                        ),
                        fontsize=10,
                        color='white',
                        ha='center',
                        va='center',
                        zorder=1000
                    )
                
                # Formatar valor
                value_fmt = f"R$ {self.values[i]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
                # Calcular percentual
                total = sum(self.values)
                percent = (self.values[i] / total * 100) if total > 0 else 0
                
                self.annotation.set_text(f"{self.labels[i]}\n{value_fmt}\n({percent:.1f}%)")
                
                # Posicionar no centro
                self.annotation.xy = (0, 0)
                self.annotation.set_visible(True)
                self.draw_idle()
                return
        
        # Se não está sobre nenhum wedge
        if self.annotation:
            self.annotation.set_visible(False)
            self.draw_idle()
    
    def update_chart(self, total_invested: float, total_interest: float):
        """Atualiza o gráfico de composição."""
        self.axes.clear()
        self.annotation = None
        
        colors = get_colors()
        
        self.values = [total_invested, total_interest]
        self.labels = ['Capital Investido', 'Lucro com Juros']
        chart_colors = ['#5d6d7e', colors['success']]
        
        # Criar gráfico de rosca
        self.wedges, texts = self.axes.pie(
            self.values,
            colors=chart_colors,
            startangle=90,
            wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2)
        )
        
        # Legenda na parte inferior
        self.axes.legend(
            self.wedges, self.labels,
            loc='lower center',
            bbox_to_anchor=(0.5, -0.08),
            frameon=False,
            fontsize=9,
            ncol=2
        )
        
        self.axes.axis('equal')
        self.fig.tight_layout(pad=0.5)
        self.draw()


class ProjectionTable(QTableWidget):
    """Tabela de projeção anual com exportação CSV."""
    
    def __init__(self):
        super().__init__()
        
        # Configuração
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            'Ano', 'Aportes Acum. (R$)', 'Juros Acum. (R$)', 
            'Saldo Total (R$)', '% do Alvo'
        ])
        
        # ========================================================
        # ALINHAMENTO DOS CABEÇALHOS (programático)
        # O QSS nem sempre aplica text-align no QHeaderView,
        # então definimos via código para garantir.
        # ========================================================
        for col in range(self.columnCount()):
            header_item = QTableWidgetItem(self.horizontalHeaderItem(col).text() if self.horizontalHeaderItem(col) else "")
            header_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.setHorizontalHeaderItem(col, header_item)
        
        # Estilo
        self.setAlternatingRowColors(False)  # Desabilitar alternância padrão
        self.setShowGrid(False)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.verticalHeader().setVisible(False)
        
        # Ajustar colunas - todas com Stretch para distribuição uniforme
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        
        # Alinhamento padrão do header (fallback)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Altura das linhas
        self.verticalHeader().setDefaultSectionSize(48)
        
        # Dados para exportação
        self._export_data = []
    
    def update_data(self, result: SimulationResult):
        """Atualiza a tabela com os dados da projeção."""
        colors = get_colors()
        
        self.setRowCount(len(result.yearly_projection))
        self._export_data = []  # Limpar dados anteriores
        
        for row, proj in enumerate(result.yearly_projection):
            # Guardar dados para exportação
            self._export_data.append({
                'Ano': proj.year,
                'Aportes Acum. (R$)': proj.accumulated_contribution,
                'Juros Acum. (R$)': proj.accumulated_interest,
                'Saldo Total (R$)': proj.total_balance,
                '% do Alvo': proj.goal_percentage
            })
            
            # Cor de fundo alternada (aplicada manualmente)
            bg_color = QColor('#ffffff') if row % 2 == 0 else QColor('#f8fffe')
            
            # Ano - alinhado à esquerda
            year_item = QTableWidgetItem(f"Ano {proj.year}")
            year_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            year_item.setForeground(QColor(colors['primary']))
            year_item.setBackground(bg_color)
            font = year_item.font()
            font.setBold(True)
            year_item.setFont(font)
            self.setItem(row, 0, year_item)
            
            # Aportes acumulados - alinhado à esquerda
            contrib_item = QTableWidgetItem(format_currency(proj.accumulated_contribution))
            contrib_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            contrib_item.setBackground(bg_color)
            self.setItem(row, 1, contrib_item)
            
            # Juros acumulados - alinhado à esquerda
            interest_item = QTableWidgetItem(format_currency(proj.accumulated_interest))
            interest_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            interest_item.setForeground(QColor(colors['success']))
            interest_item.setBackground(bg_color)
            self.setItem(row, 2, interest_item)
            
            # Saldo total - alinhado à esquerda com DESTAQUE
            balance_item = QTableWidgetItem(format_currency(proj.total_balance))
            balance_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            balance_item.setForeground(QColor(colors['primary']))  # Cor verde-água
            # Background com destaque suave na coluna de saldo
            highlight_bg = QColor('#e8f6f3') if row % 2 == 0 else QColor('#dff0ed')
            balance_item.setBackground(highlight_bg)
            font = balance_item.font()
            font.setBold(True)
            balance_item.setFont(font)
            self.setItem(row, 3, balance_item)
            
            # % do alvo - alinhado à esquerda
            pct_item = QTableWidgetItem(f"{proj.goal_percentage:.1f}%")
            pct_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            pct_item.setBackground(bg_color)
            self.setItem(row, 4, pct_item)
    
    def export_to_csv(self, filepath: str) -> tuple:
        """
        Exporta os dados da tabela para um arquivo CSV.
        
        Args:
            filepath: Caminho do arquivo CSV a ser criado
            
        Returns:
            Tuple (success: bool, error_message: str ou None)
        """
        if not self._export_data:
            return False, "Nenhum dado disponível para exportação."
        
        try:
            import csv
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                # Detectar colunas disponíveis baseado nos dados
                first_row = self._export_data[0]
                
                # Construir fieldnames dinamicamente baseado nas chaves do primeiro registro
                if 'Saldo (Det.)' in first_row:
                    # Formato Monte Carlo
                    fieldnames = ['Ano', 'Total Investido']
                    
                    # Adicionar colunas de eventos se existirem
                    if 'Aportes Extras' in first_row:
                        fieldnames.extend(['Aportes Extras', 'Resgates'])
                    
                    fieldnames.extend([
                        'Saldo (Det.)', 'Média', 'Mediana', 'Moda', 'Mín', 'P5', 'P90', 'Máx'
                    ])
                else:
                    # Formato antigo
                    fieldnames = [
                        'Ano', 'Aportes Acum. (R$)', 'Juros Acum. (R$)', 
                        'Saldo Total (R$)', '% do Alvo'
                    ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for row_data in self._export_data:
                    # Criar linha formatada com números limpos
                    clean_row = {}
                    for key in fieldnames:
                        value = row_data.get(key, 0)
                        if key == 'Ano':
                            clean_row[key] = value
                        elif key == '% do Alvo':
                            clean_row[key] = f"{value:.1f}%"
                        elif isinstance(value, (int, float)):
                            # Número puro com vírgula decimal (padrão BR)
                            clean_row[key] = f"{value:.2f}".replace('.', ',')
                        else:
                            clean_row[key] = value
                    
                    writer.writerow(clean_row)
            
            return True, None
            
        except PermissionError:
            return False, "Permissão negada. O arquivo pode estar aberto em outro programa."
        except OSError as e:
            return False, f"Erro de sistema de arquivos: {e}"
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}"
    
    def has_data(self) -> bool:
        """Verifica se há dados para exportar."""
        return len(self._export_data) > 0
    
    def update_data_monte_carlo(self, result: MonteCarloResult):
        """Atualiza a tabela com dados de Monte Carlo expandidos."""
        colors = get_colors()
        
        # Verificar se há eventos extraordinários
        has_events = any(
            getattr(proj, 'extra_deposits', 0) > 0 or getattr(proj, 'withdrawals', 0) > 0 
            for proj in result.yearly_projection
        )
        
        # Reconfigurar colunas para Monte Carlo
        if has_events:
            self.setColumnCount(12)
            self.setHorizontalHeaderLabels([
                'Ano', 'Total Investido', 'Aportes Extras', 'Resgates',
                'Saldo (Det.)', 'Média', 'Mediana', 'Moda', 'Mín', 'P5', 'P90', 'Máx'
            ])
        else:
            self.setColumnCount(10)
            self.setHorizontalHeaderLabels([
                'Ano', 'Total Investido', 'Saldo (Det.)', 
                'Média', 'Mediana', 'Moda', 'Mín', 'P5', 'P90', 'Máx'
            ])
        
        # Reconfigurar header
        for col in range(self.columnCount()):
            header_item = QTableWidgetItem(self.horizontalHeaderItem(col).text() if self.horizontalHeaderItem(col) else "")
            header_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.setHorizontalHeaderItem(col, header_item)
        
        header = self.horizontalHeader()
        for col in range(self.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.setRowCount(len(result.yearly_projection))
        self._export_data = []
        
        for row, proj in enumerate(result.yearly_projection):
            extra_deposits = getattr(proj, 'extra_deposits', 0.0)
            withdrawals = getattr(proj, 'withdrawals', 0.0)
            
            # Guardar dados para exportação
            export_row = {
                'Ano': proj.year,
                'Total Investido': proj.total_invested,
                'Saldo (Det.)': proj.balance_deterministic,
                'Média': proj.balance_mean,
                'Mediana': getattr(proj, 'balance_median', proj.balance_mean),
                'Moda': getattr(proj, 'balance_mode', proj.balance_mean),
                'Mín': proj.balance_min,
                'P5': getattr(proj, 'balance_p5', proj.balance_min),
                'P90': proj.balance_p90,
                'Máx': proj.balance_max
            }
            
            if has_events:
                export_row['Aportes Extras'] = extra_deposits
                export_row['Resgates'] = withdrawals
            
            self._export_data.append(export_row)
            
            bg_color = QColor('#ffffff') if row % 2 == 0 else QColor('#f8fffe')
            col_idx = 0
            
            # Ano
            year_item = QTableWidgetItem(f"Ano {proj.year}")
            year_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            year_item.setForeground(QColor(colors['primary']))
            year_item.setBackground(bg_color)
            font = year_item.font()
            font.setBold(True)
            year_item.setFont(font)
            self.setItem(row, col_idx, year_item)
            col_idx += 1
            
            # Total Investido
            invested_item = QTableWidgetItem(format_currency(proj.total_invested))
            invested_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            invested_item.setBackground(bg_color)
            self.setItem(row, col_idx, invested_item)
            col_idx += 1
            
            # Colunas de eventos (se houver)
            if has_events:
                # Aportes Extras
                deposits_item = QTableWidgetItem(
                    format_currency(extra_deposits) if extra_deposits > 0 else "—"
                )
                deposits_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if extra_deposits > 0:
                    deposits_item.setForeground(QColor('#059669'))
                else:
                    deposits_item.setForeground(QColor('#9CA3AF'))
                deposits_item.setBackground(bg_color)
                self.setItem(row, col_idx, deposits_item)
                col_idx += 1
                
                # Resgates
                withdrawals_item = QTableWidgetItem(
                    format_currency(withdrawals) if withdrawals > 0 else "—"
                )
                withdrawals_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if withdrawals > 0:
                    withdrawals_item.setForeground(QColor('#DC2626'))
                else:
                    withdrawals_item.setForeground(QColor('#9CA3AF'))
                withdrawals_item.setBackground(bg_color)
                self.setItem(row, col_idx, withdrawals_item)
                col_idx += 1
            
            # Saldo Determinístico (destacado)
            det_item = QTableWidgetItem(format_currency(proj.balance_deterministic))
            det_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            det_item.setForeground(QColor(colors['primary']))
            highlight_bg = QColor('#e8f6f3') if row % 2 == 0 else QColor('#dff0ed')
            det_item.setBackground(highlight_bg)
            font = det_item.font()
            font.setBold(True)
            det_item.setFont(font)
            self.setItem(row, col_idx, det_item)
            col_idx += 1
            
            # Média (vermelho suave)
            mean_item = QTableWidgetItem(format_currency(proj.balance_mean))
            mean_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            mean_item.setForeground(QColor('#e74c3c'))
            mean_item.setBackground(bg_color)
            self.setItem(row, col_idx, mean_item)
            col_idx += 1
            
            # Mediana (roxo)
            median_value = getattr(proj, 'balance_median', proj.balance_mean)
            median_item = QTableWidgetItem(format_currency(median_value))
            median_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            median_item.setForeground(QColor('#9b59b6'))
            median_item.setBackground(bg_color)
            self.setItem(row, col_idx, median_item)
            col_idx += 1
            
            # Moda (laranja)
            mode_value = getattr(proj, 'balance_mode', proj.balance_mean)
            mode_item = QTableWidgetItem(format_currency(mode_value))
            mode_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            mode_item.setForeground(QColor('#e67e22'))
            mode_item.setBackground(bg_color)
            self.setItem(row, col_idx, mode_item)
            col_idx += 1
            
            # Mínimo (cinza)
            min_item = QTableWidgetItem(format_currency(proj.balance_min))
            min_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            min_item.setForeground(QColor('#7f8c8d'))
            min_item.setBackground(bg_color)
            self.setItem(row, col_idx, min_item)
            col_idx += 1
            
            # P5 (vermelho escuro)
            p5_value = getattr(proj, 'balance_p5', proj.balance_min)
            p5_item = QTableWidgetItem(format_currency(p5_value))
            p5_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            p5_item.setForeground(QColor('#c0392b'))
            p5_item.setBackground(bg_color)
            self.setItem(row, col_idx, p5_item)
            col_idx += 1
            
            # P90 (verde)
            p90_item = QTableWidgetItem(format_currency(proj.balance_p90))
            p90_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            p90_item.setForeground(QColor('#27ae60'))
            p90_item.setBackground(bg_color)
            self.setItem(row, col_idx, p90_item)
            col_idx += 1
            
            # Máximo (azul)
            max_item = QTableWidgetItem(format_currency(proj.balance_max))
            max_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            max_item.setForeground(QColor('#3498db'))
            max_item.setBackground(bg_color)
            self.setItem(row, col_idx, max_item)


class AnalysisBox(QFrame):
    """Caixa de análise textual da simulação."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("analysis_box")
        self.setStyleSheet("""
            QFrame#analysis_box {
                background-color: rgba(16, 185, 129, 0.06);
                border-left: 4px solid #10B981;
                border-radius: 0px 12px 12px 0px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("📊 Análise da Simulação")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1F2937;
            margin-bottom: 8px;
            background: transparent;
        """)
        layout.addWidget(title)
        
        # Texto da análise (suporta HTML)
        self.analysis_label = QLabel("")
        self.analysis_label.setObjectName("analysis_text")
        self.analysis_label.setWordWrap(True)
        self.analysis_label.setTextFormat(Qt.RichText)
        self.analysis_label.setStyleSheet("""
            font-size: 13px;
            color: #374151;
            line-height: 1.7;
            background: transparent;
        """)
        layout.addWidget(self.analysis_label)
    
    def update_analysis(self, result: SimulationResult):
        """Atualiza o texto da análise."""
        a = result.analysis
        
        # Formatar valores
        initial = format_currency(a.initial_investment)
        monthly = format_currency(a.monthly_contribution)
        final = format_currency(a.final_balance)
        interest = format_currency(a.total_interest)
        goal = format_currency(a.goal_amount) if a.goal_amount > 0 else "não definida"
        
        lines = [
            f"• Seu investimento inicial de {initial} + {monthly}/mês",
            f"• Com rentabilidade de {a.annual_rate:.2f}% a.a. resulta em {final}",
            f"• Lucro com juros compostos: {interest}",
        ]
        
        if a.goal_amount > 0:
            if a.goal_achieved:
                lines.append(
                    f"• Para atingir {goal}, você precisaria de aproximadamente "
                    f"<b>{a.years_to_goal:.1f} anos</b>"
                )
            else:
                lines.append(
                    f"• Meta de {goal} não atingida no período "
                    f"({a.goal_percentage:.1f}% alcançado)"
                )
        
        lines.append(f"• Rentabilidade total: {a.total_return_percentage:.2f}%")
        
        self.analysis_label.setText("<br>".join(lines))


# =============================================================================
# SENSITIVITY DASHBOARD - Painel de Insights de Sensibilidade
# =============================================================================

class InsightCard(QFrame):
    """Card individual de insight com borda colorida à esquerda."""
    
    # Cores para cada tipo de insight
    COLORS = {
        'tempo': '#8e44ad',      # Roxo
        'aporte': '#00bcd4',     # Azul Cyan
        'capital': '#4caf50',    # Verde Lima
        'taxa': '#e74c3c'        # Vermelho Suave
    }
    
    # Ícones Unicode para cada tipo
    ICONS = {
        'tempo': '⏱️',
        'aporte': '💰',
        'capital': '🏦',
        'taxa': '📈'
    }
    
    def __init__(self, card_type: str, title: str, description: str):
        super().__init__()
        
        self.card_type = card_type
        self.title_text = title
        self.description_text = description
        
        color = self.COLORS.get(card_type, '#16a085')
        icon = self.ICONS.get(card_type, '📊')
        
        # Estilo do card com borda esquerda colorida
        self.setStyleSheet(f"""
            InsightCard {{
                background-color: #ffffff;
                border: 1px solid #e8e8e8;
                border-left: 5px solid {color};
                border-radius: 8px;
            }}
            InsightCard:hover {{
                background-color: #fafafa;
                border-color: #d0d0d0;
                border-left: 5px solid {color};
            }}
        """)
        
        self.setMinimumHeight(140)
        self.setMaximumHeight(180)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        
        # Header com ícone e título
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Ícone
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            font-size: 18px;
            background: transparent;
        """)
        header_layout.addWidget(icon_label)
        
        # Título
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {color};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: transparent;
        """)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Valor em destaque
        self.value_label = QLabel("—")
        self.value_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            background: transparent;
            padding: 4px 0px;
        """)
        layout.addWidget(self.value_label)
        
        # Texto explicativo
        self.desc_label = QLabel(description)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("""
            font-size: 11px;
            color: #7f8c8d;
            line-height: 1.4;
            background: transparent;
        """)
        layout.addWidget(self.desc_label)
        
        layout.addStretch()
    
    def set_value(self, value: str):
        """Atualiza o valor exibido no card."""
        self.value_label.setText(value)


class SensitivityDashboard(QWidget):
    """
    Dashboard de sensibilidade com 4 cards de insights.
    Exibe as derivadas parciais do montante de forma didática.
    """
    
    def __init__(self):
        super().__init__()
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)
        
        # Título da seção
        title = QLabel("📊 Insights de Sensibilidade")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px 0px;
            background: transparent;
        """)
        main_layout.addWidget(title)
        
        # Subtítulo explicativo
        subtitle = QLabel("Como cada variável impacta seu patrimônio final")
        subtitle.setStyleSheet("""
            font-size: 12px;
            color: #95a5a6;
            margin-bottom: 8px;
            background: transparent;
        """)
        main_layout.addWidget(subtitle)
        
        # Container dos cards com fundo suave
        cards_container = QFrame()
        cards_container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        # Grid 2x2 para os cards
        from PySide6.QtWidgets import QGridLayout
        grid_layout = QGridLayout(cards_container)
        grid_layout.setContentsMargins(12, 12, 12, 12)
        grid_layout.setSpacing(12)
        
        # Card 1: Velocidade Atual (dM/dt) - Tempo
        self.card_velocidade = InsightCard(
            card_type='tempo',
            title='Velocidade Atual',
            description='Neste exato momento, seu patrimônio cresce essa quantia por ano, apenas pelos juros, sem você fazer nada.'
        )
        grid_layout.addWidget(self.card_velocidade, 0, 0)
        
        # Card 2: Potência do Aporte (dM/da) - Aporte
        self.card_potencia = InsightCard(
            card_type='aporte',
            title='Potência do Aporte',
            description='Para cada R$ 1,00 a mais que você aportar por ano, seu montante final aumenta este valor multiplicador.'
        )
        grid_layout.addWidget(self.card_potencia, 0, 1)
        
        # Card 3: Eficiência do Capital (dM/dC) - Capital
        self.card_eficiencia = InsightCard(
            card_type='capital',
            title='Eficiência do Capital',
            description='Cada R$ 1,00 que você investiu lá no início se multiplicou por este fator até o final do período.'
        )
        grid_layout.addWidget(self.card_eficiencia, 1, 0)
        
        # Card 4: Sensibilidade à Taxa (dM/di) - Taxa
        self.card_taxa = InsightCard(
            card_type='taxa',
            title='Sensibilidade à Taxa',
            description='Se você conseguir apenas 1% a mais de rentabilidade anual, seu saldo final aumentaria aproximadamente este valor.'
        )
        grid_layout.addWidget(self.card_taxa, 1, 1)
        
        main_layout.addWidget(cards_container)
    
    def update_sensitivities(
        self, 
        initial_amount: float,
        monthly_contribution: float,
        annual_rate: float,
        years: int,
        final_balance: float = None
    ):
        """
        Atualiza os valores dos cards com base nos parâmetros.
        
        Args:
            initial_amount: Capital inicial (R$)
            monthly_contribution: Aporte mensal (R$)
            annual_rate: Taxa anual (%)
            years: Período em anos
            final_balance: Saldo final opcional (para usar com P50 no Modo Expert)
        """
        from core.calculation import InvestmentCalculator
        
        # Calcular sensibilidades
        calculator = InvestmentCalculator(
            C=initial_amount,
            i_anual=annual_rate,
            t_anos=years,
            a_mensal=monthly_contribution
        )
        
        metrics = calculator.get_sensitivities()
        
        # Formatar e atualizar os valores
        # Card 1: Velocidade - R$/ano
        velocidade_fmt = f"R$ {metrics.velocidade:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " / ano"
        self.card_velocidade.set_value(velocidade_fmt)
        
        # Card 2: Potência do Aporte - Multiplicador
        self.card_potencia.set_value(f"x {metrics.potencia_aporte:.2f}")
        
        # Card 3: Eficiência do Capital - Multiplicador
        self.card_eficiencia.set_value(f"x {metrics.eficiencia_capital:.2f}")
        
        # Card 4: Sensibilidade à Taxa - R$ por 1% de taxa
        # Dividir por 100 para mostrar o impacto de 1% (não 100%)
        sensib_1pct = metrics.sensibilidade_taxa / 100
        sensib_fmt = f"R$ {sensib_1pct:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        self.card_taxa.set_value(sensib_fmt)
    
    def update_from_result(self, result):
        """
        Atualiza os cards a partir de um MonteCarloResult.
        
        Args:
            result: MonteCarloResult com params_used
        """
        if hasattr(result, 'params_used'):
            params = result.params_used
            self.update_sensitivities(
                initial_amount=params.get('capital_inicial', 0),
                monthly_contribution=params.get('aporte_mensal', 0),
                annual_rate=params.get('rentabilidade_anual', 0),
                years=params.get('periodo_anos', 10)
            )
    
    def reset(self):
        """Reseta todos os cards para o estado inicial."""
        self.card_velocidade.set_value("—")
        self.card_potencia.set_value("—")
        self.card_eficiencia.set_value("—")
        self.card_taxa.set_value("—")
