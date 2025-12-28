"""
PyInvest - Wizard de Dados Mensais para Bootstrap

Interface de 4 passos para:
1. Seleção do tipo de dados (Mensal vs Anual)
2. Entrada/Importação de dados mensais
3. Configuração do Bootstrap (Simples ou Block)
4. Geração de cenários e resultados

Autor: PyInvest Team
Versão: 6.0
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QFileDialog, QLineEdit, QSpinBox,
    QDoubleSpinBox, QWidget, QSizePolicy, QAbstractItemView,
    QStackedWidget, QRadioButton, QButtonGroup, QGroupBox,
    QProgressBar, QTextEdit, QComboBox, QScrollArea,
    QGridLayout, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWebEngineWidgets import QWebEngineView

import numpy as np
from typing import List, Optional, Dict, Any
import json

from core.bootstrap import (
    MonthlyReturnData,
    SyntheticScenariosResult,
    BootstrapEngine,
    BootstrapMethod,
    SyntheticDataConfig,
    generate_monthly_template_csv,
    parse_monthly_csv,
    export_scenarios_csv,
    import_scenarios_csv,
    estimate_generation_time,
    format_time_estimate
)

MONTHS_PT = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
             'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

STYLE_SHEET = """
QDialog { background-color: #F3F4F6; }
QLabel#title { font-size: 20px; font-weight: bold; color: #1F2937; }
QLabel#step_indicator { font-size: 12px; color: #9CA3AF; font-weight: 500; }
QLabel#section_title { font-size: 14px; font-weight: 600; color: #374151; }
QPushButton { padding: 10px 20px; border-radius: 8px; font-weight: 500; font-size: 13px; }
QPushButton#btn_primary { background-color: #10B981; color: white; border: none; }
QPushButton#btn_primary:hover { background-color: #059669; }
QPushButton#btn_primary:disabled { background-color: #9CA3AF; }
QPushButton#btn_secondary { background-color: white; color: #374151; border: 1px solid #D1D5DB; }
QPushButton#btn_secondary:hover { background-color: #F9FAFB; }
QPushButton#btn_nav { background-color: #3B82F6; color: white; border: none; }
QPushButton#btn_nav:hover { background-color: #2563EB; }
QPushButton#btn_nav:disabled { background-color: #9CA3AF; }
QPushButton#btn_generate { background-color: #8B5CF6; color: white; border: none; font-size: 14px; padding: 12px 24px; }
QPushButton#btn_generate:hover { background-color: #7C3AED; }
QPushButton#btn_generate:disabled { background-color: #9CA3AF; }
QFrame#card { background-color: white; border: 1px solid #E5E7EB; border-radius: 12px; }
QFrame#card_info { background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; }
QProgressBar { border: none; border-radius: 8px; background-color: #E5E7EB; text-align: center; }
QProgressBar::chunk { background-color: #8B5CF6; border-radius: 8px; }
QComboBox, QSpinBox, QDoubleSpinBox { padding: 8px 12px; border: 1px solid #D1D5DB; border-radius: 6px; background-color: white; }
QTabWidget::pane { border: 1px solid #E5E7EB; border-radius: 8px; background-color: white; }
QTabBar::tab { background-color: #F3F4F6; color: #6B7280; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background-color: white; color: #1F2937; font-weight: 600; }
"""


class BootstrapGeneratorThread(QThread):
    """Thread para gerar cenários sem travar a UI."""
    progress = Signal(int)
    finished_signal = Signal(object)
    error = Signal(str)
    
    def __init__(self, engine, method, n_scenarios, block_size=None, seed=None):
        super().__init__()
        self.engine = engine
        self.method = method
        self.n_scenarios = n_scenarios
        self.block_size = block_size
        self.seed = seed
    
    def run(self):
        try:
            result = self.engine.generate(
                method=self.method,
                n_scenarios=self.n_scenarios,
                block_size=self.block_size,
                seed=self.seed,
                progress_callback=lambda p: self.progress.emit(p)
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MonthlyDataWizard(QDialog):
    """Wizard de 4 passos para entrada de dados mensais e geração de cenários."""
    
    scenarios_confirmed = Signal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monthly_data = None
        self.engine = None
        self.result = None
        self.generator_thread = None
        self.monthly_values = {}
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("🗓️ Wizard - Dados Mensais para Bootstrap")
        self.setMinimumSize(1000, 700)
        self.setModal(True)
        self.setStyleSheet(STYLE_SHEET)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._create_header(layout)
        
        self.stacked = QStackedWidget()
        self._create_page1_data_type()
        self._create_page2_data_entry()
        self._create_page3_bootstrap_config()
        self._create_page4_generation()
        layout.addWidget(self.stacked, stretch=1)
        
        self._create_footer(layout)
        self._go_to_page(0)
    
    def _create_header(self, parent_layout):
        header = QFrame()
        header.setStyleSheet("QFrame { background-color: white; border-bottom: 1px solid #E5E7EB; }")
        header.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 16, 24, 16)
        
        title_layout = QVBoxLayout()
        self.header_title = QLabel("Wizard - Dados Mensais")
        self.header_title.setObjectName("title")
        title_layout.addWidget(self.header_title)
        
        self.header_subtitle = QLabel("Passo 1 de 4")
        self.header_subtitle.setObjectName("step_indicator")
        title_layout.addWidget(self.header_subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        self.step_indicators = []
        steps_layout = QHBoxLayout()
        steps_layout.setSpacing(8)
        
        for i, name in enumerate(["Tipo", "Dados", "Config", "Gerar"]):
            step_frame = QFrame()
            step_frame.setFixedSize(80, 40)
            step_layout = QVBoxLayout(step_frame)
            step_layout.setContentsMargins(0, 0, 0, 0)
            step_layout.setSpacing(2)
            
            num_label = QLabel(str(i + 1))
            num_label.setAlignment(Qt.AlignCenter)
            num_label.setFixedSize(24, 24)
            num_label.setStyleSheet("background-color: #E5E7EB; color: #6B7280; border-radius: 12px; font-weight: bold;")
            
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("font-size: 11px; color: #6B7280;")
            
            step_layout.addWidget(num_label, alignment=Qt.AlignCenter)
            step_layout.addWidget(name_label, alignment=Qt.AlignCenter)
            
            self.step_indicators.append((step_frame, num_label, name_label))
            steps_layout.addWidget(step_frame)
        
        header_layout.addLayout(steps_layout)
        parent_layout.addWidget(header)
    
    def _update_step_indicators(self, current_page):
        titles = ["Selecione o Tipo de Dados", "Preencha os Dados Mensais", "Configure o Bootstrap", "Gere os Cenários"]
        self.header_title.setText(titles[current_page])
        self.header_subtitle.setText(f"Passo {current_page + 1} de 4")
        
        for i, (frame, num_label, name_label) in enumerate(self.step_indicators):
            if i < current_page:
                num_label.setStyleSheet("background-color: #10B981; color: white; border-radius: 12px; font-weight: bold;")
                num_label.setText("✓")
            elif i == current_page:
                num_label.setStyleSheet("background-color: #3B82F6; color: white; border-radius: 12px; font-weight: bold;")
                num_label.setText(str(i + 1))
                name_label.setStyleSheet("font-size: 11px; color: #3B82F6; font-weight: bold;")
            else:
                num_label.setStyleSheet("background-color: #E5E7EB; color: #6B7280; border-radius: 12px; font-weight: bold;")
                num_label.setText(str(i + 1))
                name_label.setStyleSheet("font-size: 11px; color: #6B7280;")

    def _create_option_card(self, title, description, recommended=False):
        card = QFrame()
        card.setObjectName("card")
        card.setCursor(Qt.PointingHandCursor)
        card.setMinimumHeight(280)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        if recommended:
            badge = QLabel("⭐ RECOMENDADO")
            badge.setStyleSheet("background-color: #FEF3C7; color: #92400E; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: bold;")
            badge.setFixedWidth(120)
            layout.addWidget(badge)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F2937;")
        layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #6B7280; line-height: 1.5;")
        layout.addWidget(desc_label)
        layout.addStretch()
        
        return card

    def _create_page1_data_type(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(48, 32, 48, 32)
        layout.setSpacing(24)
        
        title = QLabel("Qual tipo de dado você deseja informar?")
        title.setObjectName("section_title")
        title.setStyleSheet("font-size: 16px;")
        layout.addWidget(title)
        
        options_layout = QHBoxLayout()
        options_layout.setSpacing(24)
        
        self.card_monthly = self._create_option_card(
            title="📅 Retornos Mensais Históricos",
            description="Informe os retornos mês a mês (108 meses)\n\n• Mais dados = Melhor precisão\n• Até 100.000 cenários anuais\n• Captura eventos extremos\n• Ideal para análises detalhadas",
            recommended=True
        )
        self.card_monthly.mousePressEvent = lambda e: self._select_data_type('monthly')
        options_layout.addWidget(self.card_monthly)
        
        self.card_annual = self._create_option_card(
            title="📊 Retornos Anuais Históricos",
            description="Informe os retornos ano a ano (9 anos)\n\n• Entrada mais simples\n• Usa diálogo existente\n• Menos dados disponíveis\n• Ideal para análises rápidas",
            recommended=False
        )
        self.card_annual.mousePressEvent = lambda e: self._select_data_type('annual')
        options_layout.addWidget(self.card_annual)
        
        layout.addLayout(options_layout)
        
        self.radio_monthly = QRadioButton()
        self.radio_annual = QRadioButton()
        self.data_type_group = QButtonGroup()
        self.data_type_group.addButton(self.radio_monthly, 0)
        self.data_type_group.addButton(self.radio_annual, 1)
        self.radio_monthly.setChecked(True)
        self.radio_monthly.hide()
        self.radio_annual.hide()
        
        layout.addStretch()
        
        info_frame = QFrame()
        info_frame.setObjectName("card_info")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 12, 16, 12)
        
        info_icon = QLabel("💡")
        info_icon.setStyleSheet("font-size: 20px;")
        info_layout.addWidget(info_icon)
        
        info_text = QLabel("<b>Dica:</b> Com dados mensais, você pode gerar milhares de cenários via Bootstrap, melhorando a confiança estatística das simulações.")
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #1E40AF;")
        info_layout.addWidget(info_text, stretch=1)
        
        layout.addWidget(info_frame)
        self.stacked.addWidget(page)
        self._select_data_type('monthly')

    def _select_data_type(self, data_type):
        if data_type == 'monthly':
            self.radio_monthly.setChecked(True)
            self.card_monthly.setStyleSheet("QFrame#card { background-color: white; border: 2px solid #3B82F6; border-radius: 12px; }")
            self.card_annual.setStyleSheet("QFrame#card { background-color: white; border: 1px solid #E5E7EB; border-radius: 12px; }")
        else:
            self.radio_annual.setChecked(True)
            self.card_annual.setStyleSheet("QFrame#card { background-color: white; border: 2px solid #3B82F6; border-radius: 12px; }")
            self.card_monthly.setStyleSheet("QFrame#card { background-color: white; border: 1px solid #E5E7EB; border-radius: 12px; }")

    def _create_page2_data_entry(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)
        
        toolbar = QHBoxLayout()
        
        btn_export_template = QPushButton("📥 Exportar Modelo CSV")
        btn_export_template.setObjectName("btn_secondary")
        btn_export_template.setCursor(Qt.PointingHandCursor)
        btn_export_template.clicked.connect(self._export_template)
        toolbar.addWidget(btn_export_template)
        
        btn_import = QPushButton("📤 Importar CSV")
        btn_import.setObjectName("btn_secondary")
        btn_import.setCursor(Qt.PointingHandCursor)
        btn_import.clicked.connect(self._import_monthly_csv)
        toolbar.addWidget(btn_import)
        
        btn_example = QPushButton("📋 Carregar Exemplo")
        btn_example.setObjectName("btn_secondary")
        btn_example.setCursor(Qt.PointingHandCursor)
        btn_example.clicked.connect(self._load_example_data)
        toolbar.addWidget(btn_example)
        
        toolbar.addStretch()
        
        self.data_status_label = QLabel("0/108 meses preenchidos")
        self.data_status_label.setStyleSheet("color: #6B7280; font-weight: 500;")
        toolbar.addWidget(self.data_status_label)
        
        layout.addLayout(toolbar)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        
        self.year_tables = {}
        self.month_inputs = {}
        
        for year in range(2017, 2026):
            year_frame = self._create_year_section(year)
            scroll_layout.addWidget(year_frame)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)
        
        self.stacked.addWidget(page)

    def _create_year_section(self, year):
        frame = QFrame()
        frame.setObjectName("card")
        frame.setStyleSheet("QFrame#card { background-color: white; border: 1px solid #E5E7EB; border-radius: 8px; }")
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        header = QHBoxLayout()
        year_label = QLabel(f"📅 {year}")
        year_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1F2937;")
        header.addWidget(year_label)
        header.addStretch()
        
        year_status = QLabel("0/12 meses")
        year_status.setObjectName(f"status_{year}")
        year_status.setStyleSheet("color: #EF4444; font-size: 12px;")
        header.addWidget(year_status)
        layout.addLayout(header)
        
        grid = QGridLayout()
        grid.setSpacing(8)
        
        for i, month in enumerate(MONTHS_PT):
            row = i // 4
            col = i % 4
            
            month_widget = QWidget()
            month_layout = QHBoxLayout(month_widget)
            month_layout.setContentsMargins(0, 0, 0, 0)
            month_layout.setSpacing(4)
            
            month_label = QLabel(f"{month}:")
            month_label.setFixedWidth(35)
            month_label.setStyleSheet("color: #6B7280; font-size: 12px;")
            month_layout.addWidget(month_label)
            
            month_input = QDoubleSpinBox()
            month_input.setRange(-99.99, 999.99)
            month_input.setDecimals(2)
            month_input.setSuffix(" %")
            month_input.setSpecialValueText("")
            month_input.setValue(-99.99)
            month_input.setMinimumWidth(90)
            month_input.setStyleSheet("QDoubleSpinBox { padding: 4px 8px; border: 1px solid #D1D5DB; border-radius: 4px; }")
            
            period = f"{month}/{year}"
            month_input.setProperty("period", period)
            month_input.valueChanged.connect(lambda v, p=period: self._on_month_value_changed(p, v))
            
            self.month_inputs[period] = month_input
            month_layout.addWidget(month_input)
            grid.addWidget(month_widget, row, col)
        
        layout.addLayout(grid)
        self.year_tables[year] = (frame, year_status)
        return frame

    def _on_month_value_changed(self, period, value):
        if value <= -99:
            if period in self.monthly_values:
                del self.monthly_values[period]
        else:
            self.monthly_values[period] = value
        self._update_data_status()

    def _update_data_status(self):
        total_filled = len(self.monthly_values)
        self.data_status_label.setText(f"{total_filled}/108 meses preenchidos")
        
        if total_filled >= 108:
            self.data_status_label.setStyleSheet("color: #10B981; font-weight: 500;")
        elif total_filled >= 12:
            self.data_status_label.setStyleSheet("color: #F59E0B; font-weight: 500;")
        else:
            self.data_status_label.setStyleSheet("color: #EF4444; font-weight: 500;")
        
        for year in range(2017, 2026):
            filled_in_year = sum(1 for p in self.monthly_values if f"/{year}" in p)
            _, status_label = self.year_tables[year]
            status_label.setText(f"{filled_in_year}/12 meses")
            
            if filled_in_year == 12:
                status_label.setStyleSheet("color: #10B981; font-size: 12px; font-weight: bold;")
            elif filled_in_year > 0:
                status_label.setStyleSheet("color: #F59E0B; font-size: 12px;")
            else:
                status_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        
        self._update_navigation_buttons()

    def _export_template(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Template", "rendimentos_mensais_template.csv", "CSV (*.csv)")
        if not filepath:
            return
        try:
            template = generate_monthly_template_csv()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template)
            QMessageBox.information(self, "Sucesso", f"Template exportado para:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar: {str(e)}")

    def _import_monthly_csv(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Importar Dados Mensais", "", "CSV (*.csv);;Todos (*)")
        if not filepath:
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            data = parse_monthly_csv(content)
            self.monthly_values.clear()
            for period, ret in zip(data.periods, data.returns):
                self.monthly_values[period] = ret
                if period in self.month_inputs:
                    self.month_inputs[period].blockSignals(True)
                    self.month_inputs[period].setValue(ret)
                    self.month_inputs[period].blockSignals(False)
            self._update_data_status()
            QMessageBox.information(self, "Importação Concluída", f"{data.n_months} meses importados!\nPeríodo: {data.period_range}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar:\n{str(e)}")

    def _load_example_data(self):
        reply = QMessageBox.question(self, "Carregar Exemplo", "Isso substituirá os dados atuais.\n\nDeseja continuar?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        
        example_returns = {
            2017: [1.08, 0.86, 1.05, 0.79, 0.93, 0.81, 0.80, 0.80, 0.64, 0.64, 0.57, 0.54],
            2018: [0.58, 0.46, 0.53, 0.52, 0.52, 0.52, 0.54, 0.57, 0.47, 0.54, 0.49, 0.49],
            2019: [0.54, 0.49, 0.47, 0.52, 0.54, 0.47, 0.57, 0.50, 0.46, 0.48, 0.38, 0.37],
            2020: [0.38, 0.29, 0.34, 0.28, 0.24, 0.21, 0.19, 0.16, 0.16, 0.16, 0.15, 0.16],
            2021: [0.15, 0.13, 0.20, 0.21, 0.27, 0.31, 0.36, 0.43, 0.44, 0.49, 0.59, 0.77],
            2022: [0.73, 0.76, 0.93, 0.83, 1.03, 1.02, 1.03, 1.17, 1.07, 1.02, 1.02, 1.12],
            2023: [1.12, 0.92, 1.17, 0.92, 1.12, 1.07, 1.07, 1.14, 0.97, 1.00, 0.92, 0.89],
            2024: [0.97, 0.80, 0.83, 0.89, 0.83, 0.79, 0.91, 0.87, 0.83, 0.93, 0.79, 0.93],
            2025: [1.00, 0.99, 1.06, 0.94, 1.01, 0.89, 0.95, 0.92, 0.88, 0.97, 0.91, 1.05]
        }
        
        self.monthly_values.clear()
        for year, returns in example_returns.items():
            for i, ret in enumerate(returns):
                period = f"{MONTHS_PT[i]}/{year}"
                self.monthly_values[period] = ret
                if period in self.month_inputs:
                    self.month_inputs[period].blockSignals(True)
                    self.month_inputs[period].setValue(ret)
                    self.month_inputs[period].blockSignals(False)
        
        self._update_data_status()
        QMessageBox.information(self, "Dados Carregados", "108 meses de dados de exemplo (CDI aproximado) foram carregados.")

    def _create_page3_bootstrap_config(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(48, 32, 48, 32)
        layout.setSpacing(24)
        
        title = QLabel("Configuração do Bootstrap")
        title.setObjectName("section_title")
        title.setStyleSheet("font-size: 16px;")
        layout.addWidget(title)
        
        columns = QHBoxLayout()
        columns.setSpacing(24)
        
        left_col = QVBoxLayout()
        left_col.setSpacing(16)
        
        self.card_simple = self._create_method_card("🎲 Bootstrap Histórico", "Sorteia 12 meses aleatórios com reposição.\n\n• Assume independência (I.I.D.)\n• Mais rápido\n• Ideal sem tendências", True, "simple")
        left_col.addWidget(self.card_simple)
        
        self.card_block = self._create_method_card("📊 Block Bootstrap", "Sorteia blocos de meses consecutivos.\n\n• Preserva autocorrelação\n• Captura clustering\n• Ideal com tendências", False, "block")
        left_col.addWidget(self.card_block)
        
        self.block_config_frame = QFrame()
        self.block_config_frame.setObjectName("card")
        self.block_config_frame.hide()
        
        block_layout = QVBoxLayout(self.block_config_frame)
        block_layout.setContentsMargins(16, 12, 16, 12)
        
        block_title = QLabel("Tamanho do Bloco")
        block_title.setStyleSheet("font-weight: bold;")
        block_layout.addWidget(block_title)
        
        self.block_size_combo = QComboBox()
        self.block_size_combo.addItems(["Automático", "1 mês", "2 meses", "3 meses", "4 meses", "5 meses", "6 meses"])
        block_layout.addWidget(self.block_size_combo)
        
        self.block_suggestion_label = QLabel("")
        self.block_suggestion_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        block_layout.addWidget(self.block_suggestion_label)
        
        left_col.addWidget(self.block_config_frame)
        left_col.addStretch()
        columns.addLayout(left_col)
        
        right_col = QVBoxLayout()
        right_col.setSpacing(16)
        
        diag_frame = QFrame()
        diag_frame.setObjectName("card")
        diag_layout = QVBoxLayout(diag_frame)
        diag_layout.setContentsMargins(16, 16, 16, 16)
        
        diag_title = QLabel("📈 Diagnóstico de Autocorrelação")
        diag_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        diag_layout.addWidget(diag_title)
        
        self.acf_chart = QWebEngineView()
        self.acf_chart.setMinimumHeight(200)
        diag_layout.addWidget(self.acf_chart)
        
        self.acf_diagnosis_text = QTextEdit()
        self.acf_diagnosis_text.setReadOnly(True)
        self.acf_diagnosis_text.setMaximumHeight(150)
        self.acf_diagnosis_text.setStyleSheet("QTextEdit { border: none; background-color: transparent; }")
        diag_layout.addWidget(self.acf_diagnosis_text)
        
        right_col.addWidget(diag_frame)
        right_col.addStretch()
        columns.addLayout(right_col)
        layout.addLayout(columns)
        
        self.radio_simple = QRadioButton()
        self.radio_block = QRadioButton()
        self.method_group = QButtonGroup()
        self.method_group.addButton(self.radio_simple, 0)
        self.method_group.addButton(self.radio_block, 1)
        self.radio_simple.setChecked(True)
        self.radio_simple.hide()
        self.radio_block.hide()
        
        self._select_method('simple')
        self.stacked.addWidget(page)

    def _create_method_card(self, title, description, recommended, method_id):
        card = QFrame()
        card.setObjectName("card")
        card.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(title_label)
        header.addStretch()
        
        if recommended:
            badge = QLabel("RECOMENDADO")
            badge.setStyleSheet("background-color: #ECFDF5; color: #065F46; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold;")
            header.addWidget(badge)
        layout.addLayout(header)
        
        desc = QLabel(description)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6B7280; font-size: 12px;")
        layout.addWidget(desc)
        
        card.mousePressEvent = lambda e, m=method_id: self._select_method(m)
        return card

    def _select_method(self, method):
        if method == 'simple':
            self.radio_simple.setChecked(True)
            self.card_simple.setStyleSheet("QFrame#card { background-color: white; border: 2px solid #10B981; border-radius: 12px; }")
            self.card_block.setStyleSheet("QFrame#card { background-color: white; border: 1px solid #E5E7EB; border-radius: 12px; }")
            self.block_config_frame.hide()
        else:
            self.radio_block.setChecked(True)
            self.card_block.setStyleSheet("QFrame#card { background-color: white; border: 2px solid #10B981; border-radius: 12px; }")
            self.card_simple.setStyleSheet("QFrame#card { background-color: white; border: 1px solid #E5E7EB; border-radius: 12px; }")
            self.block_config_frame.show()

    def _update_acf_diagnosis(self):
        if not self.engine:
            return
        try:
            diagnosis = self.engine.get_acf_diagnosis()
            acf = diagnosis['acf_values']
            ci = diagnosis['confidence_interval_95']
            
            html = f"""<!DOCTYPE html><html><head><script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script><style>body {{ margin: 0; }}</style></head><body>
            <div id="chart" style="width:100%;height:200px;"></div><script>
            var data = [{{x: [0,1,2,3,4,5,6], y: {acf[:7]}, type: 'bar', marker: {{color: '#3B82F6'}}, name: 'ACF'}}];
            var layout = {{margin: {{l: 40, r: 20, t: 20, b: 40}}, xaxis: {{title: 'Lag', dtick: 1}}, yaxis: {{title: 'ACF', range: [-1, 1]}}, shapes: [
                {{type: 'line', x0: -0.5, x1: 6.5, y0: {ci}, y1: {ci}, line: {{dash: 'dash', color: '#EF4444'}}}},
                {{type: 'line', x0: -0.5, x1: 6.5, y0: {-ci}, y1: {-ci}, line: {{dash: 'dash', color: '#EF4444'}}}}
            ], paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)'}};
            Plotly.newPlot('chart', data, layout, {{responsive: true}});</script></body></html>"""
            self.acf_chart.setHtml(html)
            
            acf_1 = diagnosis['acf_lag1']
            is_sig = diagnosis['is_significant']
            interpretation = diagnosis['interpretation']
            recommendation = diagnosis['recommendation']
            optimal_block = diagnosis['optimal_block_size']
            
            sig_text = "✅ Significativa" if is_sig else "❌ Não significativa"
            text = f"<b>ACF(1):</b> {acf_1:.4f} ({sig_text})<br><b>IC 95%:</b> ±{ci:.4f}<br><br><b>Interpretação:</b> {interpretation}<br><b>Recomendação:</b> {recommendation}"
            self.acf_diagnosis_text.setHtml(text)
            self.block_suggestion_label.setText(f"Sugestão automática: {optimal_block} meses")
        except Exception as e:
            self.acf_diagnosis_text.setHtml(f"<span style='color:red;'>Erro: {str(e)}</span>")

    def _create_page4_generation(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(48, 32, 48, 32)
        layout.setSpacing(24)
        
        config_frame = QFrame()
        config_frame.setObjectName("card")
        config_layout = QVBoxLayout(config_frame)
        config_layout.setContentsMargins(20, 20, 20, 20)
        
        config_title = QLabel("Número de Cenários a Gerar")
        config_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        config_layout.addWidget(config_title)
        
        scenarios_layout = QHBoxLayout()
        
        self.scenarios_spin = QSpinBox()
        self.scenarios_spin.setRange(1000, 100000)
        self.scenarios_spin.setSingleStep(1000)
        self.scenarios_spin.setValue(10000)
        self.scenarios_spin.setMinimumWidth(150)
        self.scenarios_spin.valueChanged.connect(self._update_time_estimate)
        scenarios_layout.addWidget(self.scenarios_spin)
        
        self.time_estimate_label = QLabel("Tempo estimado: ~5s")
        self.time_estimate_label.setStyleSheet("color: #6B7280;")
        scenarios_layout.addWidget(self.time_estimate_label)
        scenarios_layout.addStretch()
        
        self.btn_generate = QPushButton("🔄 Gerar Cenários")
        self.btn_generate.setObjectName("btn_generate")
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.clicked.connect(self._start_generation)
        scenarios_layout.addWidget(self.btn_generate)
        
        config_layout.addLayout(scenarios_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        config_layout.addWidget(self.progress_bar)
        
        layout.addWidget(config_frame)
        
        self.results_frame = QFrame()
        self.results_frame.setObjectName("card")
        self.results_frame.hide()
        
        results_layout = QVBoxLayout(self.results_frame)
        results_layout.setContentsMargins(20, 20, 20, 20)
        
        results_title = QLabel("✅ Cenários Gerados com Sucesso")
        results_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #059669;")
        results_layout.addWidget(results_title)
        
        tabs = QTabWidget()
        
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(16)
        stats_layout.addLayout(self.stats_grid)
        tabs.addTab(stats_tab, "📊 Estatísticas")
        
        dist_tab = QWidget()
        dist_layout = QVBoxLayout(dist_tab)
        self.dist_chart = QWebEngineView()
        self.dist_chart.setMinimumHeight(300)
        dist_layout.addWidget(self.dist_chart)
        tabs.addTab(dist_tab, "📈 Distribuição")
        
        results_layout.addWidget(tabs)
        
        actions_layout = QHBoxLayout()
        btn_export = QPushButton("📥 Exportar CSV")
        btn_export.setObjectName("btn_secondary")
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.clicked.connect(self._export_scenarios)
        actions_layout.addWidget(btn_export)
        
        btn_import = QPushButton("📤 Importar Cenários")
        btn_import.setObjectName("btn_secondary")
        btn_import.setCursor(Qt.PointingHandCursor)
        btn_import.clicked.connect(self._import_scenarios)
        actions_layout.addWidget(btn_import)
        actions_layout.addStretch()
        results_layout.addLayout(actions_layout)
        
        layout.addWidget(self.results_frame)
        layout.addStretch()
        self.stacked.addWidget(page)

    def _update_time_estimate(self):
        n = self.scenarios_spin.value()
        time_sec = estimate_generation_time(n)
        self.time_estimate_label.setText(f"Tempo estimado: {format_time_estimate(time_sec)}")

    def _start_generation(self):
        if not self.engine:
            QMessageBox.warning(self, "Erro", "Dados não carregados.")
            return
        
        method = BootstrapMethod.SIMPLE if self.radio_simple.isChecked() else BootstrapMethod.BLOCK
        block_size = None
        if method == BootstrapMethod.BLOCK:
            idx = self.block_size_combo.currentIndex()
            block_size = None if idx == 0 else idx
        
        n_scenarios = self.scenarios_spin.value()
        
        self.btn_generate.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.generator_thread = BootstrapGeneratorThread(self.engine, method, n_scenarios, block_size, 42)
        self.generator_thread.progress.connect(self._on_generation_progress)
        self.generator_thread.finished_signal.connect(self._on_generation_finished)
        self.generator_thread.error.connect(self._on_generation_error)
        self.generator_thread.start()

    def _on_generation_progress(self, percent):
        self.progress_bar.setValue(percent)

    def _on_generation_finished(self, result):
        self.result = result
        self.btn_generate.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._display_results()
        self.results_frame.show()
        self._update_navigation_buttons()

    def _on_generation_error(self, error_msg):
        self.btn_generate.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Erro", f"Erro na geração:\n{error_msg}")

    def _display_results(self):
        if not self.result:
            return
        r = self.result
        
        while self.stats_grid.count():
            item = self.stats_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        stats = [
            ("Cenários", f"{r.n_scenarios:,}", "#3B82F6"),
            ("Método", r.get_method_display_name(), "#8B5CF6"),
            ("Tempo", f"{r.generation_time:.2f}s", "#6B7280"),
            ("Média", f"{r.mean:.2f}%", "#10B981"),
            ("Desvio", f"{r.std:.2f}%", "#F59E0B"),
            ("Mediana", f"{r.median:.2f}%", "#3B82F6"),
            ("P5", f"{r.p5:.2f}%", "#EF4444"),
            ("P95", f"{r.p95:.2f}%", "#10B981"),
            ("Mínimo", f"{r.min_val:.2f}%", "#EF4444"),
            ("Máximo", f"{r.max_val:.2f}%", "#10B981"),
            ("Skewness", f"{r.skewness:.4f}", "#6B7280"),
            ("Curtose", f"{r.kurtosis:.4f}", "#6B7280"),
        ]
        
        for i, (label, value, color) in enumerate(stats):
            row, col = i // 4, i % 4
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background-color: {color}10; border: 1px solid {color}40; border-radius: 8px; }}")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)
            card_layout.setSpacing(4)
            
            label_w = QLabel(label)
            label_w.setStyleSheet(f"color: {color}; font-size: 11px;")
            card_layout.addWidget(label_w)
            
            value_w = QLabel(value)
            value_w.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold;")
            card_layout.addWidget(value_w)
            
            self.stats_grid.addWidget(card, row, col)
        
        returns = r.annual_returns.tolist()
        html = f"""<!DOCTYPE html><html><head><script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script><style>body {{ margin: 0; }}</style></head><body>
        <div id="chart" style="width:100%;height:300px;"></div><script>
        var data = [{{x: {returns}, type: 'histogram', nbinsx: 50, marker: {{color: '#8B5CF6', line: {{color: '#7C3AED', width: 1}}}}, hovertemplate: 'Retorno: %{{x:.2f}}%<br>Freq: %{{y}}<extra></extra>'}}];
        var layout = {{margin: {{l: 50, r: 20, t: 30, b: 50}}, xaxis: {{title: 'Retorno Anual (%)'}}, yaxis: {{title: 'Frequência'}}, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
            shapes: [{{type: 'line', x0: {r.p5}, x1: {r.p5}, y0: 0, y1: 1, yref: 'paper', line: {{color: '#EF4444', width: 2, dash: 'dash'}}}},
                     {{type: 'line', x0: {r.p95}, x1: {r.p95}, y0: 0, y1: 1, yref: 'paper', line: {{color: '#10B981', width: 2, dash: 'dash'}}}},
                     {{type: 'line', x0: {r.mean}, x1: {r.mean}, y0: 0, y1: 1, yref: 'paper', line: {{color: '#3B82F6', width: 2}}}}],
            annotations: [{{x: {r.p5}, y: 1, yref: 'paper', text: 'P5', showarrow: false, yanchor: 'bottom'}},
                          {{x: {r.p95}, y: 1, yref: 'paper', text: 'P95', showarrow: false, yanchor: 'bottom'}},
                          {{x: {r.mean}, y: 1, yref: 'paper', text: 'Média', showarrow: false, yanchor: 'bottom'}}]}};
        Plotly.newPlot('chart', data, layout, {{responsive: true}});</script></body></html>"""
        self.dist_chart.setHtml(html)

    def _export_scenarios(self):
        if not self.result:
            QMessageBox.warning(self, "Sem Dados", "Gere os cenários primeiro.")
            return
        filepath, _ = QFileDialog.getSaveFileName(self, "Exportar Cenários", f"cenarios_bootstrap_{self.result.n_scenarios}.csv", "CSV (*.csv)")
        if not filepath:
            return
        try:
            content = export_scenarios_csv(self.result, include_metadata=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Sucesso", f"Cenários exportados para:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar: {str(e)}")

    def _import_scenarios(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Importar Cenários", "", "CSV (*.csv);;Todos (*)")
        if not filepath:
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            returns, metadata = import_scenarios_csv(content)
            self.result = SyntheticScenariosResult(
                annual_returns=returns, n_scenarios=len(returns), method=metadata.get('Método', 'importado'),
                block_size=None, source_period=metadata.get('Período Fonte', 'N/A'),
                source_n_months=int(metadata.get('Meses Fonte', 0)) if metadata.get('Meses Fonte', '').isdigit() else 0,
                generation_time=0.0, seed=None)
            self._display_results()
            self.results_frame.show()
            self._update_navigation_buttons()
            QMessageBox.information(self, "Importação", f"{len(returns):,} cenários importados!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar:\n{str(e)}")

    def _create_footer(self, parent_layout):
        footer = QFrame()
        footer.setStyleSheet("QFrame { background-color: white; border-top: 1px solid #E5E7EB; }")
        footer.setFixedHeight(70)
        
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 16, 24, 16)
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("btn_secondary")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_cancel)
        
        footer_layout.addStretch()
        
        self.btn_prev = QPushButton("← Anterior")
        self.btn_prev.setObjectName("btn_secondary")
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.clicked.connect(self._go_prev)
        footer_layout.addWidget(self.btn_prev)
        
        self.btn_next = QPushButton("Próximo →")
        self.btn_next.setObjectName("btn_nav")
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.clicked.connect(self._go_next)
        footer_layout.addWidget(self.btn_next)
        
        self.btn_finish = QPushButton("✓ Usar Cenários")
        self.btn_finish.setObjectName("btn_primary")
        self.btn_finish.setCursor(Qt.PointingHandCursor)
        self.btn_finish.clicked.connect(self._finish)
        self.btn_finish.hide()
        footer_layout.addWidget(self.btn_finish)
        
        parent_layout.addWidget(footer)

    def _go_to_page(self, page):
        self.stacked.setCurrentIndex(page)
        self._update_step_indicators(page)
        self._update_navigation_buttons()
        
        if page == 2:
            self._prepare_bootstrap_data()
            if self.engine:
                self._update_acf_diagnosis()

    def _go_prev(self):
        current = self.stacked.currentIndex()
        if current > 0:
            self._go_to_page(current - 1)

    def _go_next(self):
        current = self.stacked.currentIndex()
        
        if current == 0:
            if self.radio_annual.isChecked():
                self.reject()
                return
        elif current == 1:
            if len(self.monthly_values) < 12:
                QMessageBox.warning(self, "Dados Insuficientes", "É necessário preencher pelo menos 12 meses.")
                return
        
        if current < 3:
            self._go_to_page(current + 1)

    def _update_navigation_buttons(self):
        current = self.stacked.currentIndex()
        self.btn_prev.setVisible(current > 0)
        
        if current == 3:
            self.btn_next.hide()
            self.btn_finish.setVisible(self.result is not None)
        else:
            self.btn_next.show()
            self.btn_finish.hide()
            self.btn_next.setEnabled(current != 1 or len(self.monthly_values) >= 12)

    def _prepare_bootstrap_data(self):
        if len(self.monthly_values) < 12:
            return
        try:
            def period_sort_key(p):
                month, year = p.split('/')
                return int(year) * 12 + MONTHS_PT.index(month)
            
            sorted_periods = sorted(self.monthly_values.keys(), key=period_sort_key)
            returns = np.array([self.monthly_values[p] for p in sorted_periods])
            
            self.monthly_data = MonthlyReturnData(periods=sorted_periods, returns=returns)
            self.engine = BootstrapEngine(self.monthly_data)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao preparar dados:\n{str(e)}")

    def _finish(self):
        if self.result:
            self.scenarios_confirmed.emit(self.result)
        self.accept()

    def get_result(self):
        return self.result

    def get_synthetic_config(self):
        if self.result:
            return SyntheticDataConfig.from_result(self.result)
        return None
