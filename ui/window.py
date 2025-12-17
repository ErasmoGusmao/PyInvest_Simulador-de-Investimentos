"""
PyInvest - Janela Principal
Interface moderna com tema claro para simulação de investimentos.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy,
    QScrollArea, QMessageBox, QSpacerItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator, QFont

from core.calculation import calculate_compound_interest, format_currency
from ui.styles import get_style, get_colors
from ui.widgets import (
    SummaryCard, GoalStatusCard, EvolutionChart, 
    CompositionChart, ProjectionTable, AnalysisBox
)


class MainWindow(QMainWindow):
    """Janela principal do PyInvest."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PyInvest - Simulador de Investimentos")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet(get_style())
        
        # Widget central com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCentralWidget(scroll)
        
        # Container principal
        container = QWidget()
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)
        
        # Header
        self._create_header(main_layout)
        
        # Conteúdo principal (duas colunas)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(25)
        
        # Coluna esquerda - Parâmetros
        self._create_parameters_panel(content_layout)
        
        # Coluna direita - Resultados
        self._create_results_panel(content_layout)
        
        main_layout.addLayout(content_layout)
        
        # Seção de gráficos
        self._create_charts_section(main_layout)
        
        # Tabela de projeção
        self._create_projection_section(main_layout)
        
        # Espaçador final
        main_layout.addStretch()
    
    def _create_header(self, layout: QVBoxLayout):
        """Cria o cabeçalho da aplicação."""
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(8)
        
        # Título com ícone
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel("💰")
        icon_label.setStyleSheet("font-size: 32px; background: transparent;")
        
        title = QLabel("Simulador de Investimentos")
        title.setObjectName("main_title")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title)
        
        header_layout.addLayout(title_layout)
        
        # Subtítulo
        subtitle = QLabel("Planeje seu futuro financeiro com juros compostos e aportes mensais")
        subtitle.setObjectName("main_subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
    
    def _create_parameters_panel(self, layout: QHBoxLayout):
        """Cria o painel de parâmetros (coluna esquerda)."""
        panel = QFrame()
        panel.setObjectName("sidebar")
        panel.setFixedWidth(420)
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(25, 25, 25, 25)
        panel_layout.setSpacing(18)
        
        # Título da seção
        section_title = QLabel("Parâmetros da Simulação")
        section_title.setObjectName("section_title")
        panel_layout.addWidget(section_title)
        
        panel_layout.addSpacing(10)
        
        # Campos de entrada
        self.input_initial = self._create_input(
            panel_layout, "Capital Inicial (R$)", "10000"
        )
        
        self.input_monthly = self._create_input(
            panel_layout, "Aporte Mensal (R$)", "1000"
        )
        
        self.input_rate = self._create_input(
            panel_layout, "Rentabilidade Anual (%)", "10"
        )
        
        self.input_goal = self._create_input(
            panel_layout, "Objetivo (Meta em R$)", "100000"
        )
        
        self.input_years = self._create_input(
            panel_layout, "Período (Anos)", "10", is_integer=True
        )
        
        panel_layout.addSpacing(15)
        
        # Botões
        btn_calculate = QPushButton("Calcular Simulação")
        btn_calculate.setObjectName("primary")
        btn_calculate.setCursor(Qt.PointingHandCursor)
        btn_calculate.setFixedHeight(50)
        btn_calculate.clicked.connect(self._on_calculate)
        panel_layout.addWidget(btn_calculate)
        
        btn_reset = QPushButton("Resetar Valores")
        btn_reset.setObjectName("secondary")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.setFixedHeight(46)
        btn_reset.clicked.connect(self._on_reset)
        panel_layout.addWidget(btn_reset)
        
        panel_layout.addStretch()
        
        layout.addWidget(panel)
    
    def _create_input(
        self, layout: QVBoxLayout, label_text: str, 
        placeholder: str, is_integer: bool = False
    ) -> QLineEdit:
        """Cria um campo de entrada com label."""
        label = QLabel(label_text)
        label.setObjectName("input_label")
        layout.addWidget(label)
        
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setFixedHeight(48)
        
        if is_integer:
            input_field.setValidator(QIntValidator(1, 100))
        else:
            validator = QDoubleValidator(0.0, 999999999.99, 2)
            validator.setNotation(QDoubleValidator.StandardNotation)
            input_field.setValidator(validator)
        
        layout.addWidget(input_field)
        return input_field
    
    def _create_results_panel(self, layout: QHBoxLayout):
        """Cria o painel de resultados (coluna direita)."""
        panel = QFrame()
        panel.setObjectName("results_panel")
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(25, 25, 25, 25)
        panel_layout.setSpacing(18)
        
        # Título
        section_title = QLabel("Resumo dos Resultados")
        section_title.setObjectName("section_title")
        panel_layout.addWidget(section_title)
        
        panel_layout.addSpacing(5)
        
        # Cards de resumo (grid 2x2)
        cards_grid = QGridLayout()
        cards_grid.setSpacing(15)
        
        self.card_invested = SummaryCard("TOTAL INVESTIDO", "R$ 0,00", "invested")
        self.card_interest = SummaryCard("LUCRO COM JUROS", "R$ 0,00", "interest")
        self.card_final = SummaryCard("SALDO FINAL", "R$ 0,00", "final")
        self.card_goal = GoalStatusCard()
        
        cards_grid.addWidget(self.card_invested, 0, 0)
        cards_grid.addWidget(self.card_interest, 0, 1)
        cards_grid.addWidget(self.card_final, 0, 2)
        cards_grid.addWidget(self.card_goal, 1, 0)
        
        panel_layout.addLayout(cards_grid)
        
        panel_layout.addSpacing(10)
        
        # Box de análise
        self.analysis_box = AnalysisBox()
        panel_layout.addWidget(self.analysis_box)
        
        panel_layout.addStretch()
        
        layout.addWidget(panel, stretch=1)
    
    def _create_charts_section(self, layout: QVBoxLayout):
        """Cria a seção de gráficos."""
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(25)
        
        # Gráfico de evolução (maior)
        evolution_frame = QFrame()
        evolution_frame.setObjectName("card")
        evolution_layout = QVBoxLayout(evolution_frame)
        evolution_layout.setContentsMargins(20, 20, 20, 20)
        
        evolution_title = QLabel("Evolução do Patrimônio")
        evolution_title.setObjectName("section_title")
        evolution_title.setStyleSheet("font-size: 16px; color: #2c3e50;")
        evolution_layout.addWidget(evolution_title)
        
        self.evolution_chart = EvolutionChart()
        self.evolution_chart.setMinimumHeight(350)
        evolution_layout.addWidget(self.evolution_chart)
        
        charts_layout.addWidget(evolution_frame, stretch=3)
        
        # Gráfico de composição (menor)
        composition_frame = QFrame()
        composition_frame.setObjectName("card")
        composition_layout = QVBoxLayout(composition_frame)
        composition_layout.setContentsMargins(20, 20, 20, 20)
        
        composition_title = QLabel("Composição do Saldo Final")
        composition_title.setObjectName("section_title")
        composition_title.setStyleSheet("font-size: 16px; color: #2c3e50;")
        composition_layout.addWidget(composition_title)
        
        self.composition_chart = CompositionChart()
        self.composition_chart.setMinimumHeight(350)
        composition_layout.addWidget(self.composition_chart)
        
        charts_layout.addWidget(composition_frame, stretch=2)
        
        layout.addLayout(charts_layout)
    
    def _create_projection_section(self, layout: QVBoxLayout):
        """Cria a seção de projeção anual."""
        projection_frame = QFrame()
        projection_frame.setObjectName("card")
        
        projection_layout = QVBoxLayout(projection_frame)
        projection_layout.setContentsMargins(20, 20, 20, 20)
        projection_layout.setSpacing(15)
        
        # Título
        title = QLabel("Projeção Anual")
        title.setObjectName("section_title")
        title.setStyleSheet("font-size: 18px; color: #16a085;")
        projection_layout.addWidget(title)
        
        # Tabela
        self.projection_table = ProjectionTable()
        self.projection_table.setMinimumHeight(400)
        projection_layout.addWidget(self.projection_table)
        
        layout.addWidget(projection_frame)
    
    def _parse_value(self, text: str) -> float:
        """Converte texto para float."""
        clean = text.replace("R$", "").replace(" ", "").strip()
        if "," in clean and "." in clean:
            if clean.rfind(",") > clean.rfind("."):
                clean = clean.replace(".", "").replace(",", ".")
            else:
                clean = clean.replace(",", "")
        elif "," in clean:
            clean = clean.replace(",", ".")
        return float(clean) if clean else 0.0
    
    def _on_calculate(self):
        """Executa a simulação."""
        try:
            # Obter valores
            initial = self._parse_value(self.input_initial.text())
            monthly = self._parse_value(self.input_monthly.text())
            rate = self._parse_value(self.input_rate.text())
            goal = self._parse_value(self.input_goal.text())
            years = int(self.input_years.text()) if self.input_years.text() else 0
            
            # Validação
            if years <= 0:
                raise ValueError("O período deve ser maior que zero.")
            if rate < 0:
                raise ValueError("A taxa não pode ser negativa.")
            
            # Calcular
            result = calculate_compound_interest(
                initial, monthly, rate, years, goal
            )
            
            # Atualizar cards
            self.card_invested.set_value(format_currency(result.total_invested))
            self.card_interest.set_value(format_currency(result.total_interest))
            self.card_final.set_value(format_currency(result.final_balance))
            self.card_goal.update_status(
                result.analysis.goal_achieved,
                result.analysis.goal_percentage
            )
            
            # Atualizar análise
            self.analysis_box.update_analysis(result)
            
            # Atualizar gráficos
            self.evolution_chart.update_chart(result)
            self.composition_chart.update_chart(
                result.total_invested, 
                result.total_interest
            )
            
            # Atualizar tabela
            self.projection_table.update_data(result)
            
        except ValueError as e:
            QMessageBox.warning(
                self, "Dados Inválidos",
                f"Por favor, verifique os valores.\n\nErro: {str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Erro",
                f"Erro ao calcular.\n\nDetalhes: {str(e)}"
            )
    
    def _on_reset(self):
        """Reseta todos os valores."""
        # Limpar inputs
        self.input_initial.clear()
        self.input_monthly.clear()
        self.input_rate.clear()
        self.input_goal.clear()
        self.input_years.clear()
        
        # Resetar cards
        self.card_invested.set_value("R$ 0,00")
        self.card_interest.set_value("R$ 0,00")
        self.card_final.set_value("R$ 0,00")
        self.card_goal.status_label.setText("—")
        self.card_goal.percent_label.setText("")
        
        # Resetar análise
        self.analysis_box.analysis_label.setText("")
        
        # Resetar gráficos
        self.evolution_chart.axes.clear()
        self.evolution_chart._draw_empty()
        
        self.composition_chart.axes.clear()
        self.composition_chart._draw_empty()
        
        # Resetar tabela
        self.projection_table.setRowCount(0)
