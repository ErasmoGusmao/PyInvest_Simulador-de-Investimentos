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
    use_annual_data = Signal()  # Emitido quando usuário escolhe dados anuais
    
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
        
        # Inicializar tabela com 12 linhas vazias (após footer estar criado)
        self._add_multiple_rows(12)
        
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
            badge.setFixedWidth(140)  # Aumentado para caber o texto completo
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
        
        # Card de Importação Rápida (atalho para Etapa 4)
        self.card_import = self._create_option_card(
            title="📥 Importar Cenários",
            description="Carregue cenários previamente gerados\n\n• Pule diretamente para análise\n• Formato CSV suportado\n• Reutilize simulações anteriores\n• Ideal para comparações",
            recommended=False
        )
        self.card_import.mousePressEvent = lambda e: self._import_and_skip_to_results()
        options_layout.addWidget(self.card_import)
        
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
        layout.setSpacing(12)
        
        # Toolbar superior simplificada - apenas Adicionar Linha e Remover
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        
        btn_add_row = QPushButton("➕ Adicionar Linha")
        btn_add_row.setObjectName("btn_primary")
        btn_add_row.setCursor(Qt.PointingHandCursor)
        btn_add_row.clicked.connect(self._add_row)
        toolbar.addWidget(btn_add_row)
        
        btn_remove_row = QPushButton("➖ Remover Última")
        btn_remove_row.setObjectName("btn_secondary")
        btn_remove_row.setCursor(Qt.PointingHandCursor)
        btn_remove_row.clicked.connect(self._remove_last_row)
        toolbar.addWidget(btn_remove_row)
        
        toolbar.addStretch()
        
        self.data_status_label = QLabel("0 meses preenchidos (mínimo: 12)")
        self.data_status_label.setStyleSheet("color: #6B7280; font-weight: 500;")
        toolbar.addWidget(self.data_status_label)
        
        layout.addLayout(toolbar)
        
        # Área principal: Tabela + Gráfico/Estatísticas lado a lado
        splitter = QSplitter(Qt.Horizontal)
        
        # === LADO ESQUERDO: Tabela ===
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(['Nº do Mês', 'Retorno (%)', 'Obs.'])
        
        # Configurar colunas - reduzir Observação
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.data_table.setColumnWidth(0, 80)
        self.data_table.setColumnWidth(1, 100)
        
        # Estilo da tabela
        self.data_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                gridline-color: #F3F4F6;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #F9FAFB;
                color: #374151;
                font-weight: 600;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #E5E7EB;
            }
        """)
        
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.cellChanged.connect(self._on_cell_changed)
        
        table_layout.addWidget(self.data_table)
        splitter.addWidget(table_widget)
        
        # === LADO DIREITO: Gráfico + Estatísticas ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(12)
        
        # Gráfico de evolução
        chart_frame = QFrame()
        chart_frame.setObjectName("card")
        chart_frame.setStyleSheet("QFrame#card { background-color: white; border: 1px solid #E5E7EB; border-radius: 8px; }")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(12, 12, 12, 12)
        
        chart_title = QLabel("📈 Evolução dos Retornos")
        chart_title.setStyleSheet("font-weight: bold; color: #1F2937;")
        chart_layout.addWidget(chart_title)
        
        self.monthly_chart = QWebEngineView()
        self.monthly_chart.setMinimumHeight(200)
        chart_layout.addWidget(self.monthly_chart)
        
        right_layout.addWidget(chart_frame, stretch=2)
        
        # Estatísticas
        stats_frame = QFrame()
        stats_frame.setObjectName("card")
        stats_frame.setStyleSheet("QFrame#card { background-color: white; border: 1px solid #E5E7EB; border-radius: 8px; }")
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(12, 12, 12, 12)
        
        stats_title = QLabel("📊 Estatísticas")
        stats_title.setStyleSheet("font-weight: bold; color: #1F2937;")
        stats_layout.addWidget(stats_title)
        
        self.monthly_stats_label = QLabel("Preencha pelo menos 12 meses para ver estatísticas.")
        self.monthly_stats_label.setWordWrap(True)
        self.monthly_stats_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        stats_layout.addWidget(self.monthly_stats_label)
        
        right_layout.addWidget(stats_frame, stretch=1)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 350])
        
        layout.addWidget(splitter, stretch=1)
        
        # Info box
        info_frame = QFrame()
        info_frame.setObjectName("card_info")
        info_frame.setStyleSheet("QFrame#card_info { background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; }")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 8, 12, 8)
        
        info_icon = QLabel("💡")
        info_icon.setStyleSheet("font-size: 16px;")
        info_layout.addWidget(info_icon)
        
        info_text = QLabel(
            "<b>Dica:</b> Informe os retornos mensais em sequência (mês 1, 2, 3...). "
            "Mínimo de 12 meses para gerar cenários."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #1E40AF; font-size: 11px;")
        info_layout.addWidget(info_text, stretch=1)
        
        layout.addWidget(info_frame)
        
        # Guardar referências para botões do footer da página 2
        self.page2_bottom_buttons = {
            'export': None,
            'import': None,
            'example': None,
            'clear': None
        }
        
        self.stacked.addWidget(page)
        
        # NÃO inicializar linhas aqui - será feito após criar o footer

    def _add_row(self):
        """Adiciona uma nova linha na tabela."""
        row = self.data_table.rowCount()
        self.data_table.blockSignals(True)
        self.data_table.insertRow(row)
        
        # Coluna 0: Nº do Mês (não editável)
        month_item = QTableWidgetItem(str(row + 1))
        month_item.setFlags(month_item.flags() & ~Qt.ItemIsEditable)
        month_item.setTextAlignment(Qt.AlignCenter)
        month_item.setBackground(QColor("#F9FAFB"))
        self.data_table.setItem(row, 0, month_item)
        
        # Coluna 1: Retorno (editável)
        return_item = QTableWidgetItem("")
        return_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.data_table.setItem(row, 1, return_item)
        
        # Coluna 2: Observação (editável)
        obs_item = QTableWidgetItem("")
        self.data_table.setItem(row, 2, obs_item)
        
        self.data_table.blockSignals(False)
        self._update_data_status()

    def _add_multiple_rows(self, count: int):
        """Adiciona múltiplas linhas."""
        for _ in range(count):
            self._add_row()

    def _remove_last_row(self):
        """Remove a última linha."""
        row_count = self.data_table.rowCount()
        if row_count > 0:
            self.data_table.removeRow(row_count - 1)
            self._update_data_status()

    def _clear_all_data(self):
        """Limpa todos os dados."""
        reply = QMessageBox.question(
            self, "Confirmar",
            "Remover todos os dados?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.data_table.setRowCount(0)
            self.monthly_values.clear()
            self._add_multiple_rows(12)  # Reiniciar com 12 linhas
            self._update_data_status()

    def _on_cell_changed(self, row: int, column: int):
        """Callback quando uma célula é alterada."""
        if column == 1:  # Coluna de retorno
            self._update_monthly_values()
            self._update_data_status()

    def _update_monthly_values(self):
        """Atualiza dicionário de valores mensais a partir da tabela."""
        self.monthly_values.clear()
        
        for row in range(self.data_table.rowCount()):
            return_item = self.data_table.item(row, 1)
            if return_item and return_item.text().strip():
                try:
                    # Aceitar vírgula ou ponto como separador decimal
                    value_text = return_item.text().strip().replace(',', '.')
                    value = float(value_text)
                    month_num = row + 1
                    self.monthly_values[str(month_num)] = value
                except ValueError:
                    pass  # Ignorar valores inválidos

    def _update_data_status(self):
        """Atualiza status de preenchimento."""
        total_filled = len(self.monthly_values)
        
        if total_filled >= 12:
            self.data_status_label.setText(f"✅ {total_filled} meses preenchidos")
            self.data_status_label.setStyleSheet("color: #10B981; font-weight: 500;")
        else:
            self.data_status_label.setText(f"⚠️ {total_filled} meses preenchidos (mínimo: 12)")
            self.data_status_label.setStyleSheet("color: #EF4444; font-weight: 500;")
        
        # Atualizar gráfico e estatísticas
        self._update_monthly_chart()
        self._update_monthly_stats()
        
        self._update_navigation_buttons()

    def _update_monthly_chart(self):
        """Atualiza gráfico de evolução dos retornos mensais."""
        if not hasattr(self, 'monthly_chart'):
            return
            
        if len(self.monthly_values) < 2:
            self.monthly_chart.setHtml("<html><body style='display:flex;align-items:center;justify-content:center;height:100%;color:#9CA3AF;'>Preencha dados para ver o gráfico</body></html>")
            return
        
        try:
            sorted_keys = sorted(self.monthly_values.keys(), key=lambda x: int(x))
            months = [int(k) for k in sorted_keys]
            returns = [self.monthly_values[k] for k in sorted_keys]
            
            html = f"""<!DOCTYPE html><html><head>
            <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
            <style>body {{ margin: 0; }}</style></head><body>
            <div id="chart" style="width:100%;height:180px;"></div>
            <script>
            var data = [{{
                x: {months},
                y: {returns},
                type: 'scatter',
                mode: 'lines+markers',
                marker: {{color: '#10B981', size: 4}},
                line: {{color: '#10B981', width: 2}}
            }}];
            var layout = {{
                margin: {{l: 40, r: 10, t: 10, b: 30}},
                xaxis: {{title: 'Mês', dtick: {max(1, len(months)//10)}}},
                yaxis: {{title: 'Retorno (%)'}},
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)'
            }};
            Plotly.newPlot('chart', data, layout, {{responsive: true, displayModeBar: false}});
            </script></body></html>"""
            self.monthly_chart.setHtml(html)
        except Exception:
            pass

    def _update_monthly_stats(self):
        """Atualiza estatísticas dos retornos mensais."""
        if not hasattr(self, 'monthly_stats_label'):
            return
            
        if len(self.monthly_values) < 12:
            self.monthly_stats_label.setText("Preencha pelo menos 12 meses para ver estatísticas.")
            return
        
        try:
            returns = np.array(list(self.monthly_values.values()))
            
            mean_val = float(np.mean(returns))
            median_val = float(np.median(returns))
            std_val = float(np.std(returns))
            min_val = float(np.min(returns))
            max_val = float(np.max(returns))
            
            # Calcular retorno anual composto (aproximado)
            annual_return = (1 + mean_val/100)**12 - 1
            annual_return_pct = annual_return * 100
            
            stats_html = f"""
            <b>Período:</b> {len(self.monthly_values)} meses<br><br>
            <b>Média Mensal:</b> {mean_val:.2f}%<br>
            <b>Mediana:</b> {median_val:.2f}%<br>
            <b>Desvio Padrão:</b> {std_val:.2f}%<br>
            <b>Mínimo:</b> {min_val:.2f}%<br>
            <b>Máximo:</b> {max_val:.2f}%<br><br>
            <b>Retorno Anual (aprox.):</b> {annual_return_pct:.1f}%<br>
            <br><i style='color:#6B7280;font-size:10px;'>Estes valores serão usados no Bootstrap.</i>
            """
            self.monthly_stats_label.setText("")
            self.monthly_stats_label.setTextFormat(Qt.RichText)
            self.monthly_stats_label.setText(stats_html)
        except Exception:
            self.monthly_stats_label.setText("Erro ao calcular estatísticas.")

    def _export_template(self):
        """Exporta template CSV no novo formato."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Template", 
            "rendimentos_mensais_template.csv", 
            "CSV (*.csv)"
        )
        if not filepath:
            return
        try:
            # Gerar template no novo formato
            lines = ["Nº do Mês;Retorno do Mês (%);Observação"]
            for i in range(1, 13):  # 12 linhas de exemplo
                lines.append(f"{i};;")
            
            template = "\n".join(lines)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template)
            QMessageBox.information(
                self, "Sucesso", 
                f"Template exportado para:\n{filepath}\n\n"
                "Preencha a coluna 'Retorno do Mês (%)' com os valores."
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar: {str(e)}")

    def _import_monthly_csv(self):
        """Importa dados de CSV no novo formato."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importar Dados Mensais", 
            "", 
            "CSV (*.csv);;Todos (*)"
        )
        if not filepath:
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse do novo formato
            lines = content.strip().split('\n')
            
            # Detectar delimitador
            delimiter = ';' if ';' in lines[0] else ','
            
            # Pular header se existir
            start_idx = 0
            first_line = lines[0].lower()
            if 'mês' in first_line or 'mes' in first_line or 'retorno' in first_line or 'month' in first_line:
                start_idx = 1
            
            # Limpar tabela atual
            self.data_table.setRowCount(0)
            self.monthly_values.clear()
            
            # Processar linhas
            for line in lines[start_idx:]:
                if not line.strip():
                    continue
                    
                parts = line.split(delimiter)
                if len(parts) >= 2:
                    month_num = parts[0].strip()
                    return_str = parts[1].strip().replace(',', '.').replace('%', '')
                    obs = parts[2].strip() if len(parts) > 2 else ""
                    
                    if return_str:
                        try:
                            return_val = float(return_str)
                            
                            # Adicionar linha na tabela
                            row = self.data_table.rowCount()
                            self.data_table.blockSignals(True)
                            self.data_table.insertRow(row)
                            
                            # Nº do Mês
                            month_item = QTableWidgetItem(str(row + 1))
                            month_item.setFlags(month_item.flags() & ~Qt.ItemIsEditable)
                            month_item.setTextAlignment(Qt.AlignCenter)
                            month_item.setBackground(QColor("#F9FAFB"))
                            self.data_table.setItem(row, 0, month_item)
                            
                            # Retorno
                            return_item = QTableWidgetItem(f"{return_val:.2f}")
                            return_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                            self.data_table.setItem(row, 1, return_item)
                            
                            # Observação
                            obs_item = QTableWidgetItem(obs)
                            self.data_table.setItem(row, 2, obs_item)
                            
                            self.data_table.blockSignals(False)
                            
                            # Armazenar valor
                            self.monthly_values[str(row + 1)] = return_val
                            
                        except ValueError:
                            pass  # Ignorar valores inválidos
            
            self._update_data_status()
            QMessageBox.information(
                self, "Importação Concluída", 
                f"{len(self.monthly_values)} meses importados!"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar:\n{str(e)}")

    def _load_example_data(self):
        """Carrega dados de exemplo (CDI mensal aproximado)."""
        reply = QMessageBox.question(
            self, "Carregar Exemplo", 
            "Isso substituirá os dados atuais por 108 meses de exemplo (CDI).\n\nDeseja continuar?", 
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        
        # Dados de exemplo: CDI mensal aproximado 2017-2025 (108 meses)
        example_returns = [
            # 2017
            1.08, 0.86, 1.05, 0.79, 0.93, 0.81, 0.80, 0.80, 0.64, 0.64, 0.57, 0.54,
            # 2018
            0.58, 0.46, 0.53, 0.52, 0.52, 0.52, 0.54, 0.57, 0.47, 0.54, 0.49, 0.49,
            # 2019
            0.54, 0.49, 0.47, 0.52, 0.54, 0.47, 0.57, 0.50, 0.46, 0.48, 0.38, 0.37,
            # 2020
            0.38, 0.29, 0.34, 0.28, 0.24, 0.21, 0.19, 0.16, 0.16, 0.16, 0.15, 0.16,
            # 2021
            0.15, 0.13, 0.20, 0.21, 0.27, 0.31, 0.36, 0.43, 0.44, 0.49, 0.59, 0.77,
            # 2022
            0.73, 0.76, 0.93, 0.83, 1.03, 1.02, 1.03, 1.17, 1.07, 1.02, 1.02, 1.12,
            # 2023
            1.12, 0.92, 1.17, 0.92, 1.12, 1.07, 1.07, 1.14, 0.97, 1.00, 0.92, 0.89,
            # 2024
            0.97, 0.80, 0.83, 0.89, 0.83, 0.79, 0.91, 0.87, 0.83, 0.93, 0.79, 0.93,
            # 2025
            1.00, 0.99, 1.06, 0.94, 1.01, 0.89, 0.95, 0.92, 0.88, 0.97, 0.91, 1.05
        ]
        
        # Limpar tabela
        self.data_table.setRowCount(0)
        self.monthly_values.clear()
        
        # Preencher tabela
        self.data_table.blockSignals(True)
        for i, ret in enumerate(example_returns):
            row = self.data_table.rowCount()
            self.data_table.insertRow(row)
            
            # Nº do Mês
            month_item = QTableWidgetItem(str(i + 1))
            month_item.setFlags(month_item.flags() & ~Qt.ItemIsEditable)
            month_item.setTextAlignment(Qt.AlignCenter)
            month_item.setBackground(QColor("#F9FAFB"))
            self.data_table.setItem(row, 0, month_item)
            
            # Retorno
            return_item = QTableWidgetItem(f"{ret:.2f}")
            return_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.data_table.setItem(row, 1, return_item)
            
            # Observação
            obs_item = QTableWidgetItem("")
            self.data_table.setItem(row, 2, obs_item)
            
            # Armazenar valor
            self.monthly_values[str(i + 1)] = ret
        
        self.data_table.blockSignals(False)
        self._update_data_status()
        
        QMessageBox.information(
            self, "Dados Carregados", 
            f"108 meses de dados de exemplo (CDI aproximado) foram carregados."
        )

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
        """
        Etapa 4 - Geração de Cenários (Layout Unificado)
        
        Estrutura:
        - Cabeçalho compacto: Input de cenários + botão gerar
        - Área principal: Histograma (60%) + Estatísticas (40%)
        - Sem abas - visão contínua
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        
        # ═══════════════════════════════════════════════════════════════
        # BARRA DE COMANDO - Altura mínima, alinhamento perfeito
        # ═══════════════════════════════════════════════════════════════
        header_frame = QFrame()
        header_frame.setObjectName("header_bar")
        header_frame.setFixedHeight(50)
        header_frame.setStyleSheet("""
            QFrame#header_bar {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 5, 12, 5)
        header_layout.setSpacing(10)
        header_layout.setAlignment(Qt.AlignVCenter)
        
        # Label - mesma fonte do SpinBox
        config_label = QLabel("Número de Cenários:")
        config_label.setStyleSheet("font-weight: 600; color: #374151; font-size: 13px; font-family: 'Segoe UI', Arial, sans-serif;")
        header_layout.addWidget(config_label)
        
        # SpinBox - fonte harmonizada
        self.scenarios_spin = QSpinBox()
        self.scenarios_spin.setRange(1000, 100000)
        self.scenarios_spin.setSingleStep(1000)
        self.scenarios_spin.setValue(10000)
        self.scenarios_spin.setFixedWidth(110)
        self.scenarios_spin.setFixedHeight(30)
        self.scenarios_spin.setStyleSheet("""
            QSpinBox {
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 600;
                padding: 2px 8px;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                background: white;
            }
            QSpinBox:focus {
                border-color: #3B82F6;
            }
        """)
        self.scenarios_spin.valueChanged.connect(self._update_time_estimate)
        header_layout.addWidget(self.scenarios_spin)
        
        # Tempo estimado
        self.time_estimate_label = QLabel("≈ 5s")
        self.time_estimate_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        self.time_estimate_label.setFixedWidth(50)
        header_layout.addWidget(self.time_estimate_label)
        
        # Progress bar inline (compacta)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(120)
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 8px;
                background-color: #E5E7EB;
                text-align: center;
                font-size: 10px;
            }
            QProgressBar::chunk {
                border-radius: 8px;
                background-color: #10B981;
            }
        """)
        header_layout.addWidget(self.progress_bar)
        
        header_layout.addStretch()
        
        # Botão Gerar - compacto
        self.btn_generate = QPushButton("🔄 Gerar Cenários")
        self.btn_generate.setObjectName("btn_generate")
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.setFixedHeight(32)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
            QPushButton:pressed {
                background-color: #6D28D9;
            }
            QPushButton:disabled {
                background-color: #C4B5FD;
            }
        """)
        self.btn_generate.clicked.connect(self._start_generation)
        header_layout.addWidget(self.btn_generate)
        
        layout.addWidget(header_frame)
        
        # ═══════════════════════════════════════════════════════════════
        # ÁREA DE RESULTADOS (Histograma + Estatísticas) - Sem abas
        # ═══════════════════════════════════════════════════════════════
        self.results_frame = QFrame()
        self.results_frame.setObjectName("results_area")
        self.results_frame.setStyleSheet("""
            QFrame#results_area {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        self.results_frame.hide()
        
        results_main_layout = QVBoxLayout(self.results_frame)
        results_main_layout.setContentsMargins(0, 0, 0, 0)
        results_main_layout.setSpacing(0)
        
        # ScrollArea para conteúdo responsivo
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: white;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(12, 12, 12, 12)
        scroll_layout.setSpacing(12)
        
        # Título de sucesso - compacto
        success_header = QHBoxLayout()
        success_header.setSpacing(8)
        success_icon = QLabel("✅")
        success_icon.setStyleSheet("font-size: 16px;")
        success_header.addWidget(success_icon)
        
        success_title = QLabel("Cenários Gerados com Sucesso")
        success_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #059669;")
        success_header.addWidget(success_title)
        success_header.addStretch()
        
        scroll_layout.addLayout(success_header)
        
        # ─────────────────────────────────────────────────────────────
        # SEÇÃO 1: HISTOGRAMA - Topo, expansível
        # ─────────────────────────────────────────────────────────────
        chart_section = QFrame()
        chart_section.setObjectName("chart_section")
        chart_section.setStyleSheet("""
            QFrame#chart_section {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        chart_layout_inner = QVBoxLayout(chart_section)
        chart_layout_inner.setContentsMargins(8, 8, 8, 8)
        chart_layout_inner.setSpacing(4)
        
        chart_title = QLabel("📊 Distribuição dos Retornos Anuais")
        chart_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #374151;")
        chart_title.setAlignment(Qt.AlignCenter)
        chart_layout_inner.addWidget(chart_title)
        
        self.dist_chart = QWebEngineView()
        self.dist_chart.setMinimumHeight(400)
        self.dist_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chart_layout_inner.addWidget(self.dist_chart)
        
        scroll_layout.addWidget(chart_section, stretch=6)  # 60%
        
        # ─────────────────────────────────────────────────────────────
        # SEÇÃO 2: ESTATÍSTICAS - Abaixo do histograma, 100% largura
        # ─────────────────────────────────────────────────────────────
        stats_section = QFrame()
        stats_section.setObjectName("stats_section")
        stats_section.setStyleSheet("""
            QFrame#stats_section {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        stats_section_layout = QVBoxLayout(stats_section)
        stats_section_layout.setContentsMargins(12, 10, 12, 10)
        stats_section_layout.setSpacing(8)
        
        stats_title = QLabel("📈 Estatísticas dos Cenários")
        stats_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #374151;")
        stats_title.setAlignment(Qt.AlignCenter)
        stats_section_layout.addWidget(stats_title)
        
        # Grid de estatísticas - ocupa 100% da largura
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(8)
        self.stats_grid.setContentsMargins(0, 0, 0, 0)
        stats_section_layout.addLayout(self.stats_grid)
        
        scroll_layout.addWidget(stats_section, stretch=4)  # 40%
        
        scroll_area.setWidget(scroll_content)
        results_main_layout.addWidget(scroll_area)
        
        layout.addWidget(self.results_frame, stretch=1)
        
        # ═══════════════════════════════════════════════════════════════
        # PLACEHOLDER - Quando não há resultados
        # ═══════════════════════════════════════════════════════════════
        self.placeholder_frame = QFrame()
        self.placeholder_frame.setObjectName("placeholder")
        self.placeholder_frame.setStyleSheet("""
            QFrame#placeholder {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        
        placeholder_layout = QVBoxLayout(self.placeholder_frame)
        placeholder_layout.setContentsMargins(40, 40, 40, 40)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        
        placeholder_icon = QLabel("🎲")
        placeholder_icon.setStyleSheet("font-size: 48px;")
        placeholder_icon.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(placeholder_icon)
        
        placeholder_text = QLabel("Clique em 'Gerar Cenários' para iniciar a simulação Bootstrap")
        placeholder_text.setStyleSheet("color: #9CA3AF; font-size: 13px;")
        placeholder_text.setAlignment(Qt.AlignCenter)
        placeholder_text.setWordWrap(True)
        placeholder_layout.addWidget(placeholder_text)
        
        layout.addWidget(self.placeholder_frame, stretch=1)
        
        self.stacked.addWidget(page)

    def _update_time_estimate(self):
        n = self.scenarios_spin.value()
        time_sec = estimate_generation_time(n)
        self.time_estimate_label.setText(f"≈ {format_time_estimate(time_sec)}")

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
        
        # Mostrar resultados, esconder placeholder
        self.placeholder_frame.hide()
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
        
        # Função para converter hex para rgb
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
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
            card.setMinimumHeight(60)
            
            # Converter cor hex para rgba para background
            rgb = hex_to_rgb(color)
            bg_color = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.1)"
            border_color = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.3)"
            
            card.setStyleSheet(f"""
                QFrame {{ 
                    background-color: {bg_color}; 
                    border: 1px solid {border_color}; 
                    border-radius: 8px; 
                }}
                QLabel {{
                    border: none;
                    background: transparent;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 6, 10, 6)
            card_layout.setSpacing(2)
            
            label_w = QLabel(label)
            label_w.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 600;")
            card_layout.addWidget(label_w)
            
            value_w = QLabel(value)
            value_w.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
            card_layout.addWidget(value_w)
            
            self.stats_grid.addWidget(card, row, col)
        
        # Histograma refatorado com visibilidade total dos eixos
        self._render_distribution_chart(r)

    def _render_distribution_chart(self, result):
        """
        Renderiza histograma de distribuição com visibilidade total dos eixos.
        
        Configurações otimizadas:
        - Margens explícitas para garantir espaço aos títulos
        - Linha da Mediana (P50) em preto sólido
        - Posicionamento estratégico de rótulos (sem sobreposição)
        - Template plotly_white para contraste máximo
        """
        returns = result.annual_returns.tolist()
        
        # HTML com container responsivo e estilos otimizados
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ 
            width: 100%; 
            height: 100%; 
            overflow: hidden;
            background: white;
        }}
        #chart {{ 
            width: 100%; 
            height: 100%; 
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
        }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <script>
        var data = [{{
            x: {returns},
            type: 'histogram',
            nbinsx: 50,
            marker: {{
                color: '#8B5CF6',
                line: {{color: '#7C3AED', width: 1}}
            }},
            hovertemplate: 'Retorno: %{{x:.2f}}%<br>Frequência: %{{y}}<extra></extra>'
        }}];
        
        var layout = {{
            // Margens explícitas para visibilidade total
            margin: {{l: 80, r: 50, t: 70, b: 80}},
            
            // Autosize para responsividade
            autosize: true,
            
            // Template de alto contraste
            template: 'plotly_white',
            
            // Configuração do Eixo X
            xaxis: {{
                title: {{
                    text: 'Retorno Anual (%)',
                    font: {{size: 14, color: '#1F2937', family: 'Arial, sans-serif'}},
                    standoff: 20
                }},
                showticklabels: true,
                tickfont: {{size: 12, color: '#374151'}},
                tickformat: '.0f',
                showgrid: true,
                gridcolor: '#E5E7EB',
                gridwidth: 1,
                zeroline: true,
                zerolinecolor: '#9CA3AF',
                showline: true,
                linecolor: '#D1D5DB',
                linewidth: 1,
                mirror: false
            }},
            
            // Configuração do Eixo Y
            yaxis: {{
                title: {{
                    text: 'Frequência (Cenários)',
                    font: {{size: 14, color: '#1F2937', family: 'Arial, sans-serif'}},
                    standoff: 15
                }},
                showticklabels: true,
                tickfont: {{size: 12, color: '#374151'}},
                rangemode: 'tozero',
                showgrid: true,
                gridcolor: '#E5E7EB',
                gridwidth: 1,
                zeroline: true,
                zerolinecolor: '#9CA3AF',
                showline: true,
                linecolor: '#D1D5DB',
                linewidth: 1,
                mirror: false
            }},
            
            // Cores de fundo
            paper_bgcolor: 'white',
            plot_bgcolor: '#FAFAFA',
            
            // Linhas de referência (P5, Média, Mediana, P95)
            shapes: [
                // P5 - Pessimista (vermelho tracejado)
                {{
                    type: 'line',
                    x0: {result.p5}, x1: {result.p5},
                    y0: 0, y1: 1, yref: 'paper',
                    line: {{color: '#EF4444', width: 2, dash: 'dash'}}
                }},
                // Média (azul sólido)
                {{
                    type: 'line',
                    x0: {result.mean}, x1: {result.mean},
                    y0: 0, y1: 1, yref: 'paper',
                    line: {{color: '#3B82F6', width: 2, dash: 'solid'}}
                }},
                // Mediana P50 (preto sólido - destaque central)
                {{
                    type: 'line',
                    x0: {result.median}, x1: {result.median},
                    y0: 0, y1: 1, yref: 'paper',
                    line: {{color: '#1F2937', width: 2, dash: 'solid'}}
                }},
                // P95 - Otimista (verde tracejado)
                {{
                    type: 'line',
                    x0: {result.p95}, x1: {result.p95},
                    y0: 0, y1: 1, yref: 'paper',
                    line: {{color: '#10B981', width: 2, dash: 'dash'}}
                }}
            ],
            
            // Anotações com posicionamento estratégico (sem sobreposição)
            annotations: [
                // P5 - Rótulo à ESQUERDA da linha
                {{
                    x: {result.p5}, y: 1.02, yref: 'paper',
                    text: '<b>P5</b><br>{result.p5:.1f}%',
                    showarrow: false,
                    font: {{size: 10, color: '#EF4444'}},
                    xanchor: 'right',
                    align: 'right'
                }},
                // Média - Rótulo à ESQUERDA da linha
                {{
                    x: {result.mean}, y: 1.02, yref: 'paper',
                    text: '<b>Média</b><br>{result.mean:.1f}%',
                    showarrow: false,
                    font: {{size: 10, color: '#3B82F6'}},
                    xanchor: 'right',
                    align: 'right'
                }},
                // Mediana P50 - Rótulo à DIREITA da linha
                {{
                    x: {result.median}, y: 1.02, yref: 'paper',
                    text: '<b>P50</b><br>{result.median:.1f}%',
                    showarrow: false,
                    font: {{size: 10, color: '#1F2937'}},
                    xanchor: 'left',
                    align: 'left'
                }},
                // P95 - Rótulo à DIREITA da linha
                {{
                    x: {result.p95}, y: 1.02, yref: 'paper',
                    text: '<b>P95</b><br>{result.p95:.1f}%',
                    showarrow: false,
                    font: {{size: 10, color: '#10B981'}},
                    xanchor: 'left',
                    align: 'left'
                }}
            ]
        }};
        
        var config = {{
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d']
        }};
        
        Plotly.newPlot('chart', data, layout, config);
        
        // Redesenhar ao redimensionar
        window.addEventListener('resize', function() {{
            Plotly.Plots.resize('chart');
        }});
    </script>
</body>
</html>"""
        
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

    def _import_and_skip_to_results(self):
        """
        Importa cenários diretamente da Etapa 1 e pula para Etapa 4.
        
        Fluxo:
        1. Abre seletor de arquivos
        2. Importa cenários do CSV
        3. Pula diretamente para Etapa 4 (visualização)
        """
        filepath, _ = QFileDialog.getOpenFileName(
            self, 
            "Importar Cenários Existentes", 
            "", 
            "CSV de Cenários (*.csv);;Todos os arquivos (*)"
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            returns, metadata = import_scenarios_csv(content)
            
            # Criar resultado a partir dos dados importados
            self.result = SyntheticScenariosResult(
                annual_returns=returns,
                n_scenarios=len(returns),
                method=metadata.get('Método', 'importado'),
                block_size=None,
                source_period=metadata.get('Período Fonte', 'N/A'),
                source_n_months=int(metadata.get('Meses Fonte', 0)) if metadata.get('Meses Fonte', '').isdigit() else 0,
                generation_time=0.0,
                seed=None
            )
            
            # Exibir resultados
            self._display_results()
            
            # Pular diretamente para Etapa 4 (índice 3)
            self._go_to_page(3)
            
            # Mostrar frame de resultados, esconder placeholder
            self.placeholder_frame.hide()
            self.results_frame.show()
            
            QMessageBox.information(
                self, 
                "Importação Bem-Sucedida", 
                f"✅ {len(returns):,} cenários importados!\n\n"
                f"Você foi direcionado para a visualização dos resultados."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Erro na Importação", 
                f"Não foi possível importar os cenários:\n\n{str(e)}\n\n"
                "Verifique se o arquivo está no formato correto."
            )

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
        
        # Botões específicos da página 2 (dados mensais)
        self.btn_export_csv = QPushButton("📥 Exportar Modelo")
        self.btn_export_csv.setObjectName("btn_secondary")
        self.btn_export_csv.setCursor(Qt.PointingHandCursor)
        self.btn_export_csv.clicked.connect(self._export_template)
        self.btn_export_csv.hide()
        footer_layout.addWidget(self.btn_export_csv)
        
        self.btn_import_csv = QPushButton("📤 Importar CSV")
        self.btn_import_csv.setObjectName("btn_secondary")
        self.btn_import_csv.setCursor(Qt.PointingHandCursor)
        self.btn_import_csv.clicked.connect(self._import_monthly_csv)
        self.btn_import_csv.hide()
        footer_layout.addWidget(self.btn_import_csv)
        
        self.btn_load_example = QPushButton("📋 Carregar Exemplo")
        self.btn_load_example.setObjectName("btn_secondary")
        self.btn_load_example.setCursor(Qt.PointingHandCursor)
        self.btn_load_example.clicked.connect(self._load_example_data)
        self.btn_load_example.hide()
        footer_layout.addWidget(self.btn_load_example)
        
        self.btn_clear_data = QPushButton("🗑️ Limpar")
        self.btn_clear_data.setObjectName("btn_danger")
        self.btn_clear_data.setCursor(Qt.PointingHandCursor)
        self.btn_clear_data.clicked.connect(self._clear_all_data)
        self.btn_clear_data.hide()
        footer_layout.addWidget(self.btn_clear_data)
        
        # Botões específicos da página 4 (geração)
        self.btn_export_scenarios = QPushButton("📥 Exportar CSV")
        self.btn_export_scenarios.setObjectName("btn_secondary")
        self.btn_export_scenarios.setCursor(Qt.PointingHandCursor)
        self.btn_export_scenarios.clicked.connect(self._export_scenarios)
        self.btn_export_scenarios.hide()
        footer_layout.addWidget(self.btn_export_scenarios)
        
        self.btn_import_scenarios = QPushButton("📤 Importar Cenários")
        self.btn_import_scenarios.setObjectName("btn_secondary")
        self.btn_import_scenarios.setCursor(Qt.PointingHandCursor)
        self.btn_import_scenarios.clicked.connect(self._import_scenarios)
        self.btn_import_scenarios.hide()
        footer_layout.addWidget(self.btn_import_scenarios)
        
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
                # Emitir signal para abrir diálogo de dados anuais
                self.use_annual_data.emit()
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
        
        # Botões específicos da página 2 (dados mensais)
        is_page2 = (current == 1)
        self.btn_export_csv.setVisible(is_page2)
        self.btn_import_csv.setVisible(is_page2)
        self.btn_load_example.setVisible(is_page2)
        self.btn_clear_data.setVisible(is_page2)
        
        # Botões específicos da página 4 (geração)
        is_page4 = (current == 3)
        has_result = (self.result is not None)
        self.btn_export_scenarios.setVisible(is_page4 and has_result)
        self.btn_import_scenarios.setVisible(is_page4)
        
        if current == 3:
            self.btn_next.hide()
            self.btn_finish.setVisible(has_result)
        else:
            self.btn_next.show()
            self.btn_finish.hide()
            self.btn_next.setEnabled(current != 1 or len(self.monthly_values) >= 12)

    def _prepare_bootstrap_data(self):
        """Prepara dados para bootstrap a partir da tabela."""
        if len(self.monthly_values) < 12:
            return
        try:
            # Ordenar por número do mês (1, 2, 3, ...)
            sorted_keys = sorted(self.monthly_values.keys(), key=lambda x: int(x))
            
            # Criar lista de períodos sequenciais
            periods = [f"Mês {k}" for k in sorted_keys]
            returns = np.array([self.monthly_values[k] for k in sorted_keys])
            
            self.monthly_data = MonthlyReturnData(periods=periods, returns=returns)
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
