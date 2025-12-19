"""
PyInvest - Estilos Modernos (Flat Design)
Tema visual limpo com cards, sombras suaves e tipografia moderna.
"""


def get_colors():
    """Paleta de cores moderna."""
    return {
        # Cores principais
        'primary': '#10B981',        # Verde moderno (Emerald)
        'primary_hover': '#059669',  # Verde escuro
        'primary_light': '#D1FAE5',  # Verde claro
        
        # Secundárias
        'secondary': '#3B82F6',      # Azul
        'secondary_hover': '#2563EB',
        
        # Status
        'success': '#10B981',
        'warning': '#F59E0B',
        'danger': '#EF4444',
        'info': '#3B82F6',
        
        # Neutros
        'dark': '#1F2937',           # Cinza escuro (texto)
        'gray': '#6B7280',           # Cinza médio
        'gray_light': '#9CA3AF',     # Cinza claro
        'border': '#E5E7EB',         # Borda
        'background': '#E8EDF3',     # Fundo geral (CORRIGIDO: mais escuro)
        'card': '#FFFFFF',           # Fundo de cards (branco)
        
        # Gráficos
        'chart_primary': '#10B981',
        'chart_secondary': '#EF4444',
        'chart_tertiary': '#3B82F6',
        'chart_area': 'rgba(59, 130, 246, 0.1)',
    }


