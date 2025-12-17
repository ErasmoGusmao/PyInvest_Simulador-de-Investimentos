"""
PyInvest - Interface Gráfica Principal
Dashboard moderno para simulação de investimentos.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy,
    QSpacerItem, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QDoubleValidator, QIntValidator

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core.calculation import calculate_compound_interest, format_currency


# ============================================================================
# FOLHA DE ESTILOS QSS - TEMA ESCURO MODERNO
# ============================================================================

DARK_STYLE = """
QMainWindow {
    background-color: #1a1a2e;
}

QWidget {
    background-color: #1a1a2e;
    color: #eaeaea;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QFrame#sidebar {
    background-color: #16213e;
    border-radius: 10px;
    padding: 15px;
}

QFrame#card {
    background-color: #0f3460;
    border-radius: 8px;
    padding: 15px;
    min-height: 80px;
}

QLabel {
    color: #eaeaea;
}

QLabel#title {
    font-size: 24px;
    font-weight: bold;
    color: #e94560;
}

QLabel#subtitle {
    font-size: 12px;
    color: #a0a0a0;
}

QLabel#card_title {
    font-size: 11px;
    color: #a0a0a0;
    font-weight: normal;
}

QLabel#card_value {
    font-size: 20px;
    font-weight: bold;
    color: #00d9ff;
}

QLabel#card_value_green {
    font-size: 20px;
    font-weight: bold;
    color: #00ff88;
}

QLabel#card_value_gold {
    font-size: 20px;
    font-weight: bold;
    color: #ffd700;
}

/* =========================================================================
   CORREÇÃO: QLineEdit com altura mínima e padding adequado
   ========================================================================= */
QLineEdit {
    background-color: #0f3460;
    border: 2px solid #1a1a2e;
    border-radius: 6px;
    padding: 12px 15px;
    font-size: 14px;
    color: #ffffff;
    min-height: 20px;
}

QLineEdit:focus {
    border: 2px solid #e94560;
}

QLineEdit:hover {
    border: 2px solid #533483;
}

/* =========================================================================
   CORREÇÃO: Botões com altura mínima fixa e padding vertical maior
   ========================================================================= */
QPushButton#primary {
    background-color: #e94560;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 14px 20px;
    font-size: 14px;
    font-weight: bold;
    min-height: 24px;
}

QPushButton#primary:hover {
    background-color: #ff6b6b;
}

QPushButton#primary:pressed {
    background-color: #c73e54;
}

QPushButton#secondary {
    background-color: transparent;
    color: #e94560;
    border: 2px solid #e94560;
    border-radius: 6px;
    padding: 12px 20px;
    font-size: 13px;
    min-height: 20px;
}

