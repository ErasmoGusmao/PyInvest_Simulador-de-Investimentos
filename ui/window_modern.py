"""
PyInvest - Janela Principal Moderna
Interface com Flat Design, Cards e Gráficos Plotly.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy,
    QScrollArea, QMessageBox, QSpacerItem, QFileDialog,
    QSpinBox, QGroupBox, QProgressBar, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QFont, QColor

from core.monte_carlo import (
    ParameterRange, MonteCarloInput, MonteCarloResult,
    MonteCarloEngine, MonteCarloWorker
)
from core.calculation import format_currency
from ui.styles_modern import get_modern_style, get_colors, apply_shadow
from ui.plotly_charts import EvolutionChartPlotly, CompositionChartPlotly
from ui.widgets import (
    SummaryCard, GoalStatusCard, ProjectionTable, 
    AnalysisBox, SensitivityDashboard
)


class RangeInput(QFrame):
    """Widget moderno para entrada de parâmetro com range."""
    
    def __init__(self, label: str, placeholder: str = "0", parent=None):
        super().__init__(parent)
        
        self.label_text = label
        self._setup_ui(placeholder)
    
    def _setup_ui(self, placeholder: str):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(8)
        
        # Label principal
        title = QLabel(self.label_text)
        title.setObjectName("field_label")
        layout.addWidget(title)
        
        # Grid para os 3 campos
        grid = QHBoxLayout()
        grid.setSpacing(12)
        
        # Estilo comum dos sub-labels
        sublabel_style = """
            font-size: 11px;
            font-weight: 500;
            color: #9CA3AF;
            background: transparent;
            margin-bottom: 2px;
        """
        
        # Campo Mínimo
        min_container = QVBoxLayout()
        min_container.setSpacing(4)
        min_label = QLabel("Mínimo")
        min_label.setStyleSheet(sublabel_style)
        self.input_min = QLineEdit()
        self.input_min.setPlaceholderText("Mín")
        min_container.addWidget(min_label)
        min_container.addWidget(self.input_min)
        grid.addLayout(min_container)
        
        # Campo Base (Determinístico) - destacado
        det_container = QVBoxLayout()
        det_container.setSpacing(4)
        det_label = QLabel("Valor Base")
        det_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 600;
            color: #10B981;
            background: transparent;
            margin-bottom: 2px;
        """)
        self.input_det = QLineEdit()
        self.input_det.setPlaceholderText(placeholder)
        self.input_det.setStyleSheet("""
            QLineEdit {
                border: 2px solid #10B981;
                background-color: #F0FDF4;
            }
            QLineEdit:focus {
                border-color: #059669;
                background-color: #FFFFFF;
            }
        """)
        det_container.addWidget(det_label)
        det_container.addWidget(self.input_det)
        grid.addLayout(det_container)
        
        # Campo Máximo
        max_container = QVBoxLayout()
        max_container.setSpacing(4)
        max_label = QLabel("Máximo")
        max_label.setStyleSheet(sublabel_style)
        self.input_max = QLineEdit()
        self.input_max.setPlaceholderText("Máx")
        max_container.addWidget(max_label)
        max_container.addWidget(self.input_max)
        grid.addLayout(max_container)
        
        layout.addLayout(grid)
    
    def get_parameter_range(self) -> ParameterRange:
        """Retorna o ParameterRange com os valores preenchidos."""
        def parse(text):
            if not text.strip():
                return None
            clean = text.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
            try:
                return float(clean)
            except:
                return None
        
        return ParameterRange(
            min_value=parse(self.input_min.text()),
            deterministic=parse(self.input_det.text()),
            max_value=parse(self.input_max.text())
        )
    
    def clear(self):
        """Limpa todos os campos."""
        self.input_min.clear()
        self.input_det.clear()
        self.input_max.clear()


