#!/usr/bin/env python3
"""
PyInvest - Simulador de Investimentos com Juros Compostos
=========================================================

Uma aplicação desktop moderna para simulação de investimentos,
desenvolvida com Python, PySide6 e Matplotlib.

Autor: Erasmo de Melo Gusmão
Versão: 1.0.0
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from ui.window import MainWindow


def main():
    """Função principal que inicializa a aplicação."""
    # Cria a aplicação Qt
    app = QApplication(sys.argv)
    
    # Configuração de fonte padrão
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Nome da aplicação (aparece em alguns ambientes)
    app.setApplicationName("PyInvest")
    app.setApplicationDisplayName("PyInvest - Simulador de Investimentos")
    
    # Cria e exibe a janela principal
    window = MainWindow()
    window.show()
    
    # Inicia o loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
