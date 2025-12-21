"""
PyInvest - Diálogo de Eventos Extraordinários
Interface para gerenciar aportes extras e resgates programados.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QFileDialog, QDateEdit, QLineEdit,
    QDoubleSpinBox, QWidget, QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QFont

from datetime import date, datetime
from typing import List, Optional

from core.events import ExtraordinaryEvent, EventsManager
from core.calculation import format_currency


class EventsDialog(QDialog):
    """
    Diálogo para gerenciar eventos extraordinários.
    
    Permite adicionar, editar, remover, importar e exportar eventos.
    """
    
    # Sinal emitido quando eventos são confirmados
    events_confirmed = Signal(object)  # EventsManager
    
    def __init__(self, events_manager: Optional[EventsManager] = None, 
                 start_date: Optional[date] = None,
                 simulation_months: int = 120,
                 parent=None):
        super().__init__(parent)
        
        self.events_manager = events_manager or EventsManager()
        self.start_date = start_date or date.today()
        self.simulation_months = simulation_months
        self._setup_ui()
        self._load_events()
    
    def _setup_ui(self):
        """Configura a interface do diálogo."""
        self.setWindowTitle("Eventos Extraordinários")
        self.setMinimumSize(900, 550)
        self.setModal(True)
        
        # Estilo do diálogo
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
                padding: 12px;
                border: none;
                border-bottom: 2px solid #E5E7EB;
            }
            QLineEdit, QDateEdit, QDoubleSpinBox {
                padding: 8px 12px;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus {
                border-color: #10B981;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        
        title = QLabel("📅 Eventos Extraordinários")
        title.setObjectName("title")
        header.addWidget(title)
        
        # Subtítulo com data de início
        start_str = self.start_date.strftime('%d/%m/%Y')
        end_date = date(
            self.start_date.year + (self.simulation_months // 12),
            self.start_date.month,
            self.start_date.day
        )
        end_str = end_date.strftime('%d/%m/%Y')
        
        subtitle = QLabel(f"Período da simulação: {start_str} a {end_str} ({self.simulation_months // 12} anos)")
        subtitle.setObjectName("subtitle")
        header.addWidget(subtitle)
        
        layout.addLayout(header)
        
        # Formulário de entrada
        self._create_input_form(layout)
        
        # Tabela de eventos
        self._create_events_table(layout)
        
        # Resumo
        self._create_summary(layout)
        
        # Botões de ação
        self._create_action_buttons(layout)
    
    def _create_input_form(self, parent_layout: QVBoxLayout):
        """Cria o formulário de entrada de novos eventos."""
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
        
        # Data
        date_layout = QVBoxLayout()
        date_layout.setSpacing(4)
        date_label = QLabel("Data")
        date_label.setStyleSheet("font-weight: 500; color: #374151; font-size: 12px;")
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate(self.start_date.year, self.start_date.month, self.start_date.day))
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        self.date_input.setMinimumWidth(130)
        self.date_input.setFixedWidth(140)
        self.date_input.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                font-size: 13px;
            }
        """)
        self.date_input.dateChanged.connect(self._on_date_changed)
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_input)
        form_layout.addLayout(date_layout)
        
        # Mês da Simulação (read-only)
        month_layout = QVBoxLayout()
        month_layout.setSpacing(4)
        month_label = QLabel("Mês Simulação")
        month_label.setStyleSheet("font-weight: 500; color: #6B7280; font-size: 12px;")
        self.month_display = QLabel("Mês 0")
        self.month_display.setStyleSheet("""
            background-color: #F3F4F6;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            font-weight: 600;
            color: #3B82F6;
        """)
        self.month_display.setMinimumWidth(110)
        self.month_display.setAlignment(Qt.AlignCenter)
        month_layout.addWidget(month_label)
        month_layout.addWidget(self.month_display)
        form_layout.addLayout(month_layout)
        
        # Descrição
        desc_layout = QVBoxLayout()
        desc_layout.setSpacing(4)
        desc_label = QLabel("Evento (máx 35 chars)")
        desc_label.setStyleSheet("font-weight: 500; color: #374151; font-size: 12px;")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Ex: 13º Salário")
        self.desc_input.setMaxLength(35)
        self.desc_input.setMinimumWidth(180)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input)
        form_layout.addLayout(desc_layout)
        
        # Aporte Extra
        deposit_layout = QVBoxLayout()
        deposit_layout.setSpacing(4)
        deposit_label = QLabel("Aporte Extra (R$)")
        deposit_label.setStyleSheet("font-weight: 500; color: #10B981; font-size: 12px;")
        self.deposit_input = QDoubleSpinBox()
        self.deposit_input.setRange(0, 999999999)
        self.deposit_input.setDecimals(2)
        self.deposit_input.setPrefix("R$ ")
        self.deposit_input.setGroupSeparatorShown(True)
        self.deposit_input.setMinimumWidth(140)
        deposit_layout.addWidget(deposit_label)
        deposit_layout.addWidget(self.deposit_input)
        form_layout.addLayout(deposit_layout)
        
        # Resgate
        withdrawal_layout = QVBoxLayout()
        withdrawal_layout.setSpacing(4)
        withdrawal_label = QLabel("Resgate (R$)")
        withdrawal_label.setStyleSheet("font-weight: 500; color: #EF4444; font-size: 12px;")
        self.withdrawal_input = QDoubleSpinBox()
        self.withdrawal_input.setRange(0, 999999999)
        self.withdrawal_input.setDecimals(2)
        self.withdrawal_input.setPrefix("R$ ")
        self.withdrawal_input.setGroupSeparatorShown(True)
        self.withdrawal_input.setMinimumWidth(140)
        withdrawal_layout.addWidget(withdrawal_label)
        withdrawal_layout.addWidget(self.withdrawal_input)
        form_layout.addLayout(withdrawal_layout)
        
        # Botão Adicionar
        add_layout = QVBoxLayout()
        add_layout.setSpacing(4)
        add_layout.addWidget(QLabel(""))  # Espaçador
        btn_add = QPushButton("➕ Adicionar")
        btn_add.setObjectName("btn_primary")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self._add_event)
        add_layout.addWidget(btn_add)
        form_layout.addLayout(add_layout)
        
        parent_layout.addWidget(form_frame)
        
        # Atualizar mês inicial
        self._on_date_changed()
    
    def _on_date_changed(self):
        """Atualiza o display do mês da simulação quando a data muda."""
        qdate = self.date_input.date()
        event_date = date(qdate.year(), qdate.month(), qdate.day())
        
        months_diff = self._calculate_month_diff(event_date)
        
        if months_diff < 0:
            self.month_display.setText("❌ Anterior")
            self.month_display.setStyleSheet("""
                background-color: #FEE2E2;
                border: 1px solid #FECACA;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 600;
                color: #DC2626;
            """)
        elif months_diff >= self.simulation_months:
            self.month_display.setText("❌ Posterior")
            self.month_display.setStyleSheet("""
                background-color: #FEF3C7;
                border: 1px solid #FDE68A;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 600;
                color: #D97706;
            """)
        else:
            year = months_diff // 12
            month_in_year = months_diff % 12
            self.month_display.setText(f"Ano {year}, Mês {month_in_year}")
            self.month_display.setStyleSheet("""
                background-color: #ECFDF5;
                border: 1px solid #A7F3D0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 600;
                color: #059669;
            """)
    
    def _calculate_month_diff(self, event_date: date) -> int:
        """Calcula a diferença em meses entre a data do evento e a data de início."""
        return (event_date.year - self.start_date.year) * 12 + (event_date.month - self.start_date.month)
    
    def _create_events_table(self, parent_layout: QVBoxLayout):
        """Cria a tabela de eventos (sem coluna Ações - usar clique direito)."""
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            'Data', 'Mês Sim.', 'Evento', 'Aporte Extra', 'Resgate'
        ])
        
        # Configurar header
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        
        # Larguras otimizadas
        self.table.setColumnWidth(0, 110)   # Data - aumentada
        self.table.setColumnWidth(1, 100)   # Mês Sim. - aumentada
        self.table.setColumnWidth(3, 130)   # Aporte Extra
        self.table.setColumnWidth(4, 130)   # Resgate
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        # Habilitar menu de contexto para deletar
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Permitir deletar com tecla Delete
        self.table.keyPressEvent = self._table_key_press
        
        parent_layout.addWidget(self.table, stretch=1)
        
        # Dica
        hint_label = QLabel("💡 Clique direito ou tecla Del para remover evento")
        hint_label.setStyleSheet("font-size: 11px; color: #9CA3AF; font-style: italic; padding: 4px;")
        parent_layout.addWidget(hint_label)
    
    def _show_context_menu(self, position):
        """Mostra menu de contexto para deletar evento."""
        row = self.table.rowAt(position.y())
        if row < 0:
            return
        
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        menu = QMenu(self.table)
        delete_action = QAction("🗑️ Remover Evento", self.table)
        delete_action.triggered.connect(lambda: self._remove_event(row))
        menu.addAction(delete_action)
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def _table_key_press(self, event):
        """Trata teclas na tabela."""
        from PySide6.QtCore import Qt as QtCore
        from PySide6.QtWidgets import QTableWidget
        
        if event.key() in (QtCore.Key_Delete, QtCore.Key_Backspace):
            rows = set(item.row() for item in self.table.selectedItems())
            for row in sorted(rows, reverse=True):
                self._remove_event(row)
        else:
            QTableWidget.keyPressEvent(self.table, event)
    
    def _create_summary(self, parent_layout: QVBoxLayout):
        """Cria o resumo dos eventos."""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        summary_layout = QHBoxLayout(summary_frame)
        
        # Total de eventos
        self.lbl_count = QLabel("0 eventos")
        self.lbl_count.setStyleSheet("font-weight: 600; color: #1E40AF;")
        summary_layout.addWidget(self.lbl_count)
        
        summary_layout.addStretch()
        
        # Total aportes
        self.lbl_deposits = QLabel("Aportes: R$ 0,00")
        self.lbl_deposits.setStyleSheet("font-weight: 500; color: #059669;")
        summary_layout.addWidget(self.lbl_deposits)
        
        summary_layout.addWidget(QLabel(" | "))
        
        # Total resgates
        self.lbl_withdrawals = QLabel("Resgates: R$ 0,00")
        self.lbl_withdrawals.setStyleSheet("font-weight: 500; color: #DC2626;")
        summary_layout.addWidget(self.lbl_withdrawals)
        
        summary_layout.addWidget(QLabel(" | "))
        
        # Saldo líquido
        self.lbl_net = QLabel("Líquido: R$ 0,00")
        self.lbl_net.setStyleSheet("font-weight: 600; color: #1F2937;")
        summary_layout.addWidget(self.lbl_net)
        
        parent_layout.addWidget(summary_frame)
    
    def _create_action_buttons(self, parent_layout: QVBoxLayout):
        """Cria os botões de ação."""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # Importar CSV
        btn_import = QPushButton("📥 Carregar CSV")
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
        
        # Limpar tudo
        btn_clear = QPushButton("🗑️ Limpar Tudo")
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
        btn_confirm = QPushButton("✓ Confirmar Eventos")
        btn_confirm.setObjectName("btn_primary")
        btn_confirm.setCursor(Qt.PointingHandCursor)
        btn_confirm.clicked.connect(self._confirm)
        buttons_layout.addWidget(btn_confirm)
        
        parent_layout.addLayout(buttons_layout)
    
    def _add_event(self):
        """Adiciona um novo evento."""
        qdate = self.date_input.date()
        event_date = date(qdate.year(), qdate.month(), qdate.day())
        description = self.desc_input.text().strip()
        deposit = self.deposit_input.value()
        withdrawal = self.withdrawal_input.value()
        
        # Validação
        if not description:
            QMessageBox.warning(self, "Atenção", "Informe uma descrição para o evento.")
            return
        
        if deposit == 0 and withdrawal == 0:
            QMessageBox.warning(self, "Atenção", "Informe um valor de aporte ou resgate.")
            return
        
        # Verificar se está dentro do período
        months_diff = self._calculate_month_diff(event_date)
        if months_diff < 0:
            QMessageBox.warning(
                self, "Data Inválida", 
                f"A data do evento é anterior ao início da simulação ({self.start_date.strftime('%d/%m/%Y')})."
            )
            return
        
        if months_diff >= self.simulation_months:
            QMessageBox.warning(
                self, "Data Inválida", 
                f"A data do evento está além do período da simulação ({self.simulation_months // 12} anos)."
            )
            return
        
        # Criar evento
        event = ExtraordinaryEvent(
            date=event_date,
            description=description,
            deposit=deposit,
            withdrawal=withdrawal
        )
        
        self.events_manager.add_event(event)
        self._load_events()
        
        # Limpar formulário
        self.desc_input.clear()
        self.deposit_input.setValue(0)
        self.withdrawal_input.setValue(0)
    
    def _remove_event(self, index: int):
        """Remove um evento."""
        self.events_manager.remove_event(index)
        self._load_events()
    
    def _load_events(self):
        """Carrega eventos na tabela."""
        self.table.setRowCount(len(self.events_manager.events))
        
        for row, event in enumerate(self.events_manager.events):
            months_diff = self._calculate_month_diff(event.date)
            is_valid = 0 <= months_diff < self.simulation_months
            
            # Data
            date_item = QTableWidgetItem(event.date.strftime('%d/%m/%Y'))
            date_item.setTextAlignment(Qt.AlignCenter)
            if not is_valid:
                date_item.setForeground(QColor('#DC2626'))
            self.table.setItem(row, 0, date_item)
            
            # Mês da Simulação
            if is_valid:
                year = months_diff // 12
                month = months_diff % 12
                month_text = f"A{year}M{month}"
            else:
                month_text = "❌ Fora"
            
            month_item = QTableWidgetItem(month_text)
            month_item.setTextAlignment(Qt.AlignCenter)
            if not is_valid:
                month_item.setForeground(QColor('#DC2626'))
            else:
                month_item.setForeground(QColor('#3B82F6'))
            self.table.setItem(row, 1, month_item)
            
            # Descrição
            desc_item = QTableWidgetItem(event.description)
            self.table.setItem(row, 2, desc_item)
            
            # Aporte
            deposit_item = QTableWidgetItem(
                format_currency(event.deposit) if event.deposit > 0 else "—"
            )
            deposit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if event.deposit > 0:
                deposit_item.setForeground(QColor('#059669'))
            self.table.setItem(row, 3, deposit_item)
            
            # Resgate
            withdrawal_item = QTableWidgetItem(
                format_currency(event.withdrawal) if event.withdrawal > 0 else "—"
            )
            withdrawal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if event.withdrawal > 0:
                withdrawal_item.setForeground(QColor('#DC2626'))
            self.table.setItem(row, 4, withdrawal_item)
        
        self._update_summary()
    
    def _update_summary(self):
        """Atualiza o resumo."""
        # Filtrar apenas eventos válidos
        valid_count = 0
        valid_deposits = 0.0
        valid_withdrawals = 0.0
        
        for event in self.events_manager.events:
            months_diff = self._calculate_month_diff(event.date)
            if 0 <= months_diff < self.simulation_months:
                valid_count += 1
                valid_deposits += event.deposit
                valid_withdrawals += event.withdrawal
        
        net = valid_deposits - valid_withdrawals
        
        total_count = self.events_manager.count
        invalid_count = total_count - valid_count
        
        count_text = f"{valid_count} evento{'s' if valid_count != 1 else ''}"
        if invalid_count > 0:
            count_text += f" ({invalid_count} fora do período)"
        
        self.lbl_count.setText(count_text)
        self.lbl_deposits.setText(f"Aportes: {format_currency(valid_deposits)}")
        self.lbl_withdrawals.setText(f"Resgates: {format_currency(valid_withdrawals)}")
        
        net_color = '#059669' if net >= 0 else '#DC2626'
        self.lbl_net.setText(f"Líquido: {format_currency(net)}")
        self.lbl_net.setStyleSheet(f"font-weight: 600; color: {net_color};")
    
    def _import_csv(self):
        """Importa eventos de um arquivo CSV."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Carregar Eventos CSV",
            "", "Arquivos CSV (*.csv);;Todos os arquivos (*)"
        )
        
        if not filepath:
            return
        
        success, error, count = self.events_manager.import_from_csv(filepath)
        
        if success:
            self._load_events()
            QMessageBox.information(
                self, "Importação Concluída",
                f"{count} evento{'s' if count != 1 else ''} importado{'s' if count != 1 else ''} com sucesso!"
            )
        else:
            QMessageBox.critical(self, "Erro na Importação", error)
    
    def _export_csv(self):
        """Exporta eventos para CSV (sempre gera arquivo, mesmo vazio)."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exportar Eventos CSV",
            "eventos_extraordinarios.csv",
            "Arquivos CSV (*.csv);;Todos os arquivos (*)"
        )
        
        if not filepath:
            return
        
        if not filepath.lower().endswith('.csv'):
            filepath += '.csv'
        
        # Exportar mesmo se vazio (apenas cabeçalho)
        try:
            import csv
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['Data', 'Evento', 'Aporte Extra (R$)', 'Resgate (R$)'])
                
                for event in self.events_manager.events:
                    writer.writerow([
                        event.date.strftime('%d/%m/%Y'),
                        event.description,
                        f"{event.deposit:.2f}".replace('.', ',') if event.deposit > 0 else '',
                        f"{event.withdrawal:.2f}".replace('.', ',') if event.withdrawal > 0 else ''
                    ])
            
            msg = f"Eventos exportados para:\n{filepath}"
            if not self.events_manager.events:
                msg += "\n\n(Arquivo contém apenas cabeçalho)"
            
            QMessageBox.information(self, "Exportação Concluída", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro na Exportação", str(e))
    
    def _clear_all(self):
        """Limpa todos os eventos."""
        if not self.events_manager.events:
            return
        
        reply = QMessageBox.question(
            self, "Confirmar Limpeza",
            "Tem certeza que deseja remover todos os eventos?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.events_manager.clear()
            self._load_events()
    
    def _confirm(self):
        """Confirma os eventos e fecha o diálogo."""
        self.events_confirmed.emit(self.events_manager)
        self.accept()
    
    def get_events_manager(self) -> EventsManager:
        """Retorna o gerenciador de eventos."""
        return self.events_manager
