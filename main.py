#!/usr/bin/env python3
"""
PyInvest - Simulador de Investimentos com Juros Compostos
=========================================================

Uma aplicação desktop moderna para simulação de investimentos
com análise probabilística Monte Carlo.

Autor: PyInvest Team
Versão: 3.1.0 (Modern UI + Plotly Edition)
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# Janela moderna com Plotly
from ui.window_modern import ModernMainWindow


def main():
    """Função principal que inicializa a aplicação."""
    # Configurar DPI alto
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Cria a aplicação Qt
    app = QApplication(sys.argv)
    
    # Configuração de fonte padrão
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Nome da aplicação
    app.setApplicationName("PyInvest")
    app.setApplicationDisplayName("PyInvest - Simulador de Investimentos")
    
    # Cria e exibe a janela principal
    window = ModernMainWindow()
    window.show()
    
    # Inicia o loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