class ModernMainWindow(QMainWindow):
    """Janela principal moderna do PyInvest."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PyInvest - Simulador de Investimentos")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet(get_modern_style())
        
        # Thread pool para Monte Carlo
        self.thread_pool = QThreadPool()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura a interface."""
        # Widget central com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        self.setCentralWidget(scroll)
        
        # Container principal
        container = QWidget()
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)
        
        # Header
        self._create_header(main_layout)
        
        # Conteúdo principal (duas colunas)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # Coluna esquerda - Parâmetros (Card branco)
        self._create_parameters_card(content_layout)
        
        # Coluna direita - Resultados
        self._create_results_section(content_layout)
        
        main_layout.addLayout(content_layout)
        
        # Seção de gráficos
        self._create_charts_section(main_layout)
        
        # Tabela de projeção
        self._create_projection_section(main_layout)
    
    def _create_header(self, layout: QVBoxLayout):
        """Cria o cabeçalho moderno."""
        header = QFrame()
        header.setObjectName("header_card")
        header.setFixedHeight(110)
        apply_shadow(header)
        
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(8)
        
        # Título com ícone
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        title_layout.setSpacing(12)
        
        icon = QLabel("💰")
        icon.setStyleSheet("font-size: 36px; background: transparent;")
        
        title = QLabel("Simulador de Investimentos")
        title.setObjectName("main_title")
        
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        header_layout.addLayout(title_layout)
        
        # Subtítulo
        subtitle = QLabel("Análise Probabilística com Monte Carlo")
        subtitle.setObjectName("main_subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
    
    def _create_parameters_card(self, layout: QHBoxLayout):
        """Cria o card de parâmetros (coluna esquerda)."""
        card = QFrame()
        card.setObjectName("input_card")
        card.setFixedWidth(480)
        apply_shadow(card)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(8)
        
        # Título da seção
        title = QLabel("Parâmetros da Simulação")
        title.setObjectName("section_title")
        card_layout.addWidget(title)
        
        # Help text
        help_text = QLabel("💡 Preencha Min/Máx para ativar simulação Monte Carlo")
        help_text.setObjectName("help_text")
        help_text.setWordWrap(True)
        card_layout.addWidget(help_text)
        
        card_layout.addSpacing(12)
        
        # === PARÂMETROS COM RANGE ===
        
        self.input_capital = RangeInput("Capital Inicial (R$)", "10.000")
        card_layout.addWidget(self.input_capital)
        
        self.input_aporte = RangeInput("Aporte Mensal (R$)", "1.000")
        card_layout.addWidget(self.input_aporte)
        
        self.input_rentabilidade = RangeInput("Rentabilidade Anual (%)", "10")
        card_layout.addWidget(self.input_rentabilidade)
        
        # Separador
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.HLine)
        card_layout.addWidget(separator)
        
        card_layout.addSpacing(8)
        
        # === PARÂMETROS SIMPLES ===
        
        # Meta
        meta_label = QLabel("Objetivo (Meta em R$)")
        meta_label.setObjectName("field_label")
        card_layout.addWidget(meta_label)
        
        self.input_meta = QLineEdit()
        self.input_meta.setPlaceholderText("100.000")
        card_layout.addWidget(self.input_meta)
        
        card_layout.addSpacing(8)
        
        # Período
        periodo_label = QLabel("Período (Anos)")
        periodo_label.setObjectName("field_label")
        card_layout.addWidget(periodo_label)
        
        self.input_periodo = QLineEdit()
        self.input_periodo.setPlaceholderText("10")
        card_layout.addWidget(self.input_periodo)
        
        card_layout.addSpacing(8)
        
        # === CONFIGURAÇÃO MONTE CARLO ===
        mc_group = QGroupBox("Configuração Monte Carlo")
        mc_group_layout = QVBoxLayout(mc_group)
        mc_group_layout.setContentsMargins(16, 20, 16, 16)
        mc_group_layout.setSpacing(10)
        
        # Layout horizontal para label + spinbox
        mc_row = QHBoxLayout()
        mc_row.setSpacing(16)
        
        mc_label = QLabel("Número de Simulações:")
        mc_label.setStyleSheet("""
            font-weight: 500; 
            font-size: 13px; 
            color: #374151;
            background: transparent;
        """)
        
        self.spin_simulations = QSpinBox()
        self.spin_simulations.setRange(100, 50000)
        self.spin_simulations.setValue(5000)
        self.spin_simulations.setSingleStep(1000)
        self.spin_simulations.setFixedWidth(120)
        self.spin_simulations.setStyleSheet("""
            QSpinBox {
                background-color: #FFFFFF;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 600;
                color: #1F2937;
            }
            QSpinBox:focus {
                border-color: #10B981;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border: none;
                background: #F3F4F6;
                border-radius: 4px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #E5E7EB;
            }
        """)
        
        mc_row.addWidget(mc_label)
        mc_row.addWidget(self.spin_simulations)
        mc_row.addStretch()
        
        mc_group_layout.addLayout(mc_row)
        
        # Texto explicativo
        mc_help = QLabel("💡 Mais simulações = maior precisão, porém mais lento")
        mc_help.setStyleSheet("""
            font-size: 11px;
            color: #9CA3AF;
            font-style: italic;
            background: transparent;
        """)
        mc_group_layout.addWidget(mc_help)
        
        card_layout.addWidget(mc_group)
        
        card_layout.addSpacing(16)
        
        # === BOTÕES ===
        
        btn_calculate = QPushButton("🚀  Calcular Simulação")
        btn_calculate.setObjectName("btn_primary")
        btn_calculate.setCursor(Qt.PointingHandCursor)
        btn_calculate.clicked.connect(self._on_calculate)
        card_layout.addWidget(btn_calculate)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        card_layout.addWidget(self.progress_bar)
        
        btn_reset = QPushButton("Resetar Valores")
        btn_reset.setObjectName("btn_secondary")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self._on_reset)
        card_layout.addWidget(btn_reset)
        
        card_layout.addStretch()
        
        layout.addWidget(card)
    
    def _create_results_section(self, layout: QHBoxLayout):
        """Cria a seção de resultados (coluna direita)."""
        results_container = QVBoxLayout()
        results_container.setSpacing(20)
        
        # Card de resultados
        results_card = QFrame()
        results_card.setObjectName("results_card")
        apply_shadow(results_card)
        
        results_layout = QVBoxLayout(results_card)
        results_layout.setContentsMargins(24, 24, 24, 24)
        results_layout.setSpacing(16)
        
        # Título
        title = QLabel("Resumo dos Resultados")
        title.setObjectName("section_title")
        results_layout.addWidget(title)
        
        # Cards de resumo (grid 2x2)
        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)
        
        self.card_invested = SummaryCard("TOTAL INVESTIDO", "R$ 0,00", "invested")
        self.card_interest = SummaryCard("LUCRO COM JUROS", "R$ 0,00", "interest")
        self.card_final = SummaryCard("SALDO FINAL", "R$ 0,00", "final")
        self.card_goal = GoalStatusCard()
        
        cards_grid.addWidget(self.card_invested, 0, 0)
        cards_grid.addWidget(self.card_interest, 0, 1)
        cards_grid.addWidget(self.card_final, 0, 2)
        cards_grid.addWidget(self.card_goal, 1, 0)
        
        results_layout.addLayout(cards_grid)
        
        # Box de análise
        self.analysis_box = AnalysisBox()
        results_layout.addWidget(self.analysis_box)
        
        # Box Monte Carlo (quando ativo)
        self.mc_summary = QFrame()
        self.mc_summary.setObjectName("mc_summary")
        self.mc_summary.setVisible(False)
        
        mc_inner = QVBoxLayout(self.mc_summary)
        mc_inner.setContentsMargins(16, 14, 16, 14)
        mc_inner.setSpacing(8)
        
        mc_title = QLabel("📊 Análise Monte Carlo")
        mc_title.setStyleSheet("""
            font-size: 15px; 
            font-weight: 600; 
            color: #1F2937; 
            background: transparent;
        """)
        mc_inner.addWidget(mc_title)
        
        self.mc_label = QLabel("")
        self.mc_label.setWordWrap(True)
        self.mc_label.setStyleSheet("""
            font-size: 13px; 
            color: #374151; 
            line-height: 1.6; 
            background: transparent;
        """)
        mc_inner.addWidget(self.mc_label)
        
        results_layout.addWidget(self.mc_summary)
        
        results_layout.addStretch()
        
        results_container.addWidget(results_card)
        
        # Dashboard de Sensibilidade
        sensitivity_card = QFrame()
        sensitivity_card.setObjectName("card")
        apply_shadow(sensitivity_card)
        
        sens_layout = QVBoxLayout(sensitivity_card)
        sens_layout.setContentsMargins(20, 20, 20, 20)
        
        self.sensitivity_dashboard = SensitivityDashboard()
        sens_layout.addWidget(self.sensitivity_dashboard)
        
        results_container.addWidget(sensitivity_card)
        
        layout.addLayout(results_container, stretch=1)
    
    def _create_charts_section(self, layout: QVBoxLayout):
        """Cria a seção de gráficos Plotly."""
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(24)
        
        # Gráfico de evolução (70%)
        evolution_card = QFrame()
        evolution_card.setObjectName("card")
        apply_shadow(evolution_card)
        
        evolution_layout = QVBoxLayout(evolution_card)
        evolution_layout.setContentsMargins(20, 20, 20, 20)
        evolution_layout.setSpacing(12)
        
        evolution_title = QLabel("Evolução do Patrimônio")
        evolution_title.setObjectName("section_title")
        evolution_layout.addWidget(evolution_title)
        
        self.evolution_chart = EvolutionChartPlotly()
        evolution_layout.addWidget(self.evolution_chart)
        
        charts_layout.addWidget(evolution_card, stretch=7)
        
        # Gráfico de composição (30%)
        composition_card = QFrame()
        composition_card.setObjectName("card")
        apply_shadow(composition_card)
        
        composition_layout = QVBoxLayout(composition_card)
        composition_layout.setContentsMargins(20, 20, 20, 20)
        composition_layout.setSpacing(12)
        
        composition_title = QLabel("Composição do Saldo")
        composition_title.setObjectName("section_title")
        composition_layout.addWidget(composition_title)
        
        self.composition_chart = CompositionChartPlotly()
        composition_layout.addWidget(self.composition_chart)
        
        charts_layout.addWidget(composition_card, stretch=3)
        
        layout.addLayout(charts_layout)
    
    def _create_projection_section(self, layout: QVBoxLayout):
        """Cria a seção da tabela de projeção."""
        projection_card = QFrame()
        projection_card.setObjectName("card")
        apply_shadow(projection_card)
        
        projection_layout = QVBoxLayout(projection_card)
        projection_layout.setContentsMargins(20, 20, 20, 20)
        projection_layout.setSpacing(16)
        
        # Header com título e botão
        header_layout = QHBoxLayout()
        
        proj_title = QLabel("Projeção Anual")
        proj_title.setObjectName("section_title")
        header_layout.addWidget(proj_title)
        
        header_layout.addStretch()
        
        btn_export = QPushButton("📥  Exportar CSV")
        btn_export.setObjectName("btn_export")
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.clicked.connect(self._on_export_csv)
        header_layout.addWidget(btn_export)
        
        projection_layout.addLayout(header_layout)
        
        # Tabela
        self.projection_table = ProjectionTable()
        self.projection_table.setMinimumHeight(300)
        projection_layout.addWidget(self.projection_table)
        
        layout.addWidget(projection_card)
    
    def _parse_value(self, text: str) -> float:
        """Converte texto para float."""
        if not text.strip():
            return 0.0
        clean = text.replace("R$", "").replace(" ", "").strip()
        if "," in clean and "." in clean:
            if clean.rfind(",") > clean.rfind("."):
                clean = clean.replace(".", "").replace(",", ".")
            else:
                clean = clean.replace(",", "")
        elif "," in clean:
            clean = clean.replace(",", ".")
        try:
            return float(clean)
        except:
            return 0.0
    
    def _validate_inputs(self):
        """Valida todos os inputs."""
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
                periodo = int(float(periodo_text))
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
            periodo_anos=int(float(self.input_periodo.text())),
            meta=self._parse_value(self.input_meta.text()),
            n_simulations=self.spin_simulations.value()
        )
        
        return True, [], mc_input
    
    def _on_calculate(self):
        """Executa a simulação."""
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
            # Simulação simples
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
        # Cards principais
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
                f"<b>{result.n_simulations:,}</b> cenários simulados<br>"
                f"Saldo Final Médio: <b>{format_currency(result.final_balance_mean)}</b><br>"
                f"Intervalo: {format_currency(result.final_balance_min)} → "
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
        
        # Gráficos Plotly
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
        
        total = result.total_invested
        rentabilidade = (result.total_interest_det / total * 100) if total > 0 else 0
        
        lines = [
            f"• Investimento: {initial_fmt} + {monthly_fmt}/mês",
            f"• Rentabilidade: {params['rentabilidade_anual']:.2f}% a.a.",
            f"• Saldo final: {final_fmt}",
            f"• Lucro total: {interest_fmt}",
            f"• Rentabilidade acumulada: {rentabilidade:.2f}%"
        ]
        
        self.analysis_box.analysis_label.setText("<br>".join(lines))
    
    def _on_reset(self):
        """Reseta todos os campos."""
        self.input_capital.clear()
        self.input_aporte.clear()
        self.input_rentabilidade.clear()
        self.input_meta.clear()
        self.input_periodo.clear()
        
        self.spin_simulations.setValue(5000)
        
        self.card_invested.set_value("R$ 0,00")
        self.card_interest.set_value("R$ 0,00")
        self.card_final.set_value("R$ 0,00")
        self.card_goal.status_label.setText("—")
        self.card_goal.percent_label.setText("")
        
        self.analysis_box.analysis_label.setText("")
        self.mc_summary.setVisible(False)
        
        self.sensitivity_dashboard.reset()
        
        self.evolution_chart._show_empty()
        self.composition_chart._show_empty()
        
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
