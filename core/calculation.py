"""
PyInvest - Módulo de Cálculos Financeiros
Contém a lógica de simulação de juros compostos.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List


@dataclass
class YearlyProjection:
    """Projeção anual do investimento."""
    year: int
    accumulated_contribution: float  # Aportes acumulados
    accumulated_interest: float      # Juros acumulados
    total_balance: float             # Saldo total
    goal_percentage: float           # % do objetivo atingido


@dataclass
class SimulationAnalysis:
    """Análise textual da simulação."""
    initial_investment: float
    monthly_contribution: float
    annual_rate: float
    final_balance: float
    total_interest: float
    total_invested: float
    years_to_goal: float             # Anos para atingir a meta
    total_return_percentage: float   # Rentabilidade total (%)
    goal_amount: float               # Valor da meta
    goal_achieved: bool              # Meta atingida?
    goal_percentage: float           # % da meta atingido


@dataclass
class SimulationResult:
    """Resultado completo da simulação de investimento."""
    # Dados mensais
    months: np.ndarray               # Array com os meses (0, 1, 2, ..., n)
    balances: np.ndarray             # Saldo acumulado mês a mês
    
    # Totais
    total_invested: float            # Total de aportes realizados
    total_interest: float            # Total de juros ganhos
    final_balance: float             # Valor final do investimento
    
    # Projeção anual
    yearly_projection: List[YearlyProjection] = field(default_factory=list)
    
    # Análise
    analysis: SimulationAnalysis = None


def calculate_compound_interest(
    initial_amount: float,
    monthly_contribution: float,
    annual_rate: float,
    years: int,
    goal_amount: float = 0
) -> SimulationResult:
    """
    Calcula a evolução de um investimento com juros compostos.
    
    Args:
        initial_amount: Montante inicial (R$)
        monthly_contribution: Aporte mensal (R$)
        annual_rate: Taxa de juros anual (%)
        years: Tempo de investimento em anos
        goal_amount: Meta de valor a atingir (R$) - opcional
    
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
    
    # Projeção anual
    yearly_projection = []
    for year in range(years + 1):
        month_index = year * 12
        acc_contribution = initial_amount + (monthly_contribution * month_index)
        acc_interest = balances[month_index] - acc_contribution
        goal_pct = (balances[month_index] / goal_amount * 100) if goal_amount > 0 else 0
        
        yearly_projection.append(YearlyProjection(
            year=year,
            accumulated_contribution=acc_contribution,
            accumulated_interest=acc_interest,
            total_balance=balances[month_index],
            goal_percentage=goal_pct
        ))
    
    # Calcular anos para atingir a meta
    years_to_goal = 0
    if goal_amount > 0 and monthly_rate > 0:
        # Encontrar o mês em que a meta é atingida
        goal_reached_month = None
        for i, balance in enumerate(balances):
            if balance >= goal_amount:
                goal_reached_month = i
                break
        
        if goal_reached_month is not None:
            years_to_goal = goal_reached_month / 12
        else:
            # Estimar usando fórmula (aproximação)
            years_to_goal = years * (goal_amount / final_balance) if final_balance > 0 else 0
    
    # Rentabilidade total
    total_return_pct = (total_interest / total_invested * 100) if total_invested > 0 else 0
    
    # Goal achievement
    goal_achieved = final_balance >= goal_amount if goal_amount > 0 else True
    goal_pct = (final_balance / goal_amount * 100) if goal_amount > 0 else 100
    
    # Criar análise
    analysis = SimulationAnalysis(
        initial_investment=initial_amount,
        monthly_contribution=monthly_contribution,
        annual_rate=annual_rate,
        final_balance=final_balance,
        total_interest=total_interest,
        total_invested=total_invested,
        years_to_goal=years_to_goal,
        total_return_percentage=total_return_pct,
        goal_amount=goal_amount,
        goal_achieved=goal_achieved,
        goal_percentage=goal_pct
    )
    
    return SimulationResult(
        months=months,
        balances=balances,
        total_invested=total_invested,
        total_interest=total_interest,
        final_balance=final_balance,
        yearly_projection=yearly_projection,
        analysis=analysis
    )


def format_currency(value: float) -> str:
    """Formata valor como moeda brasileira."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
