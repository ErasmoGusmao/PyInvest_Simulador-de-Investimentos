"""
PyInvest - Diálogo de Rendimentos Históricos
Interface para gerenciar dados de retorno anual para Bootstrap.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QFileDialog, QLineEdit, QSpinBox,
    QDoubleSpinBox, QWidget, QSizePolicy, QAbstractItemView,
    QSplitter, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWebEngineWidgets import QWebEngineView

import numpy as np
from typing import List, Optional
import json

from core.statistics import HistoricalReturn, import_historical_returns_csv, export_historical_returns_csv


class HistoricalReturnsDialog(QDialog):
    """
    Diálogo para gerenciar dados de rendimento histórico.
    
    Permite adicionar, editar, importar/exportar dados para Bootstrap.
    """
    
    returns_confirmed = Signal(list)  # Lista de HistoricalReturn
    
    def __init__(self, returns: Optional[List[HistoricalReturn]] = None, parent=None):
        super().__init__(parent)
        
        self.returns = returns or []
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Configura a interface."""
        self.setWindowTitle("📊 Dados de Rendimento Histórico")
        self.setMinimumSize(900, 600)
        self.setModal(True)
        
        # Permitir maximizar
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        
        # Estilo
        self.setStyleSheet("""
            QDialog {
                background-color: #F3F4F6;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #1F2937;
            }
            QLabel#subtitle {
                font-size: 13px;
                color: #6B7280;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton#btn_primary {
                background-color: #10B981;
                color: white;
                border: none;
            }
            QPushButton#btn_primary:hover {
                background-color: #059669;
            }
            QPushButton#btn_secondary {
                background-color: white;
                color: #374151;
                border: 1px solid #D1D5DB;
            }
            QPushButton#btn_secondary:hover {
                background-color: #F9FAFB;
            }
            QPushButton#btn_danger {
                background-color: #EF4444;
                color: white;
                border: none;
            }
            QPushButton#btn_danger:hover {
                background-color: #DC2626;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                gridline-color: #F3F4F6;
            }
            QHeaderView::section {
                background-color: #F9FAFB;
                color: #374151;
                font-weight: 600;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #E5E7EB;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        
        title = QLabel("📊 Dados de Rendimento Histórico")
        title.setObjectName("title")
        header.addWidget(title)
        
        subtitle = QLabel("Informe os retornos anuais para usar no método Bootstrap")
        subtitle.setObjectName("subtitle")
        header.addWidget(subtitle)
        
        layout.addLayout(header)
        
        # Splitter: Tabela | Gráfico + Stats
        splitter = QSplitter(Qt.Horizontal)
        
        # === LADO ESQUERDO: Formulário + Tabela ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Formulário de entrada
        self._create_input_form(left_layout)
        
        # Tabela
        self._create_table(left_layout)
        
        splitter.addWidget(left_widget)
        
        # === LADO DIREITO: Gráfico + Estatísticas ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Gráfico
        self._create_chart(right_layout)
        
        # Estatísticas
        self._create_stats(right_layout)
        
        splitter.addWidget(right_widget)
        
        splitter.setSizes([450, 450])
        layout.addWidget(splitter, stretch=1)
        
        # Botões de ação
        self._create_action_buttons(layout)
    
    def _create_input_form(self, parent_layout: QVBoxLayout):
        """Cria formulário de entrada."""
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        
        form_layout = QHBoxLayout(form_frame)
        form_layout.setSpacing(12)
        
        # Ano
        year_layout = QVBoxLayout()
        year_layout.setSpacing(4)
        year_label = QLabel("Ano")
        year_label.setStyleSheet("font-weight: 500; color: #374151; font-size: 12px;")
        self.year_input = QSpinBox()
        self.year_input.setRange(1900, 2100)
        self.year_input.setValue(2024)
        self.year_input.setMinimumWidth(100)
        year_layout.addWidget(year_label)
        year_layout.addWidget(self.year_input)
        form_layout.addLayout(year_layout)
        
        # Retorno
        return_layout = QVBoxLayout()
        return_layout.setSpacing(4)
        return_label = QLabel("Retorno Anual (%)")
        return_label.setStyleSheet("font-weight: 500; color: #374151; font-size: 12px;")
        self.return_input = QDoubleSpinBox()
        self.return_input.setRange(-100, 500)
        self.return_input.setDecimals(2)
        self.return_input.setSuffix(" %")
        self.return_input.setValue(10.0)
        self.return_input.setMinimumWidth(120)
        return_layout.addWidget(return_label)
        return_layout.addWidget(self.return_input)
        form_layout.addLayout(return_layout)
        
        # Notas
        notes_layout = QVBoxLayout()
        notes_layout.setSpacing(4)
        notes_label = QLabel("Notas (opcional)")
        notes_label.setStyleSheet("font-weight: 500; color: #374151; font-size: 12px;")
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Ex: Ano de crise")
        notes_layout.addWidget(notes_label)
        notes_layout.addWidget(self.notes_input)
        form_layout.addLayout(notes_layout, stretch=1)
        
        # Botão Adicionar
        add_layout = QVBoxLayout()
        add_layout.setSpacing(4)
        add_layout.addWidget(QLabel(""))
        btn_add = QPushButton("➕ Adicionar")
        btn_add.setObjectName("btn_primary")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self._add_return)
        add_layout.addWidget(btn_add)
        form_layout.addLayout(add_layout)
        
        parent_layout.addWidget(form_frame)
    
    def _create_table(self, parent_layout: QVBoxLayout):
        """Cria tabela de retornos."""
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Ano', 'Retorno (%)', 'Notas'])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 120)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        # Menu de contexto
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        parent_layout.addWidget(self.table, stretch=1)
    
    def _create_chart(self, parent_layout: QVBoxLayout):
        """Cria gráfico de barras."""
        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
        """)
        
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(8, 8, 8, 8)
        
        chart_title = QLabel("📈 Evolução dos Retornos")
        chart_title.setStyleSheet("font-weight: 600; font-size: 14px; color: #1F2937;")
        chart_layout.addWidget(chart_title)
        
        self.chart_view = QWebEngineView()
        self.chart_view.setMinimumHeight(250)
        chart_layout.addWidget(self.chart_view)
        
        parent_layout.addWidget(chart_frame)
    
    def _create_stats(self, parent_layout: QVBoxLayout):
        """Cria painel de estatísticas."""
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        
        stats_layout = QVBoxLayout(stats_frame)
        
        stats_title = QLabel("📊 Estatísticas")
        stats_title.setStyleSheet("font-weight: 600; font-size: 14px; color: #1E40AF;")
        stats_layout.addWidget(stats_title)
        
        self.stats_text = QLabel("Adicione dados para ver estatísticas")
        self.stats_text.setStyleSheet("font-size: 13px; color: #374151;")
        self.stats_text.setWordWrap(True)
        stats_layout.addWidget(self.stats_text)
        
        parent_layout.addWidget(stats_frame)
    
    def _create_action_buttons(self, parent_layout: QVBoxLayout):
        """Cria botões de ação."""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # Importar CSV
        btn_import = QPushButton("📥 Importar CSV")
        btn_import.setObjectName("btn_secondary")
        btn_import.setCursor(Qt.PointingHandCursor)
        btn_import.clicked.connect(self._import_csv)
        buttons_layout.addWidget(btn_import)
        
        # Exportar CSV
        btn_export = QPushButton("📤 Exportar CSV")
        btn_export.setObjectName("btn_secondary")
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.clicked.connect(self._export_csv)
        buttons_layout.addWidget(btn_export)
        
        # Limpar
        btn_clear = QPushButton("🗑️ Limpar")
        btn_clear.setObjectName("btn_danger")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(self._clear_all)
        buttons_layout.addWidget(btn_clear)
        
        buttons_layout.addStretch()
        
        # Cancelar
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)
        
        # Confirmar
        btn_confirm = QPushButton("✓ Usar Dados")
        btn_confirm.setObjectName("btn_primary")
        btn_confirm.setCursor(Qt.PointingHandCursor)
        btn_confirm.clicked.connect(self._confirm)
        buttons_layout.addWidget(btn_confirm)
        
        parent_layout.addLayout(buttons_layout)
    
    def _add_return(self):
        """Adiciona um novo retorno."""
        year = self.year_input.value()
        return_rate = self.return_input.value() / 100  # Converter para decimal
        notes = self.notes_input.text().strip()
        
        # Verificar se ano já existe
        for r in self.returns:
            if r.year == year:
                QMessageBox.warning(self, "Ano Duplicado", f"O ano {year} já foi adicionado.")
                return
        
        self.returns.append(HistoricalReturn(
            year=year,
            return_rate=return_rate,
            notes=notes
        ))
        
        self.returns.sort(key=lambda r: r.year)
        self._load_data()
        
        # Avançar ano
        self.year_input.setValue(year + 1)
        self.notes_input.clear()
    
    def _remove_return(self, index: int):
        """Remove um retorno."""
        if 0 <= index < len(self.returns):
            self.returns.pop(index)
            self._load_data()
    
    def _load_data(self):
        """Carrega dados na tabela e atualiza gráfico."""
        self.table.setRowCount(len(self.returns))
        
        for row, ret in enumerate(self.returns):
            # Ano
            year_item = QTableWidgetItem(str(ret.year))
            year_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, year_item)
            
            # Retorno
            return_pct = ret.return_rate * 100
            return_item = QTableWidgetItem(f"{return_pct:.2f}%")
            return_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Colorir baseado no valor
            if return_pct >= 0:
                return_item.setForeground(QColor('#059669'))
            else:
                return_item.setForeground(QColor('#DC2626'))
            
            self.table.setItem(row, 1, return_item)
            
            # Notas
            notes_item = QTableWidgetItem(ret.notes)
            self.table.setItem(row, 2, notes_item)
        
        self._update_chart()
        self._update_stats()
    
    def _update_chart(self):
        """Atualiza gráfico de barras."""
        if not self.returns:
            self.chart_view.setHtml("<p style='text-align:center;color:#9CA3AF;'>Sem dados</p>")
            return
        
        years = [r.year for r in self.returns]
        values = [r.return_rate * 100 for r in self.returns]
        colors = ['#10B981' if v >= 0 else '#EF4444' for v in values]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
            <style>body {{ margin: 0; }}</style>
        </head>
        <body>
            <div id="chart" style="width:100%;height:240px;"></div>
            <script>
                var data = [{{
                    x: {years},
                    y: {values},
                    type: 'bar',
                    marker: {{
                        color: {json.dumps(colors)}
                    }},
                    hovertemplate: '<b>%{{x}}</b><br>%{{y:.2f}}%<extra></extra>'
                }}];
                
                var layout = {{
                    margin: {{l: 50, r: 20, t: 20, b: 40}},
                    xaxis: {{title: 'Ano', dtick: 1}},
                    yaxis: {{title: 'Retorno (%)', zeroline: true, zerolinewidth: 2}},
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)'
                }};
                
                Plotly.newPlot('chart', data, layout, {{responsive: true}});
            </script>
        </body>
        </html>
        """
        
        self.chart_view.setHtml(html)
    
    def _update_stats(self):
        """Atualiza estatísticas."""
        if not self.returns:
            self.stats_text.setText("Adicione dados para ver estatísticas")
            return
        
        values = np.array([r.return_rate * 100 for r in self.returns])
        
        mean = np.mean(values)
        std = np.std(values)
        min_val = np.min(values)
        max_val = np.max(values)
        median = np.median(values)
        n = len(values)
        
        # Anos
        years = [r.year for r in self.returns]
        year_range = f"{min(years)} - {max(years)}"
        
        stats_html = f"""
        <b>Período:</b> {year_range} ({n} anos)<br><br>
        <b>Média:</b> {mean:.2f}%<br>
        <b>Mediana:</b> {median:.2f}%<br>
        <b>Desvio Padrão:</b> {std:.2f}%<br>
        <b>Mínimo:</b> {min_val:.2f}%<br>
        <b>Máximo:</b> {max_val:.2f}%<br><br>
        <i style="color:#6B7280;">Estes valores serão usados<br>no método Bootstrap.</i>
        """
        
        self.stats_text.setText(stats_html)
    
    def _show_context_menu(self, position):
        """Menu de contexto para deletar."""
        row = self.table.rowAt(position.y())
        if row < 0:
            return
        
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        menu = QMenu(self.table)
        delete_action = QAction("🗑️ Remover", self.table)
        delete_action.triggered.connect(lambda: self._remove_return(row))
        menu.addAction(delete_action)
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def _import_csv(self):
        """Importa dados de CSV."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importar Rendimentos",
            "", "Arquivos CSV (*.csv);;Todos (*)"
        )
        
        if not filepath:
            return
        
        returns, error = import_historical_returns_csv(filepath)
        
        if error:
            QMessageBox.critical(self, "Erro", error)
            return
        
        self.returns = returns
        self._load_data()
        
        QMessageBox.information(
            self, "Importação Concluída",
            f"{len(returns)} registros importados!"
        )
    
    def _export_csv(self):
        """Exporta dados para CSV."""
        if not self.returns:
            QMessageBox.warning(self, "Sem Dados", "Não há dados para exportar.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exportar Rendimentos",
            "rendimentos_historicos.csv",
            "Arquivos CSV (*.csv)"
        )
        
        if not filepath:
            return
        
        success, error = export_historical_returns_csv(filepath, self.returns)
        
        if success:
            QMessageBox.information(self, "Sucesso", f"Dados exportados para:\n{filepath}")
        else:
            QMessageBox.critical(self, "Erro", error)
    
    def _clear_all(self):
        """Limpa todos os dados."""
        if not self.returns:
            return
        
        reply = QMessageBox.question(
            self, "Confirmar",
            "Remover todos os dados?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.returns.clear()
            self._load_data()
    
    def _confirm(self):
        """Confirma e fecha."""
        self.returns_confirmed.emit(self.returns)
        self.accept()
    
    def get_returns(self) -> List[HistoricalReturn]:
        """Retorna lista de retornos."""
        return self.returns
