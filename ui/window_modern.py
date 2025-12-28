"""
PyInvest - Janela Principal Moderna v4.1
Interface com Flat Design, Modo Expert, e Análise de Risco.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy,
    QScrollArea, QMessageBox, QSpacerItem, QFileDialog,
    QSpinBox, QGroupBox, QProgressBar, QGraphicsDropShadowEffect,
    QDateEdit, QTabWidget, QCheckBox, QComboBox, QMenuBar, QMenu,
    QStatusBar, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QThreadPool, QDate, Signal
from PySide6.QtGui import QFont, QColor, QAction, QKeySequence

from datetime import date
from typing import Optional, List
import numpy as np

from core.monte_carlo import (
    ParameterRange, MonteCarloInput, MonteCarloResult,
    MonteCarloEngine, MonteCarloWorker, RepresentativeScenario
)
from core.calculation import format_currency
from core.events import EventsManager, ExtraordinaryEvent
from core.statistics import (
    ProjectData, ParameterSet, HistoricalReturn, MonteCarloConfig,
    PercentileStats, RiskMetrics, ImplicitParameters,
    save_project, load_project,
    calculate_percentiles, extract_implicit_parameters, calculate_risk_metrics,
    get_risk_free_rate, clear_cdi_cache, get_cdi_info
)
from core.bootstrap import SyntheticScenariosResult, SyntheticDataConfig
from ui.styles_modern import get_modern_style, get_colors, apply_shadow
from ui.plotly_charts import EvolutionChartPlotly, CompositionChartPlotly
from ui.widgets import (
    SummaryCard, GoalStatusCard, ProjectionTable, 
    AnalysisBox, SensitivityDashboard
)
from ui.events_dialog import EventsDialog
from ui.historical_dialog import HistoricalReturnsDialog
from ui.monthly_data_wizard import MonthlyDataWizard
from ui.advanced_widgets import (
    RiskMetricsPanel, PercentileStatsPanel,
    ImplicitParametersTable, DistributionChart, ProjectionChartExpert
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
    
    def get_min_value(self) -> str:
        """Retorna valor mínimo."""
        return self.input_min.text()
    
    def get_base_value(self) -> str:
        """Retorna valor base/determinístico."""
        return self.input_det.text()
    
    def get_max_value(self) -> str:
        """Retorna valor máximo."""
        return self.input_max.text()
    
    def _format_value_ptbr(self, value) -> str:
        """Formata um valor numérico para o padrão pt-BR."""
        if value is None:
            return ""
        try:
            num = float(value)
            # Formata com separador de milhar e decimal pt-BR
            # Ex: 1400000.0 → "1.400.000,00"
            formatted = f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return formatted
        except (ValueError, TypeError):
            return str(value) if value else ""
    
    def set_min_value(self, value):
        """Define valor mínimo (formatado pt-BR)."""
        self.input_min.setText(self._format_value_ptbr(value))
    
    def set_base_value(self, value):
        """Define valor base/determinístico (formatado pt-BR)."""
        self.input_det.setText(self._format_value_ptbr(value))
    
    def set_max_value(self, value):
        """Define valor máximo (formatado pt-BR)."""
        self.input_max.setText(self._format_value_ptbr(value))
    
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
        
        # Gerenciador de eventos extraordinários
        self.events_manager = EventsManager()
        
        # Dados de rendimento histórico para Bootstrap
        self.historical_returns: List[HistoricalReturn] = []
        
        # Cenários sintéticos gerados pelo Bootstrap mensal
        self.synthetic_scenarios: Optional[SyntheticScenariosResult] = None
        
        # Resultado atual da simulação
        self.current_result: Optional[MonteCarloResult] = None
        self.current_final_balances: Optional[np.ndarray] = None
        
        # Estatísticas calculadas
        self.percentile_stats: Optional[PercentileStats] = None
        self.risk_metrics: Optional[RiskMetrics] = None
        self.implicit_params: Optional[List[ImplicitParameters]] = None
        
        # Caminho do projeto atual
        self.current_project_path: Optional[str] = None
        
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_ui()
    
    def _setup_menu_bar(self):
        """Configura a barra de menu."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E7EB;
                padding: 4px 8px;
            }
            QMenuBar::item {
                padding: 8px 16px;
                border-radius: 6px;
            }
            QMenuBar::item:selected {
                background-color: #F3F4F6;
            }
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px;
            }
            QMenu::item {
                padding: 8px 32px 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #F3F4F6;
            }
        """)
        
        # Menu Arquivo
        file_menu = menubar.addMenu("&Arquivo")
        
        new_action = QAction("📄 Novo Projeto", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._on_new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("📂 Abrir Projeto...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._on_open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("💾 Salvar", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._on_save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("💾 Salvar Como...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._on_save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 Sair", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Exportar
        export_menu = menubar.addMenu("&Exportar")
        
        export_csv_action = QAction("📊 Exportar Projeção (CSV)", self)
        export_csv_action.triggered.connect(self._on_export_csv)
        export_menu.addAction(export_csv_action)
        
        export_scenarios_action = QAction("🎯 Exportar Cenários (CSV)", self)
        export_scenarios_action.triggered.connect(self._on_export_scenarios)
        export_menu.addAction(export_scenarios_action)
        
        # Menu Configurações
        config_menu = menubar.addMenu("&Configurações")
        
        update_cdi_action = QAction("📈 Atualizar Taxa CDI", self)
        update_cdi_action.triggered.connect(self._on_update_cdi_rate)
        config_menu.addAction(update_cdi_action)
        
        # Menu Ajuda
        help_menu = menubar.addMenu("&Ajuda")
        
        about_action = QAction("ℹ️ Sobre", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """Configura a barra de status."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #F9FAFB;
                border-top: 1px solid #E5E7EB;
                padding: 4px 16px;
            }
        """)
        self.status_bar.showMessage("Pronto")
    
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
        header.setMinimumHeight(100)
        apply_shadow(header)
        
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(6)
        header_layout.setContentsMargins(24, 20, 24, 20)
        
        # Título com ícone
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        title_layout.setSpacing(10)
        
        # Ícone emoji
        icon = QLabel("💰")
        icon.setStyleSheet("""
            font-size: 32px; 
            background: transparent;
            line-height: 1;
        """)
        
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
        
        # Data de Início
        date_label = QLabel("Data de Início da Simulação")
        date_label.setObjectName("field_label")
        card_layout.addWidget(date_label)
        
        self.input_start_date = QDateEdit()
        self.input_start_date.setCalendarPopup(True)
        self.input_start_date.setDate(QDate.currentDate())
        self.input_start_date.setDisplayFormat("dd/MM/yyyy")
        self.input_start_date.setStyleSheet("""
            QDateEdit {
                background-color: #FFFFFF;
                border: 2px solid #E5E7EB;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 14px;
                color: #1F2937;
                min-height: 20px;
            }
            QDateEdit:focus {
                border-color: #10B981;
            }
            QDateEdit::drop-down {
                border: none;
                width: 30px;
            }
            QDateEdit::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #6B7280;
                margin-right: 10px;
            }
        """)
        card_layout.addWidget(self.input_start_date)
        
        date_help = QLabel("📅 Defina quando a simulação começa (para sincronizar eventos)")
        date_help.setStyleSheet("""
            font-size: 11px;
            color: #9CA3AF;
            font-style: italic;
            background: transparent;
        """)
        card_layout.addWidget(date_help)
        
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
        
        # === MODO EXPERT ===
        expert_layout = QHBoxLayout()
        expert_layout.setSpacing(12)
        
        self.check_expert_mode = QCheckBox("🔬 Modo Expert")
        self.check_expert_mode.setStyleSheet("""
            QCheckBox {
                font-weight: 600;
                font-size: 13px;
                color: #7C3AED;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #D1D5DB;
            }
            QCheckBox::indicator:checked {
                background-color: #7C3AED;
                border-color: #7C3AED;
            }
        """)
        self.check_expert_mode.toggled.connect(self._on_expert_mode_changed)
        expert_layout.addWidget(self.check_expert_mode)
        expert_layout.addStretch()
        
        mc_group_layout.addLayout(expert_layout)
        
        # Container de opções Expert (inicialmente oculto)
        self.expert_options = QWidget()
        expert_opts_layout = QVBoxLayout(self.expert_options)
        expert_opts_layout.setContentsMargins(0, 8, 0, 0)
        expert_opts_layout.setSpacing(8)
        
        # Método de simulação
        method_label = QLabel("Método de Simulação:")
        method_label.setStyleSheet("font-size: 12px; color: #374151; background: transparent;")
        expert_opts_layout.addWidget(method_label)
        
        self.combo_method = QComboBox()
        self.combo_method.addItems([
            "Bootstrap Histórico (Recomendado)",
            "Distribuição Normal (Gaussiana)",
            "Distribuição t-Student (Caudas Pesadas)"
        ])
        self.combo_method.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QComboBox:focus {
                border-color: #7C3AED;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
        """)
        expert_opts_layout.addWidget(self.combo_method)
        
        # Botão dados de rendimento
        self.btn_historical = QPushButton("📊 Dados de Rendimento")
        self.btn_historical.setStyleSheet("""
            QPushButton {
                background-color: #F5F3FF;
                color: #7C3AED;
                border: 2px solid #DDD6FE;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #EDE9FE;
                border-color: #C4B5FD;
            }
        """)
        self.btn_historical.setCursor(Qt.PointingHandCursor)
        self.btn_historical.clicked.connect(self._on_open_historical)
        expert_opts_layout.addWidget(self.btn_historical)
        
        # Status dos dados históricos
        self.historical_status = QLabel("")
        self.historical_status.setStyleSheet("""
            font-size: 11px;
            color: #6B7280;
            font-style: italic;
            background: transparent;
        """)
        expert_opts_layout.addWidget(self.historical_status)
        
        self.expert_options.setVisible(False)
        mc_group_layout.addWidget(self.expert_options)
        
        card_layout.addWidget(mc_group)
        
        card_layout.addSpacing(12)
        
        # === EVENTOS EXTRAORDINÁRIOS ===
        btn_events = QPushButton("📅  Eventos Extraordinários")
        btn_events.setObjectName("btn_secondary")
        btn_events.setCursor(Qt.PointingHandCursor)
        btn_events.clicked.connect(self._on_open_events)
        btn_events.setStyleSheet("""
            QPushButton {
                background-color: #EFF6FF;
                color: #1E40AF;
                border: 2px solid #BFDBFE;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #DBEAFE;
                border-color: #93C5FD;
            }
        """)
        card_layout.addWidget(btn_events)
        
        # Label de status dos eventos
        self.events_status_label = QLabel("")
        self.events_status_label.setStyleSheet("""
            font-size: 11px;
            color: #6B7280;
            font-style: italic;
            background: transparent;
            padding-left: 4px;
        """)
        self.events_status_label.setVisible(False)
        card_layout.addWidget(self.events_status_label)
        
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
        """Cria a seção de gráficos com abas (Projeção, Distribuição, Análise de Risco)."""
        charts_card = QFrame()
        charts_card.setObjectName("card")
        apply_shadow(charts_card)
        
        charts_main_layout = QVBoxLayout(charts_card)
        charts_main_layout.setContentsMargins(20, 20, 20, 20)
        charts_main_layout.setSpacing(12)
        
        # QTabWidget para as abas
        self.charts_tabs = QTabWidget()
        self.charts_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 4px;
                font-weight: 500;
                color: #6B7280;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #10B981;
                border-bottom: 2px solid #10B981;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E5E7EB;
            }
        """)
        
        # =====================================================================
        # ABA 1: PROJEÇÃO (Gráficos + Tabela de Cenários)
        # =====================================================================
        projection_tab = QWidget()
        projection_main = QVBoxLayout(projection_tab)
        # Maximizar área útil: margens mínimas
        projection_main.setSpacing(10)
        projection_main.setContentsMargins(0, 5, 0, 5)
        
        # --- LINHA SUPERIOR: Gráficos (Proporção Áurea 3:1) ---
        charts_row = QHBoxLayout()
        charts_row.setSpacing(10)
        charts_row.setContentsMargins(8, 0, 8, 0)
        
        # Gráfico de Evolução (75% - stretch 3)
        evolution_frame = QFrame()
        evolution_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        evolution_inner = QVBoxLayout(evolution_frame)
        evolution_inner.setContentsMargins(12, 8, 12, 8)
        evolution_inner.setSpacing(4)
        
        evolution_title = QLabel("📈 Evolução do Patrimônio")
        evolution_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151; background: transparent;")
        evolution_inner.addWidget(evolution_title)
        
        self.evolution_chart = EvolutionChartPlotly()
        self.evolution_chart.setMinimumHeight(300)
        self.evolution_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        evolution_inner.addWidget(self.evolution_chart)
        
        charts_row.addWidget(evolution_frame, stretch=3)  # Proporção Áurea
        
        # Gráfico de Composição (25% - stretch 1)
        composition_frame = QFrame()
        composition_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        composition_inner = QVBoxLayout(composition_frame)
        composition_inner.setContentsMargins(12, 8, 12, 8)
        composition_inner.setSpacing(4)
        
        composition_title = QLabel("🥧 Composição")
        composition_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151; background: transparent;")
        composition_inner.addWidget(composition_title)
        
        self.composition_chart = CompositionChartPlotly()
        self.composition_chart.setMinimumHeight(300)
        self.composition_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        composition_inner.addWidget(self.composition_chart)
        
        charts_row.addWidget(composition_frame, stretch=1)  # Proporção Áurea
        
        projection_main.addLayout(charts_row, stretch=65)
        
        # --- LINHA INFERIOR: Tabela de Cenários Reproduzíveis ---
        scenarios_frame = QFrame()
        scenarios_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        scenarios_inner = QVBoxLayout(scenarios_frame)
        scenarios_inner.setContentsMargins(12, 8, 12, 8)
        scenarios_inner.setSpacing(6)
        
        # Cabeçalho compacto
        scenarios_header = QHBoxLayout()
        scenarios_title = QLabel("🎯 Cenários Reproduzíveis")
        scenarios_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151; background: transparent;")
        scenarios_header.addWidget(scenarios_title)
        scenarios_header.addStretch()
        scenarios_hint = QLabel("💡 Duplo clique para carregar")
        scenarios_hint.setStyleSheet("font-size: 10px; color: #9CA3AF; background: transparent;")
        scenarios_header.addWidget(scenarios_hint)
        scenarios_inner.addLayout(scenarios_header)
        
        # Tabela
        self.table_cenarios = QTableWidget()
        self.table_cenarios.setColumnCount(6)
        self.table_cenarios.setHorizontalHeaderLabels([
            'Cenário', 'Percentil', 'Capital Inicial', 
            'Aporte Mensal', 'Rent. Anual', 'Saldo Final'
        ])
        
        header_cenarios = self.table_cenarios.horizontalHeader()
        
        # ========================================================
        # MODO INTERACTIVE: Permite redimensionamento manual
        # ========================================================
        header_cenarios.setSectionResizeMode(QHeaderView.Interactive)
        header_cenarios.setMinimumSectionSize(100)  # Proteção contra "R$..."
        header_cenarios.setStretchLastSection(True)
        
        # Alinhamento centralizado dos cabeçalhos
        header_cenarios.setDefaultAlignment(Qt.AlignCenter)
        
        # Larguras iniciais
        self.table_cenarios.setColumnWidth(0, 150)
        self.table_cenarios.setColumnWidth(1, 80)
        self.table_cenarios.setColumnWidth(2, 130)
        self.table_cenarios.setColumnWidth(3, 120)
        self.table_cenarios.setColumnWidth(4, 100)
        self.table_cenarios.setColumnWidth(5, 140)
        
        self.table_cenarios.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_cenarios.setAlternatingRowColors(True)
        self.table_cenarios.verticalHeader().setVisible(False)
        
        # Altura calculada: 6 linhas (P5,P25,P50,P75,P95,Média) + cabeçalho
        # rowHeight ~28px, header ~32px = 28*6 + 32 = 200px
        self.table_cenarios.setMinimumHeight(200)
        self.table_cenarios.setMaximumHeight(230)
        self.table_cenarios.verticalHeader().setDefaultSectionSize(28)
        
        self.table_cenarios.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: #F3F4F6;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 4px 6px;
                border-bottom: 1px solid #F3F4F6;
            }
            QTableWidget::item:selected {
                background-color: #DBEAFE;
                color: #1E40AF;
            }
            QHeaderView::section {
                background-color: #F9FAFB;
                border: none;
                border-bottom: 2px solid #E5E7EB;
                padding: 6px 8px;
                font-weight: 600;
                font-size: 11px;
                color: #374151;
            }
        """)
        
        self.table_cenarios.cellDoubleClicked.connect(self._on_cenario_double_clicked)
        scenarios_inner.addWidget(self.table_cenarios)
        
        projection_main.addWidget(scenarios_frame, stretch=35)
        
        self.charts_tabs.addTab(projection_tab, "📊 Projeção")
        
        # =====================================================================
        # ABA 2: DISTRIBUIÇÃO (Histograma + Estatísticas)
        # =====================================================================
        distribution_tab = QWidget()
        distribution_main = QHBoxLayout(distribution_tab)
        distribution_main.setSpacing(16)
        distribution_main.setContentsMargins(16, 16, 16, 16)
        
        # --- ESQUERDA (70%): Histograma ---
        hist_frame = QFrame()
        hist_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 10px;
            }
        """)
        hist_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        hist_inner = QVBoxLayout(hist_frame)
        hist_inner.setContentsMargins(16, 12, 16, 12)
        
        hist_title = QLabel("📊 Distribuição dos Saldos Finais")
        hist_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #374151; background: transparent;")
        hist_inner.addWidget(hist_title)
        
        self.distribution_chart = DistributionChart()
        self.distribution_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        hist_inner.addWidget(self.distribution_chart)
        
        distribution_main.addWidget(hist_frame, stretch=70)
        
        # --- DIREITA (30%): Estatísticas ---
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 10px;
            }
        """)
        stats_inner = QVBoxLayout(stats_frame)
        stats_inner.setContentsMargins(16, 0, 16, 12)  # Topo zerado para alinhar com título do histograma
        stats_inner.setSpacing(8)
        
        stats_title = QLabel("📈 Estatísticas de Saldos Finais")
        stats_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #374151; background: transparent;")
        stats_title.setFixedHeight(20)  # Mesma altura do título do histograma
        stats_inner.addWidget(stats_title)
        
        # Painel de estatísticas (sem título duplicado)
        self.percentile_stats_panel = PercentileStatsPanel(show_title=False)
        stats_inner.addWidget(self.percentile_stats_panel)
        
        distribution_main.addWidget(stats_frame, stretch=30)
        
        self.charts_tabs.addTab(distribution_tab, "📉 Distribuição")
        
        # =====================================================================
        # ABA 3: ANÁLISE DE RISCO (Cards de Métricas)
        # =====================================================================
        risk_tab = QWidget()
        risk_main = QVBoxLayout(risk_tab)
        risk_main.setSpacing(20)
        risk_main.setContentsMargins(16, 16, 16, 16)
        
        # --- CARDS DE MÉTRICAS (Grid 2x3) ---
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
            }
        """)
        metrics_inner = QVBoxLayout(metrics_frame)
        metrics_inner.setContentsMargins(20, 16, 20, 16)
        metrics_inner.setSpacing(16)
        
        metrics_title = QLabel("📊 Métricas de Risco")
        metrics_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1F2937; background: transparent;")
        metrics_inner.addWidget(metrics_title)
        
        # Grid 2x4 de cards (8 cartões)
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(10)
        metrics_grid.setContentsMargins(0, 0, 0, 0)
        
        # Criar cards de métricas (Grid 2x4 - 8 cartões)
        self.risk_cards = {}
        card_configs = [
            # Linha 1: Probabilidades, VaR e CVaR
            ('success', '✅ Prob. Sucesso', '—%', 
             'Percentual de cenários onde você atinge sua meta final\n'
             'P(Sucesso) = (# Saldos ≥ Meta) ÷ Total × 100%', 
             '#DCFCE7', '#16A34A', 0, 0),
            ('ruin', '❌ Prob. Ruína', '—%', 
             'Risco de perder dinheiro do capital investido\n'
             'P(Ruína) = (# Saldos < Capital) ÷ Total × 100%', 
             '#FEE2E2', '#DC2626', 0, 1),
            ('var', '⚠️ VaR 95%', 'R$ —', 
             'Perda máxima esperada em 5% dos piores cenários\n'
             'VaR₉₅ = Média − P₅', 
             '#FEF3C7', '#D97706', 0, 2),
            ('cvar', '🍷 CVaR 95%', 'R$ —', 
             'Média das perdas nos 5% piores cenários (cauda)\n'
             'CVaR = E[X | X ≤ VaR] (Expected Shortfall)', 
             '#FDF2F8', '#A52A2A', 0, 3),
            # Linha 2: Volatilidade, Risco/Retorno e Sharpe
            ('volatility', '📊 Volatilidade', 'R$ —', 
             'Dispersão dos saldos finais em relação à média\n'
             'σ = √[ Σ(Saldo − Média)² ÷ N ]', 
             '#F3E8FF', '#6F42C1', 1, 0),
            ('ratio', '⚖️ Risco/Retorno', '—', 
             'Quanto de risco por cada real de ganho\n'
             'Razão = VaR₉₅ ÷ Ganho Esperado', 
             '#FCE7F3', '#DB2777', 1, 1),
            ('sharpe', '📈 Sharpe Ratio', '—', 
             'Retorno por unidade de risco tomada\n'
             'Sharpe = (CAGR − CDI) ÷ Volatilidade', 
             '#DBEAFE', '#2563EB', 1, 2),
            ('cdi', '🏦 Taxa CDI', '—%', 
             'Taxa livre de risco utilizada nos cálculos\n'
             'Fonte: B3 (via API do Banco Central)', 
             '#F0FDF4', '#15803D', 1, 3),
        ]
        
        for key, title, default_value, description, bg_color, text_color, row, col in card_configs:
            card = self._create_metric_card(title, default_value, description, bg_color, text_color)
            self.risk_cards[key] = card['value_label']
            metrics_grid.addWidget(card['frame'], row, col)
        
        metrics_inner.addLayout(metrics_grid)
        risk_main.addWidget(metrics_frame, stretch=60)
        
        # --- RESUMO DE RESULTADOS ---
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
            }
        """)
        summary_inner = QVBoxLayout(summary_frame)
        summary_inner.setContentsMargins(20, 16, 20, 16)
        summary_inner.setSpacing(12)
        
        summary_title = QLabel("📊 Resumo Monte Carlo")
        summary_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #374151; background: transparent;")
        summary_inner.addWidget(summary_title)
        
        self.risk_summary_label = QLabel("Execute uma simulação Monte Carlo para ver o resumo de risco.")
        self.risk_summary_label.setStyleSheet("""
            font-size: 13px; 
            color: #6B7280; 
            background: transparent;
            padding: 12px;
        """)
        self.risk_summary_label.setWordWrap(True)
        summary_inner.addWidget(self.risk_summary_label)
        
        risk_main.addWidget(summary_frame, stretch=40)
        
        self.charts_tabs.addTab(risk_tab, "⚠️ Análise de Risco")
        
        charts_main_layout.addWidget(self.charts_tabs)
        layout.addWidget(charts_card)
    
    def _create_metric_card(self, title: str, default_value: str, description: str, 
                           bg_color: str, text_color: str) -> dict:
        """Cria um card de métrica estilizado."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 8px;
                border: 1px solid {bg_color};
            }}
        """)
        frame.setMinimumHeight(100)
        frame.setMaximumHeight(140)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 11px; 
            font-weight: 600; 
            color: {text_color}; 
            background: transparent;
        """)
        layout.addWidget(title_label)
        
        # Valor
        value_label = QLabel(default_value)
        value_label.setStyleSheet(f"""
            font-size: 18px; 
            font-weight: bold; 
            color: {text_color}; 
            background: transparent;
        """)
        layout.addWidget(value_label)
        
        # Descrição
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            font-size: 10px; 
            color: #6B7280; 
            background: transparent;
        """)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Tooltip com explicação simplificada
        tooltip_text = description.replace('\n', ' - ')
        frame.setToolTip(f"<b>{title}</b><br><br>{tooltip_text}")
        
        layout.addStretch()
        
        return {'frame': frame, 'value_label': value_label, 'desc_label': desc_label}
    
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
        """
        Valida todos os inputs.
        
        Modo Normal: Requer valores determinísticos ou ranges completos.
        Modo Expert: Campos Base são opcionais se houver >= 2 registros históricos.
        """
        errors = []
        
        # Verificar se está em Modo Expert
        is_expert_mode = hasattr(self, 'check_expert_mode') and self.check_expert_mode.isChecked()
        has_historical = len(self.historical_returns) >= 2
        
        # Obter ranges
        capital_range = self.input_capital.get_parameter_range()
        aporte_range = self.input_aporte.get_parameter_range()
        rent_range = self.input_rentabilidade.get_parameter_range()
        
        # =====================================================================
        # MODO EXPERT: VALIDAÇÃO FLEXÍVEL
        # =====================================================================
        if is_expert_mode and has_historical:
            # Calcular estatísticas dos retornos históricos
            returns = [r.return_rate * 100 for r in self.historical_returns]
            avg_return = float(np.mean(returns))
            std_return = float(np.std(returns))
            
            # Capital: se não preenchido, usar valor mínimo razoável
            if capital_range.deterministic is None and capital_range.min_value is None:
                # Capital é obrigatório - precisa de pelo menos um valor
                errors.append("Capital Inicial: informe pelo menos o valor base.")
            elif capital_range.deterministic is None and capital_range.min_value is not None:
                # Usar min como base
                capital_range = ParameterRange(
                    min_value=capital_range.min_value,
                    deterministic=capital_range.min_value,
                    max_value=capital_range.max_value or capital_range.min_value * 1.5
                )
            
            # Aporte: se não preenchido, assume zero
            if aporte_range.deterministic is None and aporte_range.min_value is None:
                aporte_range = ParameterRange(
                    min_value=0,
                    deterministic=0,
                    max_value=0
                )
            elif aporte_range.deterministic is None:
                aporte_range = ParameterRange(
                    min_value=aporte_range.min_value or 0,
                    deterministic=aporte_range.min_value or 0,
                    max_value=aporte_range.max_value or aporte_range.min_value or 0
                )
            
            # Rentabilidade: derivar dos dados históricos
            if rent_range.deterministic is None and rent_range.min_value is None:
                rent_range = ParameterRange(
                    min_value=max(-30, avg_return - 2 * std_return),
                    deterministic=avg_return,
                    max_value=min(100, avg_return + 2 * std_return)
                )
                self.status_bar.showMessage(
                    f"📊 Modo Expert: Rentabilidade derivada = {avg_return:.1f}% ± {std_return:.1f}% "
                    f"({len(self.historical_returns)} anos históricos)"
                )
            elif rent_range.deterministic is None:
                rent_range = ParameterRange(
                    min_value=rent_range.min_value,
                    deterministic=avg_return,
                    max_value=rent_range.max_value or avg_return + 2 * std_return
                )
        
        # =====================================================================
        # MODO NORMAL: VALIDAÇÃO TRADICIONAL
        # =====================================================================
        else:
            # Validar Capital (sempre obrigatório)
            is_valid, error = capital_range.validate()
            if not is_valid:
                errors.append(f"Capital Inicial: {error}")
            
            # Validar Aporte
            is_valid, error = aporte_range.validate()
            if not is_valid:
                errors.append(f"Aporte Mensal: {error}")
            
            # Validar Rentabilidade
            is_valid, error = rent_range.validate()
            if not is_valid:
                if is_expert_mode and not has_historical:
                    errors.append("Modo Expert: adicione pelo menos 2 registros de Rendimento Histórico.")
                else:
                    errors.append(f"Rentabilidade: {error}")
        
        # =====================================================================
        # VALIDAR PERÍODO (sempre obrigatório)
        # =====================================================================
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
        
        # =====================================================================
        # VALIDAÇÕES ESPECÍFICAS DO MODO EXPERT
        # =====================================================================
        if is_expert_mode:
            method_idx = self.combo_method.currentIndex() if hasattr(self, 'combo_method') else 0
            
            if method_idx == 0 and not has_historical:  # Bootstrap requer dados
                errors.append("Bootstrap: requer pelo menos 2 registros de rendimento histórico.")
            elif method_idx == 0 and len(self.historical_returns) < 2:
                errors.append(f"Bootstrap: encontrado apenas {len(self.historical_returns)} registro(s). Mínimo: 2.")
        
        if errors:
            return False, errors, None
        
        # Obter data de início
        qdate = self.input_start_date.date()
        start_date = date(qdate.year(), qdate.month(), qdate.day())
        
        # Obter retornos históricos em formato de lista de floats (%)
        historical_returns_list = []
        if is_expert_mode and has_historical:
            historical_returns_list = [r.return_rate * 100 for r in self.historical_returns]
        
        # Criar input Monte Carlo com todos os campos
        mc_input = MonteCarloInput(
            capital_inicial=capital_range,
            aporte_mensal=aporte_range,
            rentabilidade_anual=rent_range,
            periodo_anos=int(float(self.input_periodo.text())),
            meta=self._parse_value(self.input_meta.text()),
            n_simulations=self.spin_simulations.value(),
            start_date=start_date,
            events_manager=self.events_manager if self.events_manager.count > 0 else None,
            # Campos do Modo Expert
            expert_mode=is_expert_mode and has_historical,
            historical_returns=historical_returns_list,
            simulation_method=['bootstrap', 'normal', 't_student'][
                self.combo_method.currentIndex() if hasattr(self, 'combo_method') else 0
            ] if is_expert_mode else 'bootstrap'
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
            
            # Identificar método usado
            method_labels = {
                'bootstrap': '🔄 Bootstrap Histórico',
                'normal': '📊 Distribuição Normal',
                't_student': '📈 t-Student',
                'parameter_range': '📐 Ranges de Parâmetros'
            }
            method_label = method_labels.get(result.simulation_method, 'Monte Carlo')
            
            mc_text = (
                f"<b>{result.n_simulations:,}</b> cenários simulados<br>"
                f"Método: <b>{method_label}</b><br>"
                f"Capital Total Investido: <b>{format_currency(result.total_invested)}</b><br>"
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
        
        # Armazenar resultado atual
        self.current_result = result
        
        # Atualizar estatísticas avançadas (abas Expert, Distribuição, Risco)
        self._update_advanced_statistics(result)
        
        # Status bar
        method_info = ""
        if result.simulation_method:
            method_names = {
                'bootstrap': 'Bootstrap',
                'normal': 'Normal',
                't_student': 't-Student',
                'parameter_range': 'Ranges'
            }
            method_info = f" | Método: {method_names.get(result.simulation_method, result.simulation_method)}"
        
        self.status_bar.showMessage(
            f"✓ Simulação concluída | {result.n_simulations:,} cenários{method_info} | "
            f"Saldo final: {format_currency(result.final_balance_det)}"
        )
    
    def _update_analysis_text(self, result: MonteCarloResult):
        """Atualiza o texto de análise detalhado."""
        import math
        
        params = result.params_used
        
        # Valores formatados
        initial = params['capital_inicial']
        monthly = params['aporte_mensal']
        annual_rate = params['rentabilidade_anual']
        years = params['periodo_anos']
        meta = params.get('meta', 0)
        
        initial_fmt = format_currency(initial)
        monthly_fmt = format_currency(monthly)
        final_fmt = format_currency(result.final_balance_det)
        interest_fmt = format_currency(result.total_interest_det)
        invested_fmt = format_currency(result.total_invested)
        
        # Rentabilidade acumulada
        total = result.total_invested
        rentabilidade = (result.total_interest_det / total * 100) if total > 0 else 0
        
        # Construir linhas de análise
        lines = []
        
        # Investimento
        lines.append(f"<b>💼 Investimento</b>")
        lines.append(f"• Capital inicial: {initial_fmt}")
        lines.append(f"• Aporte mensal: {monthly_fmt}")
        lines.append(f"• Total investido: {invested_fmt}")
        lines.append("")
        
        # Rentabilidade
        lines.append(f"<b>📈 Rentabilidade</b>")
        lines.append(f"• Taxa anual: {annual_rate:.2f}% a.a.")
        lines.append(f"• Lucro com juros: {interest_fmt}")
        lines.append(f"• Rentabilidade acumulada: {rentabilidade:.1f}%")
        lines.append("")
        
        # Resultado
        lines.append(f"<b>🎯 Resultado Final</b>")
        lines.append(f"• Saldo após {years} anos: <span style='color:#10B981;font-weight:bold;'>{final_fmt}</span>")
        
        # Cálculo do tempo para atingir a meta (usando logaritmo)
        if meta > 0:
            time_to_goal = self._calculate_time_to_goal(initial, monthly, annual_rate, meta)
            
            if time_to_goal is not None:
                if time_to_goal <= years:
                    lines.append(f"• Meta de {format_currency(meta)}: "
                               f"<span style='color:#10B981;'>✓ Atingida em ~{time_to_goal:.1f} anos</span>")
                else:
                    lines.append(f"• Meta de {format_currency(meta)}: "
                               f"<span style='color:#F59E0B;'>→ Necessário ~{time_to_goal:.1f} anos</span>")
            else:
                lines.append(f"• Meta de {format_currency(meta)}: "
                           f"<span style='color:#EF4444;'>✗ Inatingível com estes parâmetros</span>")
        
        self.analysis_box.analysis_label.setText("<br>".join(lines))
    
    def _calculate_time_to_goal(self, initial: float, monthly: float, annual_rate: float, goal: float) -> float:
        """
        Calcula o tempo necessário para atingir a meta usando a fórmula logarítmica.
        
        Fórmula: t = ln((M*i + a) / (C*i + a)) / ln(1+i)
        
        Onde:
        - M = Meta (goal)
        - C = Capital inicial
        - a = Aporte mensal
        - i = Taxa mensal
        - t = Tempo em meses
        
        Args:
            initial: Capital inicial
            monthly: Aporte mensal
            annual_rate: Taxa de juros anual (%)
            goal: Meta a ser atingida
            
        Returns:
            Tempo em anos (float) ou None se impossível
        """
        import math
        
        # Se a meta já foi atingida
        if initial >= goal:
            return 0.0
        
        # Taxa mensal
        i = (1 + annual_rate / 100) ** (1/12) - 1
        
        # Se taxa é zero, fazer cálculo simples
        if i <= 0:
            if monthly <= 0:
                return None  # Impossível sem juros e sem aportes
            months = (goal - initial) / monthly
            return months / 12
        
        # Fórmula: t = ln((M*i + a) / (C*i + a)) / ln(1+i)
        numerator = goal * i + monthly
        denominator = initial * i + monthly
        
        # Verificar se é matematicamente possível
        if denominator <= 0 or numerator <= 0:
            return None
        
        if numerator <= denominator:
            # Meta já atingida ou inatingível
            if initial >= goal:
                return 0.0
            return None
        
        try:
            months = math.log(numerator / denominator) / math.log(1 + i)
            years = months / 12
            
            # Limitar a um valor razoável (máx 200 anos)
            if years > 200:
                return None
            
            return years
        except (ValueError, ZeroDivisionError):
            return None
    
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
        
        # Limpar eventos
        self.events_manager.clear()
        self._update_events_status()
    
    def _on_open_events(self):
        """Abre o diálogo de eventos extraordinários."""
        # Obter data de início
        qdate = self.input_start_date.date()
        start_date = date(qdate.year(), qdate.month(), qdate.day())
        
        # Obter período em meses
        try:
            years = int(float(self.input_periodo.text() or "10"))
        except:
            years = 10
        simulation_months = years * 12
        
        dialog = EventsDialog(
            self.events_manager, 
            start_date=start_date,
            simulation_months=simulation_months,
            parent=self
        )
        dialog.events_confirmed.connect(self._on_events_confirmed)
        dialog.exec()
    
    def _on_events_confirmed(self, events_manager: EventsManager):
        """Callback quando eventos são confirmados."""
        self.events_manager = events_manager
        self._update_events_status()
    
    def _update_events_status(self):
        """Atualiza o label de status dos eventos."""
        count = self.events_manager.count
        
        if count > 0:
            deposits = self.events_manager.total_deposits
            withdrawals = self.events_manager.total_withdrawals
            
            status_parts = [f"📅 {count} evento{'s' if count != 1 else ''}"]
            if deposits > 0:
                status_parts.append(f"+{format_currency(deposits)}")
            if withdrawals > 0:
                status_parts.append(f"-{format_currency(withdrawals)}")
            
            self.events_status_label.setText(" | ".join(status_parts))
            self.events_status_label.setVisible(True)
        else:
            self.events_status_label.setVisible(False)
    
    def _on_export_csv(self):
        """Exporta dados para CSV com tratamento de erros detalhado."""
        if not self.projection_table.has_data():
            QMessageBox.warning(self, "Sem Dados", "Execute uma simulação primeiro.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Projeção CSV", 
            "projecao_investimento.csv", 
            "Arquivos CSV (*.csv);;Todos os arquivos (*)"
        )
        
        if not filepath:
            return  # Usuário cancelou
        
        # Garantir extensão .csv
        if not filepath.lower().endswith('.csv'):
            filepath += '.csv'
        
        success, error_msg = self.projection_table.export_to_csv(filepath)
        
        if success:
            QMessageBox.information(
                self, "Exportação Concluída", 
                f"Dados exportados com sucesso!\n\nArquivo salvo em:\n{filepath}"
            )
        else:
            QMessageBox.critical(
                self, "Erro na Exportação", 
                f"Não foi possível exportar os dados.\n\n{error_msg}"
            )
    
    # =========================================================================
    # NOVOS MÉTODOS - MÓDULO ESTATÍSTICO v4.1
    # =========================================================================
    
    def _on_expert_mode_changed(self, checked: bool):
        """Toggle do Modo Expert."""
        self.expert_options.setVisible(checked)
        
        if checked:
            self.status_bar.showMessage("🔬 Modo Expert ativado - Configure dados históricos para Bootstrap")
        else:
            self.status_bar.showMessage("Modo padrão ativo")
    
    def _on_open_historical(self):
        """Abre wizard de dados históricos (mensais ou anuais)."""
        wizard = MonthlyDataWizard(self)
        
        # Se usuário escolher dados anuais, abre dialog tradicional
        wizard.use_annual_data.connect(self._open_annual_historical_dialog)
        
        # Se cenários forem confirmados
        wizard.scenarios_confirmed.connect(self._on_synthetic_scenarios_confirmed)
        
        wizard.exec()
    
    def _open_annual_historical_dialog(self):
        """Abre diálogo tradicional de dados anuais."""
        dialog = HistoricalReturnsDialog(self.historical_returns, self)
        dialog.returns_confirmed.connect(self._on_historical_confirmed)
        dialog.exec()
    
    def _on_synthetic_scenarios_confirmed(self, result: SyntheticScenariosResult):
        """Callback quando cenários sintéticos são confirmados."""
        # Armazenar resultado
        self.synthetic_scenarios = result
        
        # Criar dados históricos "virtuais" a partir dos cenários
        # Isso permite compatibilidade com o fluxo existente
        self.historical_returns = []
        
        # Atualizar status
        self._update_synthetic_status()
    
    def _update_synthetic_status(self):
        """Atualiza status com cenários sintéticos."""
        if hasattr(self, 'synthetic_scenarios') and self.synthetic_scenarios is not None:
            result = self.synthetic_scenarios
            self.historical_status.setText(
                f"✓ {result.n_scenarios:,} cenários sintéticos | "
                f"Média: {result.mean:.1f}% | P5/P95: {result.p5:.1f}%/{result.p95:.1f}%"
            )
            self.historical_status.setStyleSheet("""
                font-size: 11px;
                color: #3B82F6;
                font-style: normal;
                font-weight: 600;
                background: transparent;
            """)
    
    def _on_historical_confirmed(self, returns: List[HistoricalReturn]):
        """Callback quando dados históricos são confirmados."""
        self.historical_returns = returns
        self._update_historical_status()
    
    def _update_historical_status(self):
        """Atualiza status dos dados históricos."""
        count = len(self.historical_returns)
        
        if count > 0:
            years = [r.year for r in self.historical_returns]
            mean_return = np.mean([r.return_rate * 100 for r in self.historical_returns])
            
            self.historical_status.setText(
                f"✓ {count} anos ({min(years)}-{max(years)}) | Média: {mean_return:.1f}%"
            )
            self.historical_status.setStyleSheet("""
                font-size: 11px;
                color: #059669;
                font-style: normal;
                font-weight: 500;
                background: transparent;
            """)
        else:
            self.historical_status.setText("Nenhum dado histórico")
            self.historical_status.setStyleSheet("""
                font-size: 11px;
                color: #9CA3AF;
                font-style: italic;
                background: transparent;
            """)
    
    def _on_scenario_clicked(self, params: dict):
        """Carrega parâmetros de um cenário clicado."""
        reply = QMessageBox.question(
            self, "Carregar Cenário",
            f"Deseja carregar os parâmetros do cenário '{params.get('scenario_name', '')}'?\n\n"
            f"Capital: {format_currency(params['capital_inicial'])}\n"
            f"Aporte: {format_currency(params['aporte_mensal'])}\n"
            f"Rentabilidade: {params['rentabilidade_anual']:.2f}%",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Preencher campos com valores do cenário
            self.input_capital.set_base_value(params['capital_inicial'])
            self.input_aporte.set_base_value(params['aporte_mensal'])
            self.input_rentabilidade.set_base_value(params['rentabilidade_anual'])
            
            self.status_bar.showMessage(f"✓ Cenário '{params['scenario_name']}' carregado")
    
    def _on_cenario_double_clicked(self, row: int, col: int):
        """Handler para duplo clique na tabela de cenários."""
        if not hasattr(self, '_cenarios_data') or row >= len(self._cenarios_data):
            return
        
        p = self._cenarios_data[row]
        params = {
            'scenario_name': p.scenario_name,
            'capital_inicial': p.capital_inicial,
            'aporte_mensal': p.aporte_mensal,
            'rentabilidade_anual': p.rentabilidade_anual,
            'saldo_final': p.saldo_final
        }
        self._on_scenario_clicked(params)
    
    def _populate_cenarios_table(self, scenarios: List[RepresentativeScenario]):
        """
        Popula a tabela de cenários reproduzíveis com parâmetros REAIS.
        
        Cada cenário representa uma simulação real do Monte Carlo,
        com os parâmetros exatos que geraram aquele resultado.
        """
        self._cenarios_data = scenarios
        self.table_cenarios.setRowCount(len(scenarios))
        
        # Cores por tipo de cenário
        colors = {
            'Worst Case': '#FEE2E2',
            'Conservador': '#FEF3C7',
            'Típico': '#DBEAFE',
            'Otimista': '#DCFCE7',
            'Best Case': '#D1FAE5',
            'Valor Esperado': '#F3E8FF',
        }
        
        for row, s in enumerate(scenarios):
            bg_color = QColor(colors.get(s.scenario_type, '#FFFFFF'))
            
            # Formatar valores com máscara brasileira
            capital_fmt = f"R$ {s.capital_inicial:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            aporte_fmt = f"R$ {s.aporte_mensal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            rent_fmt = f"{s.rentabilidade_anual:.2f}%".replace(".", ",")
            saldo_fmt = f"R$ {s.saldo_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            # Todos os itens CENTRALIZADOS
            items = [
                s.scenario_name,
                s.percentile,
                capital_fmt,
                aporte_fmt,
                rent_fmt,
                saldo_fmt,
            ]
            
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)  # Centralizado
                item.setBackground(bg_color)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Não editável
                self.table_cenarios.setItem(row, col, item)
        
        # Ajustar altura das linhas
        self.table_cenarios.resizeRowsToContents()
        
        # Ajustar largura das colunas ao conteúdo (corrige corte em "PERCENTIL")
        self.table_cenarios.resizeColumnsToContents()
        
        # Garantir largura mínima após resize
        min_widths = [120, 80, 130, 120, 100, 140]
        for col, min_w in enumerate(min_widths):
            if self.table_cenarios.columnWidth(col) < min_w:
                self.table_cenarios.setColumnWidth(col, min_w)
    
    def _update_advanced_statistics(self, result: MonteCarloResult):
        """
        Atualiza estatísticas avançadas após simulação.
        
        Usa os dados calculados no MonteCarloEngine para garantir consistência
        entre tabelas de estatísticas e cenários reproduzíveis.
        """
        if not hasattr(result, 'yearly_projection') or not result.yearly_projection:
            return
        
        try:
            final_year = result.yearly_projection[-1]
            
            # Obter parâmetros da simulação
            meta = self._parse_value(self.input_meta.text()) or 100000
            capital = self._parse_value(self.input_capital.get_base_value()) or 10000
            aporte = self._parse_value(self.input_aporte.get_base_value()) or 0
            periodo = int(self._parse_value(self.input_periodo.text()) or 10)
            
            # =====================================================================
            # 1. USAR PERCENTILE_STATS CALCULADO NO ENGINE (fonte única de verdade)
            # =====================================================================
            
            if result.has_monte_carlo and result.percentile_stats is not None:
                # Usar estatísticas já calculadas no MonteCarloEngine
                self.percentile_stats = result.percentile_stats
                
                # Usar saldos finais reais para métricas de risco
                simulated_balances = result.sampled_final_balances
            else:
                # Fallback para modo determinístico: criar PercentileStats simples
                final_balance = final_year.balance_deterministic
                self.percentile_stats = PercentileStats(
                    p5=final_balance,
                    p10=final_balance,
                    p25=final_balance,
                    p50=final_balance,
                    p75=final_balance,
                    p90=final_balance,
                    p95=final_balance,
                    mean=final_balance,
                    mode=final_balance,
                    std_dev=0.0,
                    variance=0.0,
                    min_value=final_balance,
                    max_value=final_balance,
                    coef_variation=0.0
                )
                # Array com único valor para cálculos de risco
                simulated_balances = np.array([final_balance])
            
            # Atualizar painel de estatísticas
            self.percentile_stats_panel.update_stats(
                self.percentile_stats, 
                final_year.balance_deterministic
            )
            
            # =====================================================================
            # 2. MÉTRICAS DE RISCO (usando função centralizada)
            # =====================================================================
            
            # Obter taxa livre de risco (CDI) automaticamente
            risk_free_rate = get_risk_free_rate(
                fallback_rate=0.10,
                on_manual_input_needed=self._ask_cdi_rate_manual
            )
            
            # Obter aportes extras do resultado (se disponível)
            total_extra_deposits = result.params_used.get('total_extra_deposits', 0.0)
            
            self.risk_metrics = calculate_risk_metrics(
                final_balances=simulated_balances,
                meta=meta,
                capital_inicial=capital,
                aporte_mensal=aporte,
                periodo_anos=periodo,
                risk_free_rate=risk_free_rate,
                total_extra_deposits=total_extra_deposits
            )
            
            # Atualizar cards de risco na aba Análise de Risco
            self._update_risk_cards(self.risk_metrics)
            
            # =====================================================================
            # 3. CENÁRIOS REPRESENTATIVOS (Parâmetros REAIS do Monte Carlo)
            # =====================================================================
            
            # Usar cenários representativos diretamente do resultado Monte Carlo
            # (garantia de consistência: usam os mesmos percentis)
            if result.has_monte_carlo and result.representative_scenarios:
                self._populate_cenarios_table(result.representative_scenarios)
            else:
                # Fallback: calcular implícitos para modo determinístico
                self.implicit_params = self._calculate_implicit_parameters(
                    self.percentile_stats, capital, aporte, periodo
                )
                # Converter para formato compatível (criar RepresentativeScenario fake)
                fake_scenarios = []
                for p in self.implicit_params:
                    fake_scenarios.append(RepresentativeScenario(
                        scenario_name=p.scenario_name,
                        percentile=p.percentile,
                        capital_inicial=p.capital_inicial,
                        aporte_mensal=p.aporte_mensal,
                        rentabilidade_anual=p.rentabilidade_anual,
                        saldo_final=p.saldo_final,
                        scenario_type=p.scenario_type
                    ))
                self._populate_cenarios_table(fake_scenarios)
            
            # =====================================================================
            # 4. GRÁFICOS
            # =====================================================================
            
            # Gráfico de distribuição (histograma)
            if result.has_monte_carlo and len(simulated_balances) > 1:
                self.distribution_chart.update_chart(
                    list(simulated_balances),
                    self.percentile_stats,
                    meta,
                    final_year.balance_deterministic,
                    simulation_method=result.simulation_method  # CORREÇÃO: passar método
                )
            else:
                # Modo determinístico: mostrar mensagem informativa
                self.distribution_chart._show_deterministic_message(
                    final_year.balance_deterministic
                )
            
            # (Gráfico Expert removido - interface simplificada para 3 abas)
            
            # =====================================================================
            # 5. ATUALIZAR SENSIBILIDADE PRINCIPAL
            # =====================================================================
            params = result.params_used
            
            # Atualizar dashboard de sensibilidade principal (na seção de resultados)
            if hasattr(self, 'sensitivity_dashboard'):
                self.sensitivity_dashboard.update_sensitivities(
                    initial_amount=params['capital_inicial'],
                    monthly_contribution=params['aporte_mensal'],
                    annual_rate=params['rentabilidade_anual'],
                    years=params['periodo_anos']
                )
            
            self.status_bar.showMessage(
                f"📊 Estatísticas calculadas | Prob. Sucesso: {self.risk_metrics.prob_success:.1f}% | "
                f"VaR 95%: {format_currency(self.risk_metrics.var_95)}"
            )
            
        except Exception as e:
            import traceback
            print(f"Erro ao calcular estatísticas avançadas: {e}")
            traceback.print_exc()
            self.status_bar.showMessage(f"⚠️ Erro nas estatísticas: {str(e)[:50]}")
    
    def _calculate_implicit_parameters(
        self, 
        stats: PercentileStats, 
        capital: float, 
        aporte: float, 
        periodo: int
    ) -> List[ImplicitParameters]:
        """
        Calcula taxa de rentabilidade implícita para cada percentil via busca binária.
        
        Fórmula do Montante:
        M = C(1+i)^t + a * ((1+i)^t - 1) / i
        
        Onde:
        - M = Montante final (percentil)
        - C = Capital inicial
        - a = Aporte mensal
        - i = Taxa mensal
        - t = Tempo em meses
        """
        scenarios = [
            ("P5 (Pessimista)", "P5", stats.p5, "Worst Case"),
            ("P25 (Conservador)", "P25", stats.p25, "Conservador"),
            ("P50 (Mediana)", "P50", stats.p50, "Típico"),
            ("P75 (Bom)", "P75", stats.p75, "Otimista"),
            ("P95 (Otimista)", "P95", stats.p95, "Best Case"),
            ("Média", "MÉDIA", stats.mean, "Valor Esperado"),
        ]
        
        results = []
        
        for name, percentile, target_balance, scenario_type in scenarios:
            if target_balance <= 0:
                continue
                
            rate = self._find_rate_binary_search(
                target_balance, capital, aporte, periodo
            )
            
            if rate is not None:
                results.append(ImplicitParameters(
                    scenario_name=name,
                    percentile=percentile,
                    capital_inicial=capital,
                    aporte_mensal=aporte,
                    rentabilidade_anual=rate,
                    saldo_final=target_balance,
                    scenario_type=scenario_type
                ))
        
        return results
    
    def _find_rate_binary_search(
        self,
        target_balance: float,
        capital: float,
        aporte: float,
        periodo_anos: int,
        tolerance: float = 100.0,
        max_iterations: int = 100
    ) -> Optional[float]:
        """
        Encontra a taxa de rentabilidade anual que reproduz o saldo alvo.
        
        Usa busca binária na fórmula:
        M = C(1+i)^t + a * ((1+i)^t - 1) / i
        """
        r_min, r_max = -30.0, 100.0  # -30% a +100% ao ano
        meses = periodo_anos * 12
        
        def simulate(rate_annual: float) -> float:
            """Simula cenário determinístico com taxa anual."""
            if abs(rate_annual) < 0.001:
                # Taxa zero: apenas soma
                return capital + aporte * meses
            
            # Converter taxa anual para mensal
            rate_monthly = (1 + rate_annual / 100) ** (1/12) - 1
            
            # Fórmula do montante com aportes
            factor = (1 + rate_monthly) ** meses
            
            if abs(rate_monthly) < 1e-10:
                return capital * factor + aporte * meses
            
            return capital * factor + aporte * (factor - 1) / rate_monthly
        
        for _ in range(max_iterations):
            r_mid = (r_min + r_max) / 2
            simulated = simulate(r_mid)
            
            if abs(simulated - target_balance) < tolerance:
                return round(r_mid, 2)
            
            if simulated < target_balance:
                r_min = r_mid
            else:
                r_max = r_mid
        
        # Retorna melhor aproximação
        return round((r_min + r_max) / 2, 2)
    
    def _ask_cdi_rate_manual(self) -> Optional[float]:
        """
        Solicita ao usuário a taxa CDI manualmente via diálogo.
        
        Chamado como fallback quando a busca automática da B3 falha.
        
        Returns:
            Taxa CDI como decimal (ex: 0.1175 para 11.75%) ou None se cancelado.
        """
        from PySide6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(
            self,
            "Taxa CDI",
            "Não foi possível obter a taxa CDI automaticamente.\n\n"
            "Digite a taxa CDI anual atual (%):\n"
            "(Ex: 11.75 para 11,75% a.a.)",
            text="11.75"
        )
        
        if ok and text:
            try:
                # Aceitar vírgula ou ponto como separador decimal
                text = text.replace(",", ".").strip()
                taxa_percentual = float(text)
                
                # Validar range razoável (0% a 50%)
                if 0 <= taxa_percentual <= 50:
                    self.status_bar.showMessage(
                        f"📊 Taxa CDI definida manualmente: {taxa_percentual:.2f}% a.a."
                    )
                    return taxa_percentual / 100.0
                else:
                    QMessageBox.warning(
                        self, 
                        "Valor Inválido", 
                        "A taxa deve estar entre 0% e 50%.\nUsando valor padrão de 10%."
                    )
            except ValueError:
                QMessageBox.warning(
                    self, 
                    "Formato Inválido", 
                    "Digite um número válido.\nUsando valor padrão de 10%."
                )
        
        return None
    
    def _update_risk_cards(self, metrics: RiskMetrics):
        """Atualiza os cards de métricas de risco na aba Análise de Risco."""
        if not hasattr(self, 'risk_cards'):
            return
        
        # Formatação brasileira
        def fmt_currency(value):
            return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        def fmt_percent(value):
            return f"{value:.1f}%".replace(".", ",")
        
        # Atualizar cada card (8 cartões)
        self.risk_cards['success'].setText(fmt_percent(metrics.prob_success))
        self.risk_cards['ruin'].setText(fmt_percent(metrics.prob_ruin))
        self.risk_cards['var'].setText(fmt_currency(metrics.var_95))
        self.risk_cards['cvar'].setText(fmt_currency(metrics.cvar_95))
        self.risk_cards['volatility'].setText(fmt_currency(metrics.volatility))
        self.risk_cards['ratio'].setText(f"{metrics.risk_return_ratio:.2f}".replace(".", ","))
        self.risk_cards['sharpe'].setText(f"{metrics.sharpe_ratio:.2f}".replace(".", ","))
        
        # Atualizar card do CDI com a taxa atual
        cdi_info = get_cdi_info()
        self.risk_cards['cdi'].setText(f"{cdi_info['rate_percent']:.2f}%".replace(".", ","))
        
        # Atualizar resumo
        if hasattr(self, 'risk_summary_label'):
            # =========================================================
            # CORREÇÃO: Usar total_invested do resultado (já calculado)
            # Em vez de recalcular com valores base dos inputs
            # =========================================================
            capital_total = 0.0
            if hasattr(self, 'current_result') and self.current_result:
                capital_total = self.current_result.total_invested
            
            ganho = self.percentile_stats.mean - capital_total if self.percentile_stats else 0
            
            # Obter informações do CDI
            cdi_info = get_cdi_info()
            
            summary_html = f"""
            <div style="line-height: 1.8;">
                • <b>Probabilidade de Sucesso:</b> {fmt_percent(metrics.prob_success)} de chance de atingir a meta<br>
                • <b>Probabilidade de Ruína:</b> {fmt_percent(metrics.prob_ruin)} de risco de perder o capital investido<br>
                • <b>Value at Risk (VaR 95%):</b> Em 95% dos cenários, a perda máxima é de {fmt_currency(metrics.var_95)}<br>
                • <b>Capital Total Investido:</b> {fmt_currency(capital_total)} (inicial + aportes + extras)<br>
                • <b>Ganho Esperado:</b> {fmt_currency(ganho)} (Média - Capital Total)<br>
                • <b>Índice Sharpe:</b> {metrics.sharpe_ratio:.2f} (quanto maior, melhor o retorno ajustado ao risco)<br>
                <hr style="border-color: #E5E7EB;">
                <b>📈 Taxa Livre de Risco (CDI):</b><br>
                • <b>Taxa Anual:</b> {cdi_info['rate_percent']:.2f}% a.a.<br>
                • <b>Taxa Mensal:</b> {cdi_info['monthly_percent']:.4f}% a.m.<br>
                • <b>Origem:</b> {cdi_info['source_label']}
            </div>
            """
            self.risk_summary_label.setText(summary_html)
            self.risk_summary_label.setTextFormat(Qt.RichText)
    
    # =========================================================================
    # PERSISTÊNCIA DE PROJETO (.pyinv)
    # =========================================================================
    
    def _on_new_project(self):
        """Cria novo projeto."""
        reply = QMessageBox.question(
            self, "Novo Projeto",
            "Deseja criar um novo projeto?\nDados não salvos serão perdidos.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._on_reset()
            self.historical_returns.clear()
            self._update_historical_status()
            self.current_project_path = None
            self.setWindowTitle("PyInvest - Simulador de Investimentos")
            self.status_bar.showMessage("Novo projeto criado")
    
    def _on_open_project(self):
        """Abre projeto existente."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Abrir Projeto",
            "", "Projetos PyInvest (*.pyinv);;Todos (*)"
        )
        
        if not filepath:
            return
        
        project, error = load_project(filepath)
        
        if error:
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir:\n{error}")
            return
        
        self._load_project_data(project)
        self.current_project_path = filepath
        self.setWindowTitle(f"PyInvest - {project.name}")
        self.status_bar.showMessage(f"Projeto '{project.name}' carregado")
    
    def _on_save_project(self):
        """Salva projeto atual."""
        if self.current_project_path:
            self._save_to_path(self.current_project_path)
        else:
            self._on_save_project_as()
    
    def _on_save_project_as(self):
        """Salva projeto com novo nome."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Projeto",
            "meu_projeto.pyinv",
            "Projetos PyInvest (*.pyinv)"
        )
        
        if not filepath:
            return
        
        if not filepath.lower().endswith('.pyinv'):
            filepath += '.pyinv'
        
        self._save_to_path(filepath)
        self.current_project_path = filepath
    
    def _save_to_path(self, filepath: str):
        """Salva projeto no caminho especificado."""
        project = self._collect_project_data()
        
        success, error = save_project(filepath, project)
        
        if success:
            self.setWindowTitle(f"PyInvest - {project.name}")
            self.status_bar.showMessage(f"Projeto salvo: {filepath}")
        else:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar:\n{error}")
    
    def _collect_project_data(self) -> ProjectData:
        """Coleta dados atuais da UI para salvar."""
        from pathlib import Path
        
        name = "Projeto PyInvest"
        if self.current_project_path:
            name = Path(self.current_project_path).stem
        
        # Parâmetros
        capital = ParameterSet(
            min_value=self._parse_value(self.input_capital.get_min_value()) or None,
            base_value=self._parse_value(self.input_capital.get_base_value()),
            max_value=self._parse_value(self.input_capital.get_max_value()) or None
        )
        
        aporte = ParameterSet(
            min_value=self._parse_value(self.input_aporte.get_min_value()) or None,
            base_value=self._parse_value(self.input_aporte.get_base_value()),
            max_value=self._parse_value(self.input_aporte.get_max_value()) or None
        )
        
        rentabilidade = ParameterSet(
            min_value=self._parse_value(self.input_rentabilidade.get_min_value()) or None,
            base_value=self._parse_value(self.input_rentabilidade.get_base_value()),
            max_value=self._parse_value(self.input_rentabilidade.get_max_value()) or None
        )
        
        # Data de início
        qdate = self.input_start_date.date()
        start_date = f"{qdate.year()}-{qdate.month():02d}-{qdate.day():02d}"
        
        # Configuração Monte Carlo
        methods = ["bootstrap", "normal", "t_student"]
        method = methods[self.combo_method.currentIndex()] if hasattr(self, 'combo_method') else "bootstrap"
        
        mc_config = MonteCarloConfig(
            n_simulations=self.spin_simulations.value(),
            method=method,
            expert_mode=self.check_expert_mode.isChecked() if hasattr(self, 'check_expert_mode') else False
        )
        
        # Eventos
        events_data = []
        for event in self.events_manager.events:
            events_data.append(ExtraordinaryEventData(
                date_str=event.date.strftime('%Y-%m-%d'),
                month_simulation=0,  # Será calculado
                description=event.description,
                extra_deposit=event.deposit,
                withdrawal=event.withdrawal
            ))
        
        return ProjectData(
            name=name,
            capital_inicial=capital,
            aporte_mensal=aporte,
            rentabilidade_anual=rentabilidade,
            meta_final=self._parse_value(self.input_meta.text()),
            periodo_anos=int(self._parse_value(self.input_periodo.text()) or 10),
            start_date=start_date,
            historical_returns=self.historical_returns,
            monte_carlo_config=mc_config,
            extraordinary_events=events_data
        )
    
    def _load_project_data(self, project: ProjectData):
        """Carrega dados do projeto na UI."""
        # Parâmetros
        if project.capital_inicial.min_value:
            self.input_capital.set_min_value(project.capital_inicial.min_value)
        self.input_capital.set_base_value(project.capital_inicial.base_value)
        if project.capital_inicial.max_value:
            self.input_capital.set_max_value(project.capital_inicial.max_value)
        
        if project.aporte_mensal.min_value:
            self.input_aporte.set_min_value(project.aporte_mensal.min_value)
        self.input_aporte.set_base_value(project.aporte_mensal.base_value)
        if project.aporte_mensal.max_value:
            self.input_aporte.set_max_value(project.aporte_mensal.max_value)
        
        if project.rentabilidade_anual.min_value:
            self.input_rentabilidade.set_min_value(project.rentabilidade_anual.min_value)
        self.input_rentabilidade.set_base_value(project.rentabilidade_anual.base_value)
        if project.rentabilidade_anual.max_value:
            self.input_rentabilidade.set_max_value(project.rentabilidade_anual.max_value)
        
        self.input_meta.setText(str(project.meta_final) if project.meta_final else "")
        self.input_periodo.setText(str(project.periodo_anos))
        
        # Data de início
        if project.start_date:
            parts = project.start_date.split('-')
            if len(parts) == 3:
                self.input_start_date.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
        
        # Configuração Monte Carlo
        self.spin_simulations.setValue(project.monte_carlo_config.n_simulations)
        
        if hasattr(self, 'check_expert_mode'):
            self.check_expert_mode.setChecked(project.monte_carlo_config.expert_mode)
        
        methods = ["bootstrap", "normal", "t_student"]
        if hasattr(self, 'combo_method') and project.monte_carlo_config.method in methods:
            self.combo_method.setCurrentIndex(methods.index(project.monte_carlo_config.method))
        
        # Dados históricos
        self.historical_returns = project.historical_returns
        self._update_historical_status()
        
        # Eventos (simplificado - idealmente converter de volta)
        self.events_manager = EventsManager()
        for ev in project.extraordinary_events:
            try:
                parts = ev.date_str.split('-')
                ev_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
                self.events_manager.add_event(ExtraordinaryEvent(
                    date=ev_date,
                    description=ev.description,
                    deposit=ev.extra_deposit,
                    withdrawal=ev.withdrawal
                ))
            except:
                pass
        
        self._update_events_status()
    
    def _on_export_scenarios(self):
        """Exporta tabela de cenários para CSV."""
        if not self.implicit_params:
            QMessageBox.warning(self, "Sem Dados", "Execute uma simulação primeiro.")
            return
        
        from core.statistics import export_percentiles_csv
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exportar Cenários",
            "cenarios_investimento.csv",
            "Arquivos CSV (*.csv)"
        )
        
        if not filepath:
            return
        
        success, error = export_percentiles_csv(filepath, self.implicit_params)
        
        if success:
            QMessageBox.information(self, "Sucesso", f"Cenários exportados:\n{filepath}")
        else:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar:\n{error}")
    
    def _on_update_cdi_rate(self):
        """Atualiza a taxa CDI da B3 ou solicita input manual."""
        from PySide6.QtWidgets import QInputDialog
        
        # Perguntar se quer buscar automaticamente ou digitar
        options = ["🌐 Buscar da B3 (Internet)", "✏️ Digitar manualmente"]
        choice, ok = QInputDialog.getItem(
            self,
            "Atualizar Taxa CDI",
            "Como deseja atualizar a taxa CDI?",
            options,
            0,  # índice padrão
            False  # não editável
        )
        
        if not ok:
            return
        
        if choice == options[0]:
            # Buscar da B3 (via API do BCB)
            clear_cdi_cache()  # Limpar cache para forçar nova busca
            rate = get_risk_free_rate(force_refresh=True, fallback_rate=0.10)
            
            if rate:
                QMessageBox.information(
                    self,
                    "Taxa CDI Atualizada",
                    f"Taxa CDI obtida da B3:\n\n"
                    f"<b>{rate * 100:.2f}% a.a.</b>\n\n"
                    f"Esta taxa será usada nos cálculos do Índice de Sharpe."
                )
                self.status_bar.showMessage(f"📈 Taxa CDI atualizada: {rate * 100:.2f}% a.a.")
        else:
            # Digitar manualmente
            manual_rate = self._ask_cdi_rate_manual()
            if manual_rate:
                QMessageBox.information(
                    self,
                    "Taxa CDI Definida",
                    f"Taxa CDI definida manualmente:\n\n"
                    f"<b>{manual_rate * 100:.2f}% a.a.</b>"
                )
    
    def _on_about(self):
        """Exibe diálogo Sobre."""
        QMessageBox.about(
            self, "Sobre PyInvest",
            """<h2>PyInvest v4.1</h2>
            <p><b>Simulador de Investimentos com Monte Carlo</b></p>
            <p>Desenvolvido com PySide6 + Plotly</p>
            <hr>
            <p><b>Funcionalidades:</b></p>
            <ul>
                <li>Simulação Monte Carlo (até 50.000 cenários)</li>
                <li>Análise probabilística (P5/P50/P95)</li>
                <li>Métricas de risco (VaR, Sharpe, etc.)</li>
                <li>Eventos extraordinários</li>
                <li>Persistência de projetos (.pyinv)</li>
            </ul>
            <p><i>© 2025 - Licença MIT</i></p>
            """
        )


# Importar ExtraordinaryEventData no escopo correto
from core.statistics import ExtraordinaryEventData