def get_modern_style():
    """Retorna o stylesheet moderno completo."""
    colors = get_colors()
    
    return f"""
    /* ============================================
       RESET E BASE
       ============================================ */
    
    QMainWindow {{
        background-color: {colors['background']};
    }}
    
    QScrollArea {{
        background-color: {colors['background']};
        border: none;
    }}
    
    QScrollArea > QWidget > QWidget {{
        background-color: {colors['background']};
    }}
    
    /* Container principal também com fundo */
    QWidget#central_container {{
        background-color: {colors['background']};
    }}
    
    QWidget {{
        font-family: 'Segoe UI', 'Roboto', 'SF Pro Display', sans-serif;
        font-size: 14px;
        color: {colors['dark']};
    }}
    
    /* ============================================
       CARDS E CONTAINERS
       ============================================ */
    
    QFrame#card, QFrame#input_card, QFrame#results_card {{
        background-color: {colors['card']};
        border: 1px solid {colors['border']};
        border-radius: 16px;
        padding: 24px;
    }}
    
    QFrame#panel {{
        background-color: {colors['card']};
        border: 1px solid {colors['border']};
        border-radius: 16px;
    }}
    
    QFrame#header_card {{
        background-color: {colors['card']};
        border: 1px solid {colors['border']};
        border-radius: 16px;
        padding: 20px;
    }}
    
    /* ============================================
       TIPOGRAFIA
       ============================================ */
    
    QLabel#main_title {{
        font-size: 28px;
        font-weight: 700;
        color: {colors['dark']};
        background: transparent;
        letter-spacing: -0.5px;
    }}
    
    QLabel#main_subtitle {{
        font-size: 15px;
        font-weight: 400;
        color: {colors['gray']};
        background: transparent;
    }}
    
    QLabel#section_title {{
        font-size: 18px;
        font-weight: 600;
        color: {colors['dark']};
        background: transparent;
        margin-bottom: 8px;
    }}
    
    QLabel#field_label {{
        font-size: 14px;
        font-weight: 500;
        color: {colors['dark']};
        background: transparent;
        margin-bottom: 4px;
    }}
    
    QLabel#help_text {{
        font-size: 12px;
        font-weight: 400;
        color: {colors['gray_light']};
        background: transparent;
        font-style: italic;
    }}
    
    /* ============================================
       INPUTS
       ============================================ */
    
    QLineEdit {{
        background-color: {colors['card']};
        border: 2px solid {colors['border']};
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 14px;
        font-weight: 500;
        color: {colors['dark']};
        min-height: 20px;
    }}
    
    QLineEdit:focus {{
        border-color: {colors['primary']};
        background-color: #FFFFFF;
    }}
    
    QLineEdit:hover {{
        border-color: {colors['gray_light']};
    }}
    
    QLineEdit::placeholder {{
        color: {colors['gray_light']};
        font-weight: 400;
    }}
    
    QSpinBox {{
        background-color: {colors['card']};
        border: 2px solid {colors['border']};
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 14px;
        font-weight: 500;
        color: {colors['dark']};
        min-height: 20px;
    }}
    
    QSpinBox:focus {{
        border-color: {colors['primary']};
    }}
    
    QSpinBox::up-button, QSpinBox::down-button {{
        width: 24px;
        border: none;
        background: transparent;
    }}
    
    /* ============================================
       BOTÕES
       ============================================ */
    
    QPushButton#btn_primary {{
        background-color: {colors['primary']};
        color: white;
        border: none;
        border-radius: 12px;
        padding: 16px 32px;
        font-size: 15px;
        font-weight: 600;
        min-height: 24px;
    }}
    
    QPushButton#btn_primary:hover {{
        background-color: {colors['primary_hover']};
    }}
    
    QPushButton#btn_primary:pressed {{
        background-color: #047857;
    }}
    
    QPushButton#btn_secondary {{
        background-color: transparent;
        color: {colors['gray']};
        border: 2px solid {colors['border']};
        border-radius: 12px;
        padding: 14px 28px;
        font-size: 14px;
        font-weight: 500;
        min-height: 20px;
    }}
    
    QPushButton#btn_secondary:hover {{
        background-color: {colors['background']};
        border-color: {colors['gray_light']};
        color: {colors['dark']};
    }}
    
    QPushButton#btn_export {{
        background-color: {colors['secondary']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 13px;
        font-weight: 500;
    }}
    
    QPushButton#btn_export:hover {{
        background-color: {colors['secondary_hover']};
    }}
    
    /* ============================================
       CARDS DE RESUMO (Summary Cards)
       ============================================ */
    
    QFrame#card_invested {{
        background-color: #1F2937;
        border: none;
        border-radius: 12px;
    }}
    
    QFrame#card_interest {{
        background-color: {colors['primary']};
        border: none;
        border-radius: 12px;
    }}
    
    QFrame#card_final {{
        background-color: {colors['secondary']};
        border: none;
        border-radius: 12px;
    }}
    
    QFrame#card_goal {{
        background-color: {colors['warning']};
        border: none;
        border-radius: 12px;
    }}
    
    QLabel#card_title {{
        font-size: 11px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.8);
        text-transform: uppercase;
        letter-spacing: 1px;
        background: transparent;
    }}
    
    QLabel#card_value {{
        font-size: 22px;
        font-weight: 700;
        color: white;
        background: transparent;
    }}
    
    /* ============================================
       GROUP BOX (Monte Carlo Config)
       ============================================ */
    
    QGroupBox {{
        font-weight: 600;
        font-size: 13px;
        color: {colors['dark']};
        border: 2px solid {colors['border']};
        border-radius: 12px;
        margin-top: 16px;
        padding: 20px 16px 16px 16px;
        background-color: {colors['background']};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
        background-color: {colors['background']};
    }}
    
    /* ============================================
       PROGRESS BAR
       ============================================ */
    
    QProgressBar {{
        border: none;
        border-radius: 6px;
        background-color: {colors['border']};
        height: 8px;
        text-align: center;
    }}
    
    QProgressBar::chunk {{
        background-color: {colors['primary']};
        border-radius: 6px;
    }}
    
    /* ============================================
       TABELA
       ============================================ */
    
    QTableWidget {{
        background-color: {colors['card']};
        border: 1px solid {colors['border']};
        border-radius: 12px;
        gridline-color: {colors['border']};
        font-size: 13px;
    }}
    
    QTableWidget::item {{
        padding: 12px 16px;
        border-bottom: 1px solid {colors['border']};
    }}
    
    QTableWidget::item:selected {{
        background-color: {colors['primary_light']};
        color: {colors['dark']};
    }}
    
    QHeaderView::section {{
        background-color: {colors['background']};
        color: {colors['gray']};
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 14px 16px;
        border: none;
        border-bottom: 2px solid {colors['border']};
    }}
    
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {colors['gray_light']};
        border-radius: 4px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {colors['gray']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    /* ============================================
       ANALYSIS BOX
       ============================================ */
    
    QFrame#analysis_box {{
        background-color: {colors['primary_light']};
        border-left: 4px solid {colors['primary']};
        border-radius: 0px 12px 12px 0px;
        padding: 16px 20px;
    }}
    
    QFrame#mc_summary {{
        background-color: rgba(59, 130, 246, 0.1);
        border-left: 4px solid {colors['secondary']};
        border-radius: 0px 12px 12px 0px;
        padding: 16px 20px;
    }}
    
    /* ============================================
       SEPARADORES
       ============================================ */
    
    QFrame#separator {{
        background-color: {colors['border']};
        max-height: 1px;
        margin: 8px 0;
    }}
    """


def get_shadow_effect():
    """Retorna configuração de sombra para cards."""
    from PySide6.QtWidgets import QGraphicsDropShadowEffect
    from PySide6.QtGui import QColor
    from PySide6.QtCore import Qt
    
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(20)
    shadow.setXOffset(0)
    shadow.setYOffset(4)
    shadow.setColor(QColor(0, 0, 0, 25))
    return shadow


def apply_shadow(widget):
    """Aplica sombra suave a um widget."""
    shadow = get_shadow_effect()
    widget.setGraphicsEffect(shadow)