QPushButton#secondary:hover {
    background-color: #e94560;
    color: white;
}
"""


class SummaryCard(QFrame):
    """Card de resumo estilizado."""
    
    def __init__(self, title: str, value: str = "R$ 0,00", color_style: str = "card_value"):
        super().__init__()
        self.setObjectName("card")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Título do card
        self.title_label = QLabel(title)
        self.title_label.setObjectName("card_title")
        
        # Valor do card
        self.value_label = QLabel(value)
        self.value_label.setObjectName(color_style)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()
    
    def set_value(self, value: str):
        """Atualiza o valor exibido no card."""
        self.value_label.setText(value)


class ChartCanvas(FigureCanvas):
    """Canvas do Matplotlib integrado ao Qt."""
    
    def __init__(self, parent=None):
        # Cria a figura com fundo transparente
        self.fig = Figure(figsize=(10, 6), facecolor='#1a1a2e')
        self.axes = self.fig.add_subplot(111)
        
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Configuração inicial do gráfico
        self._setup_style()
        self._draw_empty_chart()
    
    def _setup_style(self):
        """Configura o estilo visual do gráfico."""
        self.axes.set_facecolor('#1a1a2e')
        
        # Cor dos eixos e labels
        self.axes.tick_params(colors='#a0a0a0', labelsize=9)
        self.axes.spines['bottom'].set_color('#333355')
        self.axes.spines['left'].set_color('#333355')
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        
        # Grid sutil
        self.axes.grid(True, linestyle='--', alpha=0.2, color='#555577')
    
    def _draw_empty_chart(self):
        """Desenha um gráfico vazio inicial."""
        self.axes.set_xlabel('Meses', color='#a0a0a0', fontsize=10)
        self.axes.set_ylabel('Valor (R$)', color='#a0a0a0', fontsize=10)
        self.axes.set_title('Evolução do Patrimônio', color='#eaeaea', fontsize=14, pad=15)
        
        # Texto informativo
        self.axes.text(
            0.5, 0.5, 'Insira os dados e clique em\n"Calcular Simulação"',
            transform=self.axes.transAxes,
            ha='center', va='center',
            fontsize=12, color='#666688',
            style='italic'
        )
        
        self.fig.tight_layout()
        self.draw()
    
    def update_chart(self, months, balances, total_invested_line):
        """Atualiza o gráfico com os novos dados."""
        self.axes.clear()
        self._setup_style()
        
        # Linha do patrimônio total
        self.axes.fill_between(
            months, balances, alpha=0.3, color='#00d9ff'
        )
        self.axes.plot(
            months, balances, 
            color='#00d9ff', linewidth=2.5, label='Patrimônio Total'
        )
        
        # Linha do total investido (sem juros)
        self.axes.plot(
            months, total_invested_line,
            color='#e94560', linewidth=2, linestyle='--', 
            label='Total Investido', alpha=0.8
        )
        
        # Labels e título
        self.axes.set_xlabel('Meses', color='#a0a0a0', fontsize=10)
        self.axes.set_ylabel('Valor (R$)', color='#a0a0a0', fontsize=10)
        self.axes.set_title('Evolução do Patrimônio', color='#eaeaea', fontsize=14, pad=15)
        
        # Legenda
        legend = self.axes.legend(
            loc='upper left', 
            facecolor='#16213e', 
            edgecolor='#333355',
            fontsize=9
        )
        for text in legend.get_texts():
            text.set_color('#eaeaea')
        
        # Formatação do eixo Y para valores monetários
        self.axes.yaxis.set_major_formatter(
            lambda x, p: f'R$ {x/1000:.0f}k' if x >= 1000 else f'R$ {x:.0f}'
        )
        
        self.fig.tight_layout()
        self.draw()


class MainWindow(QMainWindow):
    """Janela principal da aplicação PyInvest."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PyInvest - Simulador de Investimentos")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet(DARK_STYLE)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal (horizontal)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Cria as duas áreas principais
        self._create_sidebar(main_layout)
        self._create_dashboard(main_layout)
    
    def _create_sidebar(self, parent_layout: QHBoxLayout):
        """Cria o painel lateral com os inputs."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(320)
        
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(15)  # CORREÇÃO: Reduzi spacing para melhor distribuição
        layout.setContentsMargins(20, 25, 20, 25)
        
        # Título
        title = QLabel("PyInvest")
        title.setObjectName("title")
        layout.addWidget(title)
        
        subtitle = QLabel("Simulador de Juros Compostos")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        
        layout.addSpacing(15)
        
        # Campos de entrada
        self.input_initial = self._create_input_field(
            layout, "Montante Inicial", "R$ 10.000,00", is_currency=True
        )
        
        self.input_monthly = self._create_input_field(
            layout, "Aporte Mensal", "R$ 1.000,00", is_currency=True
        )
        
        self.input_rate = self._create_input_field(
            layout, "Taxa de Juros Anual (%)", "12.0", is_percent=True
        )
        
        self.input_years = self._create_input_field(
            layout, "Tempo (Anos)", "10", is_integer=True
        )
        
        layout.addSpacing(10)
        
        # Botão calcular - CORREÇÃO: Altura fixa definida programaticamente
        btn_calculate = QPushButton("📊  Calcular Simulação")
        btn_calculate.setObjectName("primary")
        btn_calculate.setCursor(Qt.PointingHandCursor)
        btn_calculate.setFixedHeight(48)  # CORREÇÃO: Altura fixa
        btn_calculate.clicked.connect(self._on_calculate)
        layout.addWidget(btn_calculate)
        
        # Botão limpar - CORREÇÃO: Altura fixa definida programaticamente
        btn_clear = QPushButton("Limpar Campos")
        btn_clear.setObjectName("secondary")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setFixedHeight(44)  # CORREÇÃO: Altura fixa
        btn_clear.clicked.connect(self._on_clear)
        layout.addWidget(btn_clear)
        
        layout.addStretch()
        
        # Créditos
        credits = QLabel("Desenvolvido com Python + PySide6")
        credits.setObjectName("subtitle")
        credits.setAlignment(Qt.AlignCenter)
        layout.addWidget(credits)
        
        parent_layout.addWidget(sidebar)
    
    def _create_input_field(
        self, layout: QVBoxLayout, label_text: str, placeholder: str,
        is_currency: bool = False, is_percent: bool = False, is_integer: bool = False
    ) -> QLineEdit:
        """Cria um campo de entrada com label."""
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 12px; margin-bottom: 2px;")
        layout.addWidget(label)
        
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setFixedHeight(44)  # CORREÇÃO: Altura fixa para inputs
        
        # Validadores
        if is_integer:
            input_field.setValidator(QIntValidator(1, 100))
        else:
            validator = QDoubleValidator(0.0, 999999999.99, 2)
            validator.setNotation(QDoubleValidator.StandardNotation)
            input_field.setValidator(validator)
        
        layout.addWidget(input_field)
        return input_field
    
    def _create_dashboard(self, parent_layout: QHBoxLayout):
        """Cria a área principal do dashboard."""
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Cards de resumo (horizontal)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.card_invested = SummaryCard(
            "💰 TOTAL INVESTIDO", "R$ 0,00", "card_value"
        )
        self.card_interest = SummaryCard(
            "📈 TOTAL EM JUROS", "R$ 0,00", "card_value_green"
        )
        self.card_final = SummaryCard(
            "🏆 VALOR FINAL BRUTO", "R$ 0,00", "card_value_gold"
        )
        
        cards_layout.addWidget(self.card_invested)
        cards_layout.addWidget(self.card_interest)
        cards_layout.addWidget(self.card_final)
        
        layout.addLayout(cards_layout)
        
        # Gráfico
        self.chart = ChartCanvas()
        self.chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.chart)
        
        parent_layout.addWidget(dashboard, stretch=1)
    
    def _parse_currency(self, text: str) -> float:
        """Converte texto de moeda para float."""
        # Remove caracteres não numéricos exceto vírgula e ponto
        clean = text.replace("R$", "").replace(" ", "").strip()
        # Trata formato brasileiro (1.000,00) ou americano (1,000.00)
        if "," in clean and "." in clean:
            if clean.rfind(",") > clean.rfind("."):
                # Formato brasileiro: 1.000,00
                clean = clean.replace(".", "").replace(",", ".")
            else:
                # Formato americano: 1,000.00
                clean = clean.replace(",", "")
        elif "," in clean:
            clean = clean.replace(",", ".")
        
        return float(clean) if clean else 0.0
    
    def _on_calculate(self):
        """Executa o cálculo da simulação."""
        try:
            # Obtém os valores dos inputs
            initial = self._parse_currency(self.input_initial.text())
            monthly = self._parse_currency(self.input_monthly.text())
            rate = self._parse_currency(self.input_rate.text())
            years = int(self.input_years.text()) if self.input_years.text() else 0
            
            # Validação básica
            if years <= 0:
                raise ValueError("O tempo deve ser maior que zero.")
            if rate < 0:
                raise ValueError("A taxa de juros não pode ser negativa.")
            
            # Executa o cálculo
            result = calculate_compound_interest(initial, monthly, rate, years)
            
            # Atualiza os cards
            self.card_invested.set_value(format_currency(result.total_invested))
            self.card_interest.set_value(format_currency(result.total_interest))
            self.card_final.set_value(format_currency(result.final_balance))
            
            # Cria linha do total investido para comparação no gráfico
            import numpy as np
            total_invested_line = initial + (monthly * result.months)
            
            # Atualiza o gráfico
            self.chart.update_chart(result.months, result.balances, total_invested_line)
            
        except ValueError as e:
            QMessageBox.warning(
                self, "Dados Inválidos",
                f"Por favor, verifique os valores inseridos.\n\nErro: {str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Erro",
                f"Ocorreu um erro ao calcular.\n\nDetalhes: {str(e)}"
            )
    
    def _on_clear(self):
        """Limpa todos os campos."""
        self.input_initial.clear()
        self.input_monthly.clear()
        self.input_rate.clear()
        self.input_years.clear()
        
        self.card_invested.set_value("R$ 0,00")
        self.card_interest.set_value("R$ 0,00")
        self.card_final.set_value("R$ 0,00")
        
        # Redesenha gráfico vazio
        self.chart.axes.clear()
        self.chart._setup_style()
        self.chart._draw_empty_chart()