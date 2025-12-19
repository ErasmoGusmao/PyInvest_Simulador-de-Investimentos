"""
PyInvest - Folha de Estilos QSS
Tema claro moderno inspirado em dashboards web financeiros.
"""

# Paleta de cores
COLORS = {
    'primary': '#16a085',           # Verde-água (botão principal)
    'primary_hover': '#1abc9c',     # Verde-água claro
    'secondary': '#6c757d',         # Cinza (botão secundário)
    'secondary_hover': '#5a6268',   # Cinza escuro
    
    'success': '#27ae60',           # Verde (lucro/juros)
    'info': '#2980b9',              # Azul (saldo final)
    'warning': '#f39c12',           # Laranja/amarelo (meta)
    'danger': '#e74c3c',            # Vermelho
    
    'bg_main': '#f4f6f9',           # Fundo principal
    'bg_card': '#ffffff',           # Fundo dos cards
    'bg_input': '#ffffff',          # Fundo dos inputs
    
    'text_primary': '#2c3e50',      # Texto principal
    'text_secondary': '#7f8c8d',    # Texto secundário
    'text_muted': '#95a5a6',        # Texto sutil
    
    'border': '#e0e0e0',            # Bordas
    'border_focus': '#16a085',      # Borda com foco
    
    'table_header': '#f8f9fa',      # Cabeçalho tabela
    'table_row_alt': '#f9fbfc',     # Linha alternada tabela
}


LIGHT_STYLE = """
/* ==========================================================================
   TEMA CLARO MODERNO - PyInvest
   ========================================================================== */

/* --- Base --- */
QMainWindow {
    background-color: #f4f6f9;
}

QWidget {
    background-color: #f4f6f9;
    color: #2c3e50;
    font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
    font-size: 13px;
}

QScrollArea {
    border: none;
    background-color: #f4f6f9;
}

QScrollBar:vertical {
    background-color: #f4f6f9;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* --- Cards / Frames --- */
QFrame#card {
    background-color: #ffffff;
    border-radius: 10px;
    border: 1px solid #e0e0e0;
}

QFrame#sidebar {
    background-color: #ffffff;
    border-radius: 12px;
    border: 1px solid #e0e0e0;
}

QFrame#results_panel {
    background-color: #ffffff;
    border-radius: 12px;
    border: 1px solid #e0e0e0;
}

/* --- Labels --- */
QLabel {
    color: #2c3e50;
    background-color: transparent;
}

QLabel#main_title {
    font-size: 28px;
    font-weight: bold;
    color: #2c3e50;
}

QLabel#main_subtitle {
    font-size: 14px;
    color: #7f8c8d;
}

QLabel#section_title {
    font-size: 18px;
    font-weight: bold;
    color: #16a085;
}

QLabel#card_title {
    font-size: 11px;
    font-weight: bold;
    color: #ffffff;
    text-transform: uppercase;
    letter-spacing: 1px;
}

QLabel#card_value {
    font-size: 22px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#input_label {
    font-size: 13px;
    font-weight: 500;
    color: #2c3e50;
    margin-bottom: 4px;
}

QLabel#analysis_text {
    font-size: 13px;
    color: #2c3e50;
    line-height: 1.6;
}

/* --- Inputs --- */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    color: #2c3e50;
    selection-background-color: #16a085;
}

QLineEdit:focus {
    border: 2px solid #16a085;
    padding: 11px 15px;
}

QLineEdit:hover {
    border: 1px solid #16a085;
}

QLineEdit::placeholder {
    color: #95a5a6;
}

/* --- Botões --- */
QPushButton#primary {
    background-color: #16a085;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 14px 24px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#primary:hover {
    background-color: #1abc9c;
}

QPushButton#primary:pressed {
    background-color: #0e7c61;
}

QPushButton#secondary {
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#secondary:hover {
    background-color: #5a6268;
}

QPushButton#secondary:pressed {
    background-color: #495057;
}

/* --- Cards de Resultado (cores específicas) --- */
QFrame#card_invested {
    background-color: #2c3e50;
    border-radius: 10px;
    border: none;
}

QFrame#card_interest {
    background-color: #27ae60;
    border-radius: 10px;
    border: none;
}

QFrame#card_final {
    background-color: #2980b9;
    border-radius: 10px;
    border: none;
}

QFrame#card_goal {
    background-color: #f39c12;
    border-radius: 10px;
    border: none;
}

/* --- Tabela --- */
QTableWidget {
    background-color: #ffffff;
    border: none;
    font-size: 13px;
}

QTableWidget::item {
    padding: 12px 20px;
    border-bottom: 1px solid #f0f0f0;
}

QTableWidget::item:selected {
    background-color: #e8f6f3;
    color: #2c3e50;
}

QHeaderView::section {
    background-color: #ffffff;
    color: #7f8c8d;
    font-weight: 600;
    font-size: 12px;
    padding: 14px 20px;
    border: none;
    border-bottom: 1px solid #e0e0e0;
    text-align: left;
}

/* --- Análise Box --- */
QFrame#analysis_box {
    background-color: #ffffff;
    border-left: 4px solid #16a085;
    border-radius: 0px 8px 8px 0px;
    padding: 15px;
}
"""


def get_style() -> str:
    """Retorna a folha de estilos completa."""
    return LIGHT_STYLE


def get_colors() -> dict:
    """Retorna o dicionário de cores."""
    return COLORS
