"""
PyInvest - Widgets Personalizados
Componentes reutilizáveis da interface.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QWidget, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from core.calculation import format_currency, SimulationResult
from ui.styles import get_colors


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
    """Gráfico de evolução do patrimônio."""
    
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 5), facecolor='#ffffff')
        self.axes = self.fig.add_subplot(111)
        
        super().__init__(self.fig)
        self.setParent(parent)
        
        self._setup_style()
        self._draw_empty()
    
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
    
    def update_chart(self, result: SimulationResult):
        """Atualiza o gráfico com os dados da simulação."""
        self.axes.clear()
        self._setup_style()
        
        colors = get_colors()
        
        # Converter meses para anos para o eixo X
        years = result.months / 12
        
        # Área preenchida
        self.axes.fill_between(
            years, result.balances, 
            alpha=0.2, color=colors['primary']
        )
        
        # Linha com marcadores (apenas pontos anuais)
        annual_indices = [i for i in range(len(result.months)) if i % 12 == 0]
        annual_years = years[annual_indices]
        annual_balances = result.balances[annual_indices]
        
        # Linha contínua
        self.axes.plot(
            years, result.balances,
            color=colors['primary'], linewidth=2
        )
        
        # Marcadores apenas nos pontos anuais
        self.axes.scatter(
            annual_years, annual_balances,
            color=colors['primary'], s=50, zorder=5,
            edgecolors='white', linewidths=2
        )
        
        # Labels
        self.axes.set_xlabel('', fontsize=10, color='#7f8c8d')
        self.axes.set_ylabel('', fontsize=10, color='#7f8c8d')
        
        # Título e legenda
        self.axes.legend(
            ['Saldo Total (R$)'], 
            loc='upper left',
            frameon=True,
            facecolor='white',
            edgecolor='#e0e0e0',
            fontsize=10
        )
        
        # Formatação do eixo Y
        self.axes.yaxis.set_major_formatter(
            lambda x, p: f'R$ {x/1000:,.0f}'.replace(',', '.') + '' if x >= 1000 else f'R$ {x:,.0f}'
        )
        
        # Formatação do eixo X
        max_years = int(years[-1])
        self.axes.set_xticks(range(0, max_years + 1))
        self.axes.set_xticklabels([f'Ano {i}' for i in range(0, max_years + 1)])
        
        self.fig.tight_layout()
        self.draw()


class CompositionChart(FigureCanvas):
    """Gráfico de rosca mostrando composição do saldo final."""
    
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 5), facecolor='#ffffff')
        self.axes = self.fig.add_subplot(111)
        
        super().__init__(self.fig)
        self.setParent(parent)
        
        self._draw_empty()
    
    def _draw_empty(self):
        """Desenha gráfico vazio."""
        self.axes.text(
            0.5, 0.5, 'Aguardando\nsimulação...',
            transform=self.axes.transAxes,
            ha='center', va='center',
            fontsize=11, color='#95a5a6', style='italic'
        )
        self.axes.axis('off')
        self.fig.tight_layout()
        self.draw()
    
    def update_chart(self, total_invested: float, total_interest: float):
        """Atualiza o gráfico de composição."""
        self.axes.clear()
        
        colors = get_colors()
        
        values = [total_invested, total_interest]
        labels = ['Capital Investido', 'Lucro com Juros']
        chart_colors = ['#5d6d7e', colors['success']]
        
        # Criar gráfico de rosca
        wedges, texts = self.axes.pie(
            values,
            colors=chart_colors,
            startangle=90,
            wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2)
        )
        
        # Legenda
        self.axes.legend(
            wedges, labels,
            loc='lower center',
            bbox_to_anchor=(0.5, -0.05),
            frameon=False,
            fontsize=10,
            ncol=2
        )
        
        self.axes.axis('equal')
        self.fig.tight_layout()
        self.draw()


class ProjectionTable(QTableWidget):
    """Tabela de projeção anual."""
    
    def __init__(self):
        super().__init__()
        
        # Configuração
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            'Ano', 'Aportes Acum. (R$)', 'Juros Acum. (R$)', 
            'Saldo Total (R$)', '% do Alvo'
        ])
        
        # Estilo
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.verticalHeader().setVisible(False)
        
        # Ajustar colunas
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.setColumnWidth(0, 80)
        self.setColumnWidth(4, 100)
        
        # Altura das linhas
        self.verticalHeader().setDefaultSectionSize(45)
    
    def update_data(self, result: SimulationResult):
        """Atualiza a tabela com os dados da projeção."""
        colors = get_colors()
        
        self.setRowCount(len(result.yearly_projection))
        
        for row, proj in enumerate(result.yearly_projection):
            # Ano
            year_item = QTableWidgetItem(f"Ano {proj.year}")
            year_item.setTextAlignment(Qt.AlignCenter)
            year_item.setForeground(QColor(colors['primary']))
            font = year_item.font()
            font.setBold(True)
            year_item.setFont(font)
            self.setItem(row, 0, year_item)
            
            # Aportes acumulados
            contrib_item = QTableWidgetItem(format_currency(proj.accumulated_contribution))
            contrib_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.setItem(row, 1, contrib_item)
            
            # Juros acumulados
            interest_item = QTableWidgetItem(format_currency(proj.accumulated_interest))
            interest_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            interest_item.setForeground(QColor(colors['success']))
            self.setItem(row, 2, interest_item)
            
            # Saldo total
            balance_item = QTableWidgetItem(format_currency(proj.total_balance))
            balance_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            balance_item.setForeground(QColor(colors['info']))
            font = balance_item.font()
            font.setBold(True)
            balance_item.setFont(font)
            self.setItem(row, 3, balance_item)
            
            # % do alvo
            pct_item = QTableWidgetItem(f"{proj.goal_percentage:.1f}%")
            pct_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 4, pct_item)
            
            # Cor de fundo alternada
            if row % 2 == 1:
                for col in range(5):
                    item = self.item(row, col)
                    if item:
                        item.setBackground(QColor('#f9fbfc'))


class AnalysisBox(QFrame):
    """Caixa de análise textual da simulação."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("analysis_box")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        
        # Título
        title = QLabel("Análise da Simulação:")
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        """)
        layout.addWidget(title)
        
        # Texto da análise
        self.analysis_label = QLabel("")
        self.analysis_label.setObjectName("analysis_text")
        self.analysis_label.setWordWrap(True)
        self.analysis_label.setStyleSheet("""
            font-size: 13px;
            color: #2c3e50;
            line-height: 1.8;
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
