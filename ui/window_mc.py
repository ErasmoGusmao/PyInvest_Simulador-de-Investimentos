"""
PyInvest - Janela Principal
Interface moderna com Monte Carlo para simulação de investimentos.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy,
    QScrollArea, QMessageBox, QSpacerItem, QFileDialog,
    QSpinBox, QGroupBox, QProgressBar
)
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QDoubleValidator, QIntValidator, QFont

from core.calculation import calculate_compound_interest, format_currency, InvestmentCalculator
from core.monte_carlo import (
    ParameterRange, MonteCarloInput, MonteCarloResult,
    MonteCarloEngine, MonteCarloWorker
)
from ui.styles import get_style, get_colors
from ui.widgets import (
    SummaryCard, GoalStatusCard, EvolutionChart, 
    CompositionChart, ProjectionTable, AnalysisBox,
    SensitivityDashboard, RangeParameterInput
)


class MainWindow(QMainWindow):
    """Janela principal do PyInvest com Monte Carlo."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PyInvest - Simulador de Investimentos")
        self.setMinimumSize(1300, 900)
        self.setStyleSheet(get_style())
        
        # Thread pool para Monte Carlo
        self.thread_pool = QThreadPool()
        
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
        subtitle = QLabel("Análise Probabilística com Monte Carlo")
        subtitle.setObjectName("main_subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
    
    def _create_parameters_panel(self, layout: QHBoxLayout):
        """Cria o painel de parâmetros com ranges."""
        panel = QFrame()
        panel.setObjectName("panel")
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(12)
        
        # Título
        section_title = QLabel("Parâmetros da Simulação")
        section_title.setObjectName("section_title")
        panel_layout.addWidget(section_title)
        
        # Subtítulo explicativo
        help_text = QLabel("💡 Preencha Min/Máx para ativar simulação Monte Carlo")
        help_text.setStyleSheet("""
            font-size: 11px;
            color: #7f8c8d;
            font-style: italic;
            margin-bottom: 5px;
        """)
        panel_layout.addWidget(help_text)
        
        # === PARÂMETROS COM RANGE (Monte Carlo) ===
        
        # Capital Inicial
        self.input_capital = RangeParameterInput("Capital Inicial (R$)")
        panel_layout.addWidget(self.input_capital)
        
        # Aporte Mensal
        self.input_aporte = RangeParameterInput("Aporte Mensal (R$)")
        panel_layout.addWidget(self.input_aporte)
        
        # Rentabilidade Anual
        self.input_rentabilidade = RangeParameterInput("Rentabilidade Anual (%)")
        panel_layout.addWidget(self.input_rentabilidade)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #e0e0e0; max-height: 1px;")
        panel_layout.addWidget(separator)
        
        # === PARÂMETROS SIMPLES ===
        
        # Meta
        self._add_simple_input(
            panel_layout, "Objetivo (Meta em R$)",
            "input_meta", "100000"
        )
        
        # Período
        self._add_simple_input(
            panel_layout, "Período (Anos)",
            "input_periodo", "10"
        )
        
        # === CONFIGURAÇÃO MONTE CARLO ===
        mc_group = QGroupBox("Configuração Monte Carlo")
        mc_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        mc_layout = QHBoxLayout(mc_group)
        
        mc_label = QLabel("Simulações:")
        mc_label.setStyleSheet("font-weight: normal; font-size: 12px;")
        
        self.spin_simulations = QSpinBox()
        self.spin_simulations.setRange(100, 50000)
        self.spin_simulations.setValue(5000)
        self.spin_simulations.setSingleStep(1000)
        self.spin_simulations.setStyleSheet("""
            QSpinBox {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QSpinBox:focus {
                border-color: #16a085;
            }
        """)
        
        mc_layout.addWidget(mc_label)
        mc_layout.addWidget(self.spin_simulations)
        mc_layout.addStretch()
        
        panel_layout.addWidget(mc_group)
        
        # === BOTÕES ===
        panel_layout.addSpacing(10)
        
        # Botão Calcular
        btn_calculate = QPushButton("🚀 Calcular Simulação")
        btn_calculate.setObjectName("btn_calculate")
        btn_calculate.setCursor(Qt.PointingHandCursor)
        btn_calculate.clicked.connect(self._on_calculate)
        panel_layout.addWidget(btn_calculate)
        
        # Progress Bar (oculta por padrão)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #ecf0f1;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #16a085;
                border-radius: 4px;
            }
        """)
        panel_layout.addWidget(self.progress_bar)
        
        # Botão Resetar
        btn_reset = QPushButton("Resetar Valores")
        btn_reset.setObjectName("btn_reset")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self._on_reset)
        panel_layout.addWidget(btn_reset)
        
        panel_layout.addStretch()
        
        layout.addWidget(panel, stretch=1)
    
    def _add_simple_input(self, layout, label_text, attr_name, placeholder=""):
        """Adiciona um input simples (sem range)."""
        label = QLabel(label_text)
        label.setStyleSheet("""
            font-size: 13px;
            font-weight: 500;
            color: #2c3e50;
        """)
        layout.addWidget(label)
        
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #16a085;
            }
        """)
        layout.addWidget(input_field)
        
        setattr(self, attr_name, input_field)
    
    def _create_results_panel(self, layout: QHBoxLayout):
        """Cria o painel de resultados."""
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
        
        # Box de análise
        self.analysis_box = AnalysisBox()
        panel_layout.addWidget(self.analysis_box)
        
        # Card Monte Carlo (quando ativo)
        self.mc_summary = QFrame()
        self.mc_summary.setObjectName("mc_summary")
        self.mc_summary.setStyleSheet("""
            QFrame#mc_summary {
                background-color: rgba(52, 152, 219, 0.08);
                border-left: 4px solid #3498db;
                border-radius: 0px 8px 8px 0px;
            }
        """)
        self.mc_summary.setVisible(False)
        
        mc_layout = QVBoxLayout(self.mc_summary)
        mc_layout.setContentsMargins(15, 12, 15, 12)
        mc_layout.setSpacing(6)
        
        mc_title = QLabel("📊 Análise Monte Carlo:")
        mc_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; background: transparent;")
        mc_layout.addWidget(mc_title)
        
        self.mc_label = QLabel("")
        self.mc_label.setWordWrap(True)
        self.mc_label.setStyleSheet("font-size: 13px; color: #2c3e50; line-height: 1.6; background: transparent;")
        mc_layout.addWidget(self.mc_label)
        
        panel_layout.addWidget(self.mc_summary)
        
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
        self.evolution_chart.setMinimumHeight(350)
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
        self.composition_chart.setMinimumHeight(350)
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
            QPushButton:hover {
                background-color: #2ecc71;
            }
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
    
    def _parse_value(self, text: str) -> float:
        """Converte texto para float."""
        if not text.strip():
            return 0.0
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
            return 0.0
    
    def _validate_inputs(self) -> tuple:
        """
        Valida todos os inputs antes de calcular.
        
        Returns:
            tuple: (is_valid, errors_list, mc_input)
        """
        errors = []
        
        # Obter ranges
        capital_range = self.input_capital.get_parameter_range()
        aporte_range = self.input_aporte.get_parameter_range()
        rent_range = self.input_rentabilidade.get_parameter_range()
        
        # Validar cada range
        for name, param in [
            ("Capital Inicial", capital_range),
            ("Aporte Mensal", aporte_range),
            ("Rentabilidade", rent_range)
        ]:
            is_valid, error = param.validate()
            if not is_valid:
                errors.append(f"{name}: {error}")
        
        # Validar período
        periodo_text = self.input_periodo.text().strip()
        if not periodo_text:
            errors.append("Período: informe o número de anos.")
        else:
            try:
                periodo = int(periodo_text)
                if periodo <= 0:
                    errors.append("Período: deve ser maior que zero.")
                elif periodo > 100:
                    errors.append("Período: máximo de 100 anos.")
            except ValueError:
                errors.append("Período: valor inválido.")
        
        if errors:
            return False, errors, None
        
        # Criar input Monte Carlo
        mc_input = MonteCarloInput(
            capital_inicial=capital_range,
            aporte_mensal=aporte_range,
            rentabilidade_anual=rent_range,
            periodo_anos=int(self.input_periodo.text()),
            meta=self._parse_value(self.input_meta.text()),
            n_simulations=self.spin_simulations.value()
        )
        
        return True, [], mc_input
    
    def _on_calculate(self):
        """Executa a simulação."""
        # Validar inputs
        is_valid, errors, mc_input = self._validate_inputs()
        
        if not is_valid:
            QMessageBox.warning(
                self, "Erro de Validação",
                "Corrija os seguintes erros:\n\n• " + "\n• ".join(errors)
            )
            return
        
        # Mostrar progress bar se tiver Monte Carlo
        if mc_input.has_probabilistic_params():
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Executar em thread separada
            worker = MonteCarloWorker(mc_input)
            worker.signals.progress.connect(self._on_progress)
            worker.signals.finished.connect(self._on_simulation_finished)
            worker.signals.error.connect(self._on_simulation_error)
            
            self.thread_pool.start(worker)
        else:
            # Simulação simples (sem Monte Carlo)
            try:
                engine = MonteCarloEngine(mc_input)
                result = engine.run()
                self._update_ui_with_result(result)
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))
    
    def _on_progress(self, value: int):
        """Atualiza progress bar."""
        self.progress_bar.setValue(value)
    
    def _on_simulation_finished(self, result: MonteCarloResult):
        """Callback quando simulação termina."""
        self.progress_bar.setVisible(False)
        self._update_ui_with_result(result)
    
    def _on_simulation_error(self, error_msg: str):
        """Callback para erro na simulação."""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Erro na Simulação", error_msg)
    
    def _update_ui_with_result(self, result: MonteCarloResult):
        """Atualiza toda a interface com o resultado."""
        # Cards principais (usando valores determinísticos)
        self.card_invested.set_value(format_currency(result.total_invested))
        self.card_interest.set_value(format_currency(result.total_interest_det))
        self.card_final.set_value(format_currency(result.final_balance_det))
        
        # Card de meta
        meta = result.params_used.get('meta', 0)
        if meta > 0:
            achieved = result.final_balance_det >= meta
            percentage = (result.final_balance_det / meta * 100)
            self.card_goal.update_status(achieved, percentage)
        else:
            self.card_goal.status_label.setText("—")
            self.card_goal.percent_label.setText("")
        
        # Análise textual
        self._update_analysis_text(result)
        
        # Summary Monte Carlo
        if result.has_monte_carlo:
            self.mc_summary.setVisible(True)
            mc_text = (
                f"• {result.n_simulations:,} cenários simulados<br>"
                f"• Saldo Final Médio: {format_currency(result.final_balance_mean)}<br>"
                f"• Intervalo: {format_currency(result.final_balance_min)} a "
                f"{format_currency(result.final_balance_max)}"
            )
            self.mc_label.setText(mc_text)
        else:
            self.mc_summary.setVisible(False)
        
        # Dashboard de sensibilidade
        params = result.params_used
        self.sensitivity_dashboard.update_sensitivities(
            initial_amount=params['capital_inicial'],
            monthly_contribution=params['aporte_mensal'],
            annual_rate=params['rentabilidade_anual'],
            years=params['periodo_anos']
        )
        
        # Gráficos
        self.evolution_chart.update_chart_monte_carlo(result)
        self.composition_chart.update_chart(result.total_invested, result.total_interest_det)
        
        # Tabela
        self.projection_table.update_data_monte_carlo(result)
    
    def _update_analysis_text(self, result: MonteCarloResult):
        """Atualiza o texto de análise."""
        params = result.params_used
        
        initial_fmt = format_currency(params['capital_inicial'])
        monthly_fmt = format_currency(params['aporte_mensal'])
        final_fmt = format_currency(result.final_balance_det)
        interest_fmt = format_currency(result.total_interest_det)
        
        total_invested = result.total_invested
        rentabilidade = (result.total_interest_det / total_invested * 100) if total_invested > 0 else 0
        
        lines = [
            f"• Seu investimento: {initial_fmt} + {monthly_fmt}/mês",
            f"• Com rentabilidade de {params['rentabilidade_anual']:.2f}% a.a.",
            f"• Saldo final: {final_fmt}",
            f"• Lucro com juros: {interest_fmt}",
            f"• Rentabilidade total: {rentabilidade:.2f}%"
        ]
        
        self.analysis_box.analysis_label.setText("<br>".join(lines))
    
    def _on_reset(self):
        """Reseta todos os campos."""
        # Limpar inputs de range
        self.input_capital.clear()
        self.input_aporte.clear()
        self.input_rentabilidade.clear()
        
        # Limpar inputs simples
        self.input_meta.clear()
        self.input_periodo.clear()
        
        # Resetar spin
        self.spin_simulations.setValue(5000)
        
        # Resetar cards
        self.card_invested.set_value("R$ 0,00")
        self.card_interest.set_value("R$ 0,00")
        self.card_final.set_value("R$ 0,00")
        self.card_goal.status_label.setText("—")
        self.card_goal.percent_label.setText("")
        
        # Resetar análise
        self.analysis_box.analysis_label.setText("")
        self.mc_summary.setVisible(False)
        
        # Resetar sensibilidade
        self.sensitivity_dashboard.reset()
        
        # Resetar gráficos
        self.evolution_chart.axes.clear()
        self.evolution_chart._draw_empty()
        self.composition_chart.axes.clear()
        self.composition_chart._draw_empty()
        
        # Resetar tabela
        self.projection_table.reset_columns()
        self.projection_table.setRowCount(0)
    
    def _on_export_csv(self):
        """Exporta dados para CSV."""
        if not self.projection_table.has_data():
            QMessageBox.warning(self, "Sem Dados", "Execute uma simulação primeiro.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar CSV", "projecao_monte_carlo.csv", "CSV (*.csv)"
        )
        
        if filepath:
            if self.projection_table.export_to_csv(filepath):
                QMessageBox.information(self, "Sucesso", f"Exportado para:\n{filepath}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao exportar.")
