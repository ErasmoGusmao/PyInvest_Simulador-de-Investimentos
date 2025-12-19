"""
PyInvest - Janela Principal
Interface moderna com tema claro para simulação de investimentos.
Suporte a análise probabilística Monte Carlo.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy,
    QScrollArea, QMessageBox, QSpacerItem, QFileDialog,
    QSpinBox, QGroupBox, QProgressBar
)
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QDoubleValidator, QIntValidator, QFont

from core.calculation import (
    calculate_compound_interest, format_currency,
    ParameterRange, SimulationParameters, run_full_simulation
)
from core.worker import SimulationWorker
from ui.styles import get_style, get_colors
from ui.widgets import (
    SummaryCard, GoalStatusCard, EvolutionChart, 
    CompositionChart, ProjectionTable, AnalysisBox,
    SensitivityDashboard
)


class RangeInputWidget(QFrame):
    """Widget para entrada de parâmetro com range (Min, Det, Max)."""
    
    def __init__(self, label: str, unit: str = "", is_percentage: bool = False):
        super().__init__()
        self.is_percentage = is_percentage
        
        self.setObjectName("range_input_widget")
        self.setStyleSheet("""
            QFrame#range_input_widget {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Label principal
        title = QLabel(f"{label} ({unit})" if unit else label)
        title.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #2c3e50;
        """)
        layout.addWidget(title)
        
        # Grid para os 3 campos
        grid = QGridLayout()
        grid.setSpacing(8)
        
        # Estilo comum dos inputs
        input_style = """
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 13px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border: 2px solid #16a085;
            }
            QLineEdit::placeholder {
                color: #bdc3c7;
            }
        """
        
        # Labels
        lbl_min = QLabel("Mínimo")
        lbl_min.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        lbl_det = QLabel("Determinístico")
        lbl_det.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        lbl_max = QLabel("Máximo")
        lbl_max.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        
        grid.addWidget(lbl_min, 0, 0)
        grid.addWidget(lbl_det, 0, 1)
        grid.addWidget(lbl_max, 0, 2)
        
        # Inputs
        self.input_min = QLineEdit()
        self.input_min.setPlaceholderText("Min")
        self.input_min.setStyleSheet(input_style)
        self.input_min.setValidator(QDoubleValidator(0, 999999999, 2))
        
        self.input_det = QLineEdit()
        self.input_det.setPlaceholderText("Valor Base")
        self.input_det.setStyleSheet(input_style)
        self.input_det.setValidator(QDoubleValidator(0, 999999999, 2))
        
        self.input_max = QLineEdit()
        self.input_max.setPlaceholderText("Max")
        self.input_max.setStyleSheet(input_style)
        self.input_max.setValidator(QDoubleValidator(0, 999999999, 2))
        
        grid.addWidget(self.input_min, 1, 0)
        grid.addWidget(self.input_det, 1, 1)
        grid.addWidget(self.input_max, 1, 2)
        
        layout.addLayout(grid)
    
    def get_parameter_range(self) -> ParameterRange:
        """Retorna o ParameterRange com os valores preenchidos."""
        def parse_value(text: str):
            if not text.strip():
                return None
            try:
                clean = text.replace("R$", "").replace("%", "").replace(" ", "").strip()
                if "," in clean and "." in clean:
                    if clean.rfind(",") > clean.rfind("."):
                        clean = clean.replace(".", "").replace(",", ".")
                    else:
                        clean = clean.replace(",", "")
                elif "," in clean:
                    clean = clean.replace(",", ".")
                return float(clean)
            except:
                return None
        
        return ParameterRange(
            min_value=parse_value(self.input_min.text()),
            deterministic=parse_value(self.input_det.text()),
            max_value=parse_value(self.input_max.text())
        )
    
    def clear(self):
        """Limpa todos os campos."""
        self.input_min.clear()
        self.input_det.clear()
        self.input_max.clear()
    
    def set_deterministic(self, value: float):
        """Define apenas o valor determinístico."""
        self.input_det.setText(str(value))


class MainWindow(QMainWindow):
    """Janela principal do PyInvest com suporte a Monte Carlo."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PyInvest - Simulador de Investimentos")
        self.setMinimumSize(1300, 900)
        self.setStyleSheet(get_style())
        
        # Thread pool para simulações
        self.thread_pool = QThreadPool()
        self.current_worker = None
        
        # Widget central com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCentralWidget(scroll)
        
        # Container principal
        container = QWidget()
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        self._create_header(main_layout)
        
        # Conteúdo principal (duas colunas)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Coluna esquerda - Parâmetros
        self._create_parameters_panel(content_layout)
        
        # Coluna direita - Resultados
        self._create_results_panel(content_layout)
        
        main_layout.addLayout(content_layout)
        
        # Seção de Sensibilidade
        self._create_sensitivity_section(main_layout)
        
        # Seção de gráficos
        self._create_charts_section(main_layout)
        
        # Tabela de projeção
        self._create_projection_section(main_layout)
    
    def _create_header(self, layout: QVBoxLayout):
        """Cria o cabeçalho da aplicação."""
        header = QFrame()
        header.setObjectName("card")
        header.setFixedHeight(100)
        
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(6)
        
        # Título com ícone
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel("💰")
        icon_label.setStyleSheet("font-size: 28px; background: transparent;")
        
        title = QLabel("Simulador de Investimentos")
        title.setObjectName("main_title")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title)
        
        header_layout.addLayout(title_layout)
        
        # Subtítulo
        subtitle = QLabel("Planeje seu futuro financeiro com juros compostos e análise Monte Carlo")
        subtitle.setObjectName("main_subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
    
    def _create_parameters_panel(self, layout: QHBoxLayout):
        """Cria o painel de parâmetros (coluna esquerda)."""
        panel = QFrame()
        panel.setObjectName("card")
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(12)
        
        # Título
        section_title = QLabel("Parâmetros da Simulação")
        section_title.setObjectName("section_title")
        panel_layout.addWidget(section_title)
        
        # Parâmetros com Range (Min/Det/Max)
        range_title = QLabel("📊 Parâmetros Probabilísticos")
        range_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #16a085; margin-top: 5px;")
        panel_layout.addWidget(range_title)
        
        range_subtitle = QLabel("Defina ranges para análise Monte Carlo (opcional)")
        range_subtitle.setStyleSheet("font-size: 11px; color: #7f8c8d; margin-bottom: 5px;")
        panel_layout.addWidget(range_subtitle)
        
        # Capital Inicial
        self.range_initial = RangeInputWidget("Capital Inicial", "R$")
        panel_layout.addWidget(self.range_initial)
        
        # Aporte Mensal
        self.range_monthly = RangeInputWidget("Aporte Mensal", "R$")
        panel_layout.addWidget(self.range_monthly)
        
        # Rentabilidade Anual
        self.range_rate = RangeInputWidget("Rentabilidade Anual", "%", is_percentage=True)
        panel_layout.addWidget(self.range_rate)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        separator.setFixedHeight(1)
        panel_layout.addWidget(separator)
        
        # Parâmetros simples (sem range)
        simple_title = QLabel("📌 Parâmetros Fixos")
        simple_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #2c3e50; margin-top: 5px;")
        panel_layout.addWidget(simple_title)
        
        # Objetivo (Meta)
        self.input_goal = self._create_simple_input(panel_layout, "Objetivo (Meta em R$)")
        
        # Período (Anos)
        self.input_years = self._create_simple_input(panel_layout, "Período (Anos)")
        self.input_years.setValidator(QIntValidator(1, 100))
        
        # Número de Simulações Monte Carlo
        simulations_layout = QHBoxLayout()
        sim_label = QLabel("Simulações Monte Carlo:")
        sim_label.setStyleSheet("font-size: 12px; color: #2c3e50;")
        
        self.spin_simulations = QSpinBox()
        self.spin_simulations.setRange(100, 50000)
        self.spin_simulations.setValue(5000)
        self.spin_simulations.setSingleStep(1000)
        self.spin_simulations.setStyleSheet("""
            QSpinBox {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
        """)
        
        simulations_layout.addWidget(sim_label)
        simulations_layout.addWidget(self.spin_simulations)
        simulations_layout.addStretch()
        panel_layout.addLayout(simulations_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #e0e0e0;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #16a085;
                border-radius: 4px;
            }
        """)
        panel_layout.addWidget(self.progress_bar)
        
        # Botões
        panel_layout.addSpacing(10)
        
        # Botão Calcular
        btn_calculate = QPushButton("🚀 Calcular Simulação")
        btn_calculate.setObjectName("btn_primary")
        btn_calculate.setCursor(Qt.PointingHandCursor)
        btn_calculate.clicked.connect(self._on_calculate)
        btn_calculate.setMinimumHeight(48)
        panel_layout.addWidget(btn_calculate)
        
        # Botão Reset
        btn_reset = QPushButton("🔄 Resetar Valores")
        btn_reset.setObjectName("btn_secondary")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self._on_reset)
        btn_reset.setMinimumHeight(44)
        panel_layout.addWidget(btn_reset)
        
        panel_layout.addStretch()
        
        layout.addWidget(panel, stretch=1)
    
    def _create_simple_input(self, layout: QVBoxLayout, label: str) -> QLineEdit:
        """Cria um campo de input simples."""
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 12px; color: #2c3e50;")
        layout.addWidget(lbl)
        
        input_field = QLineEdit()
        input_field.setObjectName("input_field")
        input_field.setMinimumHeight(42)
        input_field.setValidator(QDoubleValidator(0, 999999999, 2))
        layout.addWidget(input_field)
        
        return input_field
    
    def _create_results_panel(self, layout: QHBoxLayout):
        """Cria o painel de resultados (coluna direita)."""
        panel = QFrame()
        panel.setObjectName("results_panel")
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(15)
        
        # Título
        section_title = QLabel("Resumo dos Resultados")
        section_title.setObjectName("section_title")
        panel_layout.addWidget(section_title)
        
        # Cards de resumo
        cards_grid = QGridLayout()
        cards_grid.setSpacing(12)
        
        self.card_invested = SummaryCard("TOTAL INVESTIDO", "R$ 0,00", "invested")
        self.card_interest = SummaryCard("LUCRO COM JUROS", "R$ 0,00", "interest")
        self.card_final = SummaryCard("SALDO FINAL", "R$ 0,00", "final")
        self.card_goal = GoalStatusCard()
        
        cards_grid.addWidget(self.card_invested, 0, 0)
        cards_grid.addWidget(self.card_interest, 0, 1)
        cards_grid.addWidget(self.card_final, 0, 2)
        cards_grid.addWidget(self.card_goal, 1, 0)
        
        panel_layout.addLayout(cards_grid)
        
        # Card Monte Carlo (novo)
        self.monte_carlo_info = QFrame()
        self.monte_carlo_info.setObjectName("monte_carlo_card")
        self.monte_carlo_info.setStyleSheet("""
            QFrame#monte_carlo_card {
                background-color: rgba(142, 68, 173, 0.08);
                border-left: 4px solid #8e44ad;
                border-radius: 0px 8px 8px 0px;
                padding: 10px;
            }
        """)
        self.monte_carlo_info.setVisible(False)
        
        mc_layout = QVBoxLayout(self.monte_carlo_info)
        mc_layout.setContentsMargins(15, 12, 15, 12)
        mc_layout.setSpacing(6)
        
        mc_title = QLabel("📊 Análise Monte Carlo")
        mc_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #8e44ad; background: transparent;")
        mc_layout.addWidget(mc_title)
        
        self.mc_stats_label = QLabel("")
        self.mc_stats_label.setStyleSheet("font-size: 12px; color: #2c3e50; line-height: 1.6; background: transparent;")
        self.mc_stats_label.setWordWrap(True)
        mc_layout.addWidget(self.mc_stats_label)
        
        panel_layout.addWidget(self.monte_carlo_info)
        
        # Box de análise
        self.analysis_box = AnalysisBox()
        panel_layout.addWidget(self.analysis_box)
        
        panel_layout.addStretch()
        
        layout.addWidget(panel, stretch=1)
    
    def _create_sensitivity_section(self, layout: QVBoxLayout):
        """Cria a seção do dashboard de sensibilidade."""
        sensitivity_frame = QFrame()
        sensitivity_frame.setObjectName("card")
        
        sensitivity_layout = QVBoxLayout(sensitivity_frame)
        sensitivity_layout.setContentsMargins(20, 20, 20, 20)
        sensitivity_layout.setSpacing(15)
        
        self.sensitivity_dashboard = SensitivityDashboard()
        sensitivity_layout.addWidget(self.sensitivity_dashboard)
        
        layout.addWidget(sensitivity_frame)
    
    def _create_charts_section(self, layout: QVBoxLayout):
        """Cria a seção de gráficos."""
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)
        
        # Gráfico de evolução (60%)
        evolution_frame = QFrame()
        evolution_frame.setObjectName("card")
        evolution_layout = QVBoxLayout(evolution_frame)
        evolution_layout.setContentsMargins(15, 15, 15, 15)
        evolution_layout.setSpacing(10)
        
        evolution_title = QLabel("Evolução do Patrimônio")
        evolution_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        evolution_layout.addWidget(evolution_title)
        
        self.evolution_chart = EvolutionChart()
        self.evolution_chart.setMinimumHeight(300)
        self.evolution_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        evolution_layout.addWidget(self.evolution_chart)
        
        charts_layout.addWidget(evolution_frame, stretch=3)
        
        # Gráfico de composição (40%)
        composition_frame = QFrame()
        composition_frame.setObjectName("card")
        composition_layout = QVBoxLayout(composition_frame)
        composition_layout.setContentsMargins(15, 15, 15, 15)
        composition_layout.setSpacing(10)
        
        composition_title = QLabel("Composição do Saldo Final")
        composition_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        composition_layout.addWidget(composition_title)
        
        self.composition_chart = CompositionChart()
        self.composition_chart.setMinimumHeight(300)
        self.composition_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        composition_layout.addWidget(self.composition_chart)
        
        charts_layout.addWidget(composition_frame, stretch=2)
        
        layout.addLayout(charts_layout)
    
    def _create_projection_section(self, layout: QVBoxLayout):
        """Cria a seção de projeção anual."""
        projection_frame = QFrame()
        projection_frame.setObjectName("card")
        
        projection_layout = QVBoxLayout(projection_frame)
        projection_layout.setContentsMargins(15, 15, 15, 15)
        projection_layout.setSpacing(10)
        
        # Header com título e botão
        header_layout = QHBoxLayout()
        
        title = QLabel("Projeção Anual")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #16a085;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        btn_export = QPushButton("📥 Exportar CSV")
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2ecc71; }
            QPushButton:pressed { background-color: #1e8449; }
        """)
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.clicked.connect(self._on_export_csv)
        header_layout.addWidget(btn_export)
        
        projection_layout.addLayout(header_layout)
        
        # Tabela
        self.projection_table = ProjectionTable()
        self.projection_table.setMinimumHeight(300)
        self.projection_table.setMaximumHeight(450)
        projection_layout.addWidget(self.projection_table)
        
        layout.addWidget(projection_frame)
    
    def _on_export_csv(self):
        """Exporta os dados da tabela para CSV."""
        if not self.projection_table.has_data():
            QMessageBox.warning(self, "Sem Dados", "Execute uma simulação antes de exportar.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Projeção como CSV",
            "projecao_investimento.csv", "Arquivos CSV (*.csv)"
        )
        
        if filepath:
            if self.projection_table.export_to_csv(filepath):
                QMessageBox.information(self, "Exportado", f"Dados exportados com sucesso para:\n{filepath}")
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível exportar os dados.")
    
    def _parse_value(self, text: str) -> float:
        """Converte texto para float."""
        clean = text.replace("R$", "").replace("%", "").replace(" ", "").strip()
        if "," in clean and "." in clean:
            if clean.rfind(",") > clean.rfind("."):
                clean = clean.replace(".", "").replace(",", ".")
            else:
                clean = clean.replace(",", "")
        elif "," in clean:
            clean = clean.replace(",", ".")
        return float(clean) if clean else 0.0
    
    def _validate_parameters(self) -> tuple:
        """Valida todos os parâmetros e retorna SimulationParameters ou erros."""
        errors = []
        
        # Obter ranges
        initial_range = self.range_initial.get_parameter_range()
        monthly_range = self.range_monthly.get_parameter_range()
        rate_range = self.range_rate.get_parameter_range()
        
        # Validar cada range
        for name, param in [
            ("Capital Inicial", initial_range),
            ("Aporte Mensal", monthly_range),
            ("Rentabilidade Anual", rate_range)
        ]:
            is_valid, error = param.validate()
            if not is_valid:
                errors.append(f"{name}: {error}")
        
        # Validar período
        years_text = self.input_years.text().strip()
        if not years_text:
            errors.append("Período: Campo obrigatório.")
            years = 0
        else:
            try:
                years = int(years_text)
                if years <= 0:
                    errors.append("Período: Deve ser maior que zero.")
            except:
                errors.append("Período: Valor inválido.")
                years = 0
        
        # Meta (opcional)
        goal_text = self.input_goal.text().strip()
        goal = self._parse_value(goal_text) if goal_text else 0
        
        # Número de simulações
        num_simulations = self.spin_simulations.value()
        
        if errors:
            return None, errors
        
        params = SimulationParameters(
            initial_amount=initial_range,
            monthly_contribution=monthly_range,
            annual_rate=rate_range,
            years=years,
            goal_amount=goal,
            num_simulations=num_simulations
        )
        
        return params, []
    
    def _on_calculate(self):
        """Executa a simulação."""
        # Validar parâmetros
        params, errors = self._validate_parameters()
        
        if errors:
            error_msg = "Corrija os seguintes erros:\n\n• " + "\n• ".join(errors)
            QMessageBox.warning(self, "Validação", error_msg)
            return
        
        # Mostrar progress bar se tiver Monte Carlo
        if params.has_any_range():
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
        
        # Criar worker e executar
        self.current_worker = SimulationWorker(params)
        self.current_worker.signals.started.connect(self._on_simulation_started)
        self.current_worker.signals.finished.connect(self._on_simulation_finished)
        self.current_worker.signals.error.connect(self._on_simulation_error)
        
        self.thread_pool.start(self.current_worker)
    
    def _on_simulation_started(self):
        """Callback quando simulação inicia."""
        pass
    
    def _on_simulation_finished(self, result):
        """Callback quando simulação termina."""
        self.progress_bar.setVisible(False)
        
        # Atualizar cards
        self.card_invested.set_value(format_currency(result.total_invested))
        self.card_interest.set_value(format_currency(result.total_interest))
        self.card_final.set_value(format_currency(result.final_balance))
        self.card_goal.update_status(
            result.analysis.goal_achieved,
            result.analysis.goal_percentage
        )
        
        # Atualizar Monte Carlo info
        if result.has_monte_carlo:
            mc = result.monte_carlo
            self.monte_carlo_info.setVisible(True)
            self.mc_stats_label.setText(
                f"• Simulações: {mc.num_simulations:,}\n"
                f"• Saldo Final Médio: {format_currency(mc.final_mean)}\n"
                f"• Desvio Padrão: {format_currency(mc.final_std)}\n"
                f"• Range: {format_currency(mc.final_min)} - {format_currency(mc.final_max)}"
            )
        else:
            self.monte_carlo_info.setVisible(False)
        
        # Atualizar análise
        self.analysis_box.update_analysis(result)
        
        # Atualizar dashboard de sensibilidade
        det_initial = result.analysis.initial_investment
        det_monthly = result.analysis.monthly_contribution
        det_rate = result.analysis.annual_rate
        years = len(result.yearly_projection) - 1
        
        self.sensitivity_dashboard.update_sensitivities(
            initial_amount=det_initial,
            monthly_contribution=det_monthly,
            annual_rate=det_rate,
            years=years
        )
        
        # Atualizar gráficos
        self.evolution_chart.update_chart(result)
        self.composition_chart.update_chart(result.total_invested, result.total_interest)
        
        # Atualizar tabela
        self.projection_table.update_data(result)
    
    def _on_simulation_error(self, error_msg):
        """Callback quando simulação falha."""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Erro na Simulação", f"Ocorreu um erro:\n{error_msg}")
    
    def _on_reset(self):
        """Reseta todos os campos."""
        # Limpar inputs de range
        self.range_initial.clear()
        self.range_monthly.clear()
        self.range_rate.clear()
        
        # Limpar inputs simples
        self.input_goal.clear()
        self.input_years.clear()
        
        # Reset simulações
        self.spin_simulations.setValue(5000)
        
        # Resetar cards
        self.card_invested.set_value("R$ 0,00")
        self.card_interest.set_value("R$ 0,00")
        self.card_final.set_value("R$ 0,00")
        self.card_goal.status_label.setText("—")
        self.card_goal.percent_label.setText("")
        
        # Esconder Monte Carlo info
        self.monte_carlo_info.setVisible(False)
        
        # Resetar análise
        self.analysis_box.analysis_label.setText("")
        
        # Resetar sensibilidade
        self.sensitivity_dashboard.reset()
        
        # Resetar gráficos
        self.evolution_chart.axes.clear()
        self.evolution_chart._draw_empty()
        
        self.composition_chart.axes.clear()
        self.composition_chart._draw_empty()
        
        # Resetar tabela
        self.projection_table.setRowCount(0)
