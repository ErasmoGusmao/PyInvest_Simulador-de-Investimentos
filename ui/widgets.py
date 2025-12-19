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
        years: int
    ):
        """
        Atualiza os valores dos cards com base nos parâmetros.
        
        Args:
            initial_amount: Capital inicial (R$)
            monthly_contribution: Aporte mensal (R$)
            annual_rate: Taxa anual (%)
            years: Período em anos
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
    
    def reset(self):
        """Reseta todos os cards para o estado inicial."""
        self.card_velocidade.set_value("—")
        self.card_potencia.set_value("—")
        self.card_eficiencia.set_value("—")
        self.card_taxa.set_value("—")
