"""
PyInvest - Módulo de Cálculos Financeiros
Contém a lógica de simulação de juros compostos.
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class SimulationResult:
    """Resultado da simulação de investimento."""
    months: np.ndarray           # Array com os meses (0, 1, 2, ..., n)
    balances: np.ndarray         # Saldo acumulado mês a mês
    total_invested: float        # Total de aportes realizados
    total_interest: float        # Total de juros ganhos
    final_balance: float         # Valor final do investimento


def calculate_compound_interest(
    initial_amount: float,
    monthly_contribution: float,
    annual_rate: float,
    years: int
) -> SimulationResult:
    """
    Calcula a evolução de um investimento com juros compostos.
    
    Args:
        initial_amount: Montante inicial (R$)
        monthly_contribution: Aporte mensal (R$)
        annual_rate: Taxa de juros anual (%)
        years: Tempo de investimento em anos
    
    Returns:
        SimulationResult com todos os dados da simulação
    """
    # Converte taxa anual para mensal
    monthly_rate = (1 + annual_rate / 100) ** (1/12) - 1
    
    # Total de meses
    total_months = years * 12
    
    # Arrays para armazenar os resultados
    months = np.arange(total_months + 1)
    balances = np.zeros(total_months + 1)
    
    # Mês 0: apenas o montante inicial
    balances[0] = initial_amount
    
    # Cálculo mês a mês
    for month in range(1, total_months + 1):
        # Saldo anterior + juros + aporte mensal
        balances[month] = balances[month - 1] * (1 + monthly_rate) + monthly_contribution
    
    # Cálculos finais
    total_invested = initial_amount + (monthly_contribution * total_months)
    final_balance = balances[-1]
    total_interest = final_balance - total_invested
    
    return SimulationResult(
        months=months,
        balances=balances,
        total_invested=total_invested,
        total_interest=total_interest,
        final_balance=final_balance
    )


def format_currency(value: float) -> str:
    """Formata valor como moeda brasileira."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
