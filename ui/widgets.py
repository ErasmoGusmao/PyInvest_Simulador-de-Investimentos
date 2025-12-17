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
    """Gráfico de evolução do patrimônio com interatividade."""
    
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 4), facecolor='#ffffff', dpi=100)
        self.axes = self.fig.add_subplot(111)
        
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Dados para tooltip
        self.annual_data = None
        self.invested_data = None
        self.annotation = None
        
        self._setup_style()
        self._draw_empty()
        
        # Conectar evento de movimento do mouse
        self.mpl_connect('motion_notify_event', self._on_hover)
    
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
    
    def _on_hover(self, event):
        """Handler para mostrar tooltip ao passar o mouse."""
        if event.inaxes != self.axes or self.annual_data is None:
            if self.annotation:
                self.annotation.set_visible(False)
                self.draw_idle()
            return
        
        # Encontrar o ponto mais próximo
        x = event.xdata
        if x is None:
            return
            
        # Encontrar o ano mais próximo
        year_idx = int(round(x))
        if 0 <= year_idx < len(self.annual_data['years']):
            year = self.annual_data['years'][year_idx]
            balance = self.annual_data['balances'][year_idx]
            invested = self.invested_data[year_idx] if self.invested_data is not None else 0
            
            # Criar ou atualizar annotation
            if self.annotation is None:
                self.annotation = self.axes.annotate(
                    '',
                    xy=(0, 0),
                    xytext=(15, 15),
                    textcoords='offset points',
                    bbox=dict(
                        boxstyle='round,pad=0.5',
                        facecolor='#2c3e50',
                        edgecolor='none',
                        alpha=0.9
                    ),
                    fontsize=9,
                    color='white'
                )
            
            # Formatar texto do tooltip
            balance_fmt = f"R$ {balance:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            invested_fmt = f"R$ {invested:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            self.annotation.set_text(
                f"Ano {year}\n"
                f"Saldo Total: {balance_fmt}\n"
                f"Investido: {invested_fmt}"
            )
            self.annotation.xy = (year, balance)
            self.annotation.set_visible(True)
            self.draw_idle()
    
    def update_chart(self, result: SimulationResult):
        """Atualiza o gráfico com os dados da simulação."""
        self.axes.clear()
        self._setup_style()
        self.annotation = None
        
        colors = get_colors()
        
        # Converter meses para anos para o eixo X
        years = result.months / 12
        max_years = int(years[-1])
        
        # Calcular linha de capital investido
        initial = result.analysis.initial_investment
        monthly = result.analysis.monthly_contribution
        invested_line = initial + (monthly * result.months)
        
        # Área preenchida para saldo total
        self.axes.fill_between(
            years, result.balances, 
            alpha=0.15, color=colors['primary']
        )
        
        # Pontos anuais para interatividade
        annual_indices = [i for i in range(len(result.months)) if i % 12 == 0]
        annual_years = [int(years[i]) for i in annual_indices]
        annual_balances = [result.balances[i] for i in annual_indices]
        annual_invested = [invested_line[i] for i in annual_indices]
        
        # Guardar dados para tooltip
        self.annual_data = {
            'years': annual_years,
            'balances': annual_balances
        }
        self.invested_data = annual_invested
        
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
        
        # Linha do capital investido (tracejada)
        line2, = self.axes.plot(
            years, invested_line,
            color='#5d6d7e', linewidth=2, linestyle='--',
            label='Capital Investido (R$)', alpha=0.8
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
                            boxstyle='round,pad=0.5',
                            facecolor='#2c3e50',
                            edgecolor='none',
                            alpha=0.9
                        ),
                        fontsize=9,
                        color='white',
                        ha='center',
                        va='center'
                    )
                
                # Formatar valor
                value_fmt = f"R$ {self.values[i]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
                self.annotation.set_text(f"{self.labels[i]}: {value_fmt}")
                
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
            
            # Ano - alinhado à esquerda
            year_item = QTableWidgetItem(f"Ano {proj.year}")
            year_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            year_item.setForeground(QColor(colors['primary']))
            font = year_item.font()
            font.setBold(True)
            year_item.setFont(font)
            self.setItem(row, 0, year_item)
            
            # Aportes acumulados - alinhado à esquerda
            contrib_item = QTableWidgetItem(format_currency(proj.accumulated_contribution))
            contrib_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.setItem(row, 1, contrib_item)
            
            # Juros acumulados - alinhado à esquerda
            interest_item = QTableWidgetItem(format_currency(proj.accumulated_interest))
            interest_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            interest_item.setForeground(QColor(colors['success']))
            self.setItem(row, 2, interest_item)
            
            # Saldo total - alinhado à esquerda
            balance_item = QTableWidgetItem(format_currency(proj.total_balance))
            balance_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            balance_item.setForeground(QColor(colors['info']))
            font = balance_item.font()
            font.setBold(True)
            balance_item.setFont(font)
            self.setItem(row, 3, balance_item)
            
            # % do alvo - alinhado ao centro
            pct_item = QTableWidgetItem(f"{proj.goal_percentage:.1f}%")
            pct_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 4, pct_item)
            
            # Cor de fundo alternada
            if row % 2 == 1:
                for col in range(5):
                    item = self.item(row, col)
                    if item:
                        item.setBackground(QColor('#f9fbfc'))
    
    def export_to_csv(self, filepath: str) -> bool:
        """
        Exporta os dados da tabela para um arquivo CSV.
        
        Args:
            filepath: Caminho do arquivo CSV a ser criado
            
        Returns:
            True se exportou com sucesso, False caso contrário
        """
        if not self._export_data:
            return False
        
        try:
            import csv
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['Ano', 'Aportes Acum. (R$)', 'Juros Acum. (R$)', 
                             'Saldo Total (R$)', '% do Alvo']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                
                writer.writeheader()
                for row_data in self._export_data:
                    # Formatar valores para CSV
                    writer.writerow({
                        'Ano': row_data['Ano'],
                        'Aportes Acum. (R$)': f"{row_data['Aportes Acum. (R$)']:.2f}".replace('.', ','),
                        'Juros Acum. (R$)': f"{row_data['Juros Acum. (R$)']:.2f}".replace('.', ','),
                        'Saldo Total (R$)': f"{row_data['Saldo Total (R$)']:.2f}".replace('.', ','),
                        '% do Alvo': f"{row_data['% do Alvo']:.1f}%"
                    })
            
            return True
        except Exception as e:
            print(f"Erro ao exportar CSV: {e}")
            return False
    
    def has_data(self) -> bool:
        """Verifica se há dados para exportar."""
        return len(self._export_data) > 0


class AnalysisBox(QFrame):
    """Caixa de análise textual da simulação."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("analysis_box")
        self.setStyleSheet("""
            QFrame#analysis_box {
                background-color: rgba(22, 160, 133, 0.08);
                border-left: 4px solid #16a085;
                border-radius: 0px 8px 8px 0px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("Análise da Simulação:")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
            background: transparent;
        """)
        layout.addWidget(title)
        
        # Texto da análise
        self.analysis_label = QLabel("")
        self.analysis_label.setObjectName("analysis_text")
        self.analysis_label.setWordWrap(True)
        self.analysis_label.setStyleSheet("""
            font-size: 14px;
            color: #2c3e50;
            line-height: 1.8;
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