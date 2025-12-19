"""
PyInvest - Módulo de Cálculos Financeiros
Contém a lógica de simulação de juros compostos e Monte Carlo.
"""

import numpy as np
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


# =============================================================================
# DATA CLASSES - Estruturas de Dados
# =============================================================================

@dataclass
class ParameterRange:
    """Define um parâmetro com range de valores (Min, Det, Max)."""
    min_value: Optional[float] = None
    deterministic: Optional[float] = None
    max_value: Optional[float] = None
    
    def is_range_defined(self) -> bool:
        """Verifica se o range (min/max) está definido."""
        return self.min_value is not None and self.max_value is not None
    
    def get_deterministic_value(self) -> float:
        """Retorna o valor determinístico ou a média do range."""
        if self.deterministic is not None:
            return self.deterministic
        if self.is_range_defined():
            return (self.min_value + self.max_value) / 2
        return 0.0
    
    def get_mean(self) -> float:
        """Retorna a média do range."""
        if self.is_range_defined():
            return (self.min_value + self.max_value) / 2
        return self.get_deterministic_value()
    
    def get_std(self) -> float:
        """Retorna o desvio padrão estimado (range / 6 para ~99.7% cobertura)."""
        if self.is_range_defined():
            return (self.max_value - self.min_value) / 6
        return 0.0
    
    def validate(self) -> Tuple[bool, str]:
        """
        Valida o parâmetro.
        
        Returns:
            Tuple (is_valid, error_message)
        """
        # Se nenhum valor preenchido
        if self.min_value is None and self.deterministic is None and self.max_value is None:
            return False, "Pelo menos um valor deve ser preenchido."
        
        # Se apenas determinístico preenchido - OK
        if self.deterministic is not None and self.min_value is None and self.max_value is None:
            return True, ""
        
        # Se min ou max preenchido, ambos devem estar
        if (self.min_value is not None) != (self.max_value is not None):
            return False, "Se Min ou Max for preenchido, ambos devem ser informados."
        
        # Se range definido, validar lógica
        if self.is_range_defined():
            if self.min_value > self.max_value:
                return False, "Valor Mínimo não pode ser maior que Máximo."
            
            # Se determinístico preenchido, deve estar no range
            if self.deterministic is not None:
                if self.deterministic < self.min_value or self.deterministic > self.max_value:
                    return False, "Valor Determinístico deve estar entre Min e Max."
        
        return True, ""


@dataclass
class SimulationParameters:
    """Parâmetros completos para simulação."""
    initial_amount: ParameterRange
    monthly_contribution: ParameterRange
    annual_rate: ParameterRange
    years: int  # Período não tem range (sempre determinístico)
    goal_amount: float = 0
    num_simulations: int = 5000
    
    def validate_all(self) -> Tuple[bool, List[str]]:
        """Valida todos os parâmetros."""
        errors = []
        
        # Validar cada parâmetro com range
        params = [
            ("Capital Inicial", self.initial_amount),
            ("Aporte Mensal", self.monthly_contribution),
            ("Rentabilidade Anual", self.annual_rate),
        ]
        
        for name, param in params:
            is_valid, error = param.validate()
            if not is_valid:
                errors.append(f"{name}: {error}")
        
        # Validar período
        if self.years <= 0:
            errors.append("Período deve ser maior que zero.")
        
        # Validar número de simulações
        if self.num_simulations < 100:
            errors.append("Número de simulações deve ser pelo menos 100.")
        
        return len(errors) == 0, errors
    
    def has_any_range(self) -> bool:
        """Verifica se algum parâmetro tem range definido."""
        return (
            self.initial_amount.is_range_defined() or
            self.monthly_contribution.is_range_defined() or
            self.annual_rate.is_range_defined()
        )


@dataclass
class YearlyProjection:
    """Projeção anual do investimento."""
    year: int
    accumulated_contribution: float
    accumulated_interest: float
    total_balance: float
    goal_percentage: float
    
    # Campos Monte Carlo (opcionais)
    balance_mean: Optional[float] = None
    balance_min: Optional[float] = None
    balance_max: Optional[float] = None


@dataclass
class SimulationAnalysis:
    """Análise textual da simulação."""
    initial_investment: float
    monthly_contribution: float
    annual_rate: float
    final_balance: float
    total_interest: float
    total_invested: float
    years_to_goal: float
    total_return_percentage: float
    goal_amount: float
    goal_achieved: bool
    goal_percentage: float


@dataclass
class MonteCarloResult:
    """Resultado específico da simulação Monte Carlo."""
    # Dados mensais agregados
    mean_balances: np.ndarray      # Média dos saldos mês a mês
    min_balances: np.ndarray       # Mínimo (pior cenário)
    max_balances: np.ndarray       # Máximo (melhor cenário)
    std_balances: np.ndarray       # Desvio padrão
    
    # Percentis
    p5_balances: np.ndarray        # Percentil 5%
    p25_balances: np.ndarray       # Percentil 25%
    p75_balances: np.ndarray       # Percentil 75%
    p95_balances: np.ndarray       # Percentil 95%
    
    # Estatísticas finais
    final_mean: float
    final_std: float
    final_min: float
    final_max: float
    
    # Número de simulações executadas
    num_simulations: int


@dataclass
class SimulationResult:
    """Resultado completo da simulação de investimento."""
    # Dados mensais (determinístico)
    months: np.ndarray
    balances: np.ndarray           # Saldo determinístico mês a mês
    
    # Totais
    total_invested: float
    total_interest: float
    final_balance: float
    
    # Projeção anual
    yearly_projection: List[YearlyProjection] = field(default_factory=list)
    
    # Análise
    analysis: SimulationAnalysis = None
    
    # Monte Carlo (opcional)
    monte_carlo: Optional[MonteCarloResult] = None
    
    @property
    def has_monte_carlo(self) -> bool:
        return self.monte_carlo is not None


# =============================================================================
# MOTOR DE CÁLCULO
# =============================================================================

def calculate_compound_interest_vectorized(
    initial_amount: np.ndarray,
    monthly_contribution: np.ndarray,
    annual_rate: np.ndarray,
    total_months: int
) -> np.ndarray:
    """
    Calcula juros compostos de forma vetorizada para múltiplos cenários.
    
    Args:
        initial_amount: Array de capitais iniciais (n_simulations,)
        monthly_contribution: Array de aportes mensais (n_simulations,)
        annual_rate: Array de taxas anuais em % (n_simulations,)
        total_months: Número total de meses
    
    Returns:
        Matriz de saldos (n_simulations, total_months + 1)
    """
    n_simulations = len(initial_amount)
    
    # Converter taxa anual para mensal
    monthly_rate = (1 + annual_rate / 100) ** (1/12) - 1
    
    # Matriz de resultados: (simulações, meses)
    balances = np.zeros((n_simulations, total_months + 1))
    
    # Mês 0: capital inicial
    balances[:, 0] = initial_amount
    
    # Cálculo vetorizado mês a mês
    for month in range(1, total_months + 1):
        balances[:, month] = (
            balances[:, month - 1] * (1 + monthly_rate) + monthly_contribution
        )
    
    return balances


def run_monte_carlo_simulation(
    params: SimulationParameters,
    seed: Optional[int] = None
) -> MonteCarloResult:
    """
    Executa simulação Monte Carlo vetorizada.
    
    Args:
        params: Parâmetros da simulação
        seed: Semente para reprodutibilidade (opcional)
    
    Returns:
        MonteCarloResult com estatísticas agregadas
    """
    if seed is not None:
        np.random.seed(seed)
    
    n_sim = params.num_simulations
    total_months = params.years * 12
    
    # Gerar amostras para cada parâmetro com range
    def sample_parameter(param: ParameterRange, n: int) -> np.ndarray:
        if param.is_range_defined():
            # Distribuição normal truncada aproximada
            mean = param.get_mean()
            std = param.get_std()
            samples = np.random.normal(mean, std, n)
            # Truncar nos limites
            samples = np.clip(samples, param.min_value, param.max_value)
            return samples
        else:
            # Valor fixo
            return np.full(n, param.get_deterministic_value())
    
    # Amostrar parâmetros
    initial_samples = sample_parameter(params.initial_amount, n_sim)
    monthly_samples = sample_parameter(params.monthly_contribution, n_sim)
    rate_samples = sample_parameter(params.annual_rate, n_sim)
    
    # Garantir valores não-negativos
    initial_samples = np.maximum(initial_samples, 0)
    monthly_samples = np.maximum(monthly_samples, 0)
    rate_samples = np.maximum(rate_samples, 0)
    
    # Executar simulação vetorizada
    all_balances = calculate_compound_interest_vectorized(
        initial_samples,
        monthly_samples,
        rate_samples,
        total_months
    )
    
    # Calcular estatísticas agregadas
    mean_balances = np.mean(all_balances, axis=0)
    std_balances = np.std(all_balances, axis=0)
    min_balances = np.min(all_balances, axis=0)
    max_balances = np.max(all_balances, axis=0)
    
    # Percentis
    p5_balances = np.percentile(all_balances, 5, axis=0)
    p25_balances = np.percentile(all_balances, 25, axis=0)
    p75_balances = np.percentile(all_balances, 75, axis=0)
    p95_balances = np.percentile(all_balances, 95, axis=0)
    
    # Estatísticas finais
    final_values = all_balances[:, -1]
    
    return MonteCarloResult(
        mean_balances=mean_balances,
        min_balances=min_balances,
        max_balances=max_balances,
        std_balances=std_balances,
        p5_balances=p5_balances,
        p25_balances=p25_balances,
        p75_balances=p75_balances,
        p95_balances=p95_balances,
        final_mean=np.mean(final_values),
        final_std=np.std(final_values),
        final_min=np.min(final_values),
        final_max=np.max(final_values),
        num_simulations=n_sim
    )


def calculate_deterministic(
    initial_amount: float,
    monthly_contribution: float,
    annual_rate: float,
    years: int,
    goal_amount: float = 0
) -> Tuple[np.ndarray, np.ndarray, List[YearlyProjection], SimulationAnalysis]:
    """
    Calcula simulação determinística (cenário base).
    
    Returns:
        Tuple (months, balances, yearly_projection, analysis)
    """
    # Converter taxa anual para mensal
    monthly_rate = (1 + annual_rate / 100) ** (1/12) - 1
    
    total_months = years * 12
    
    # Arrays
    months = np.arange(total_months + 1)
    balances = np.zeros(total_months + 1)
    
    # Mês 0
    balances[0] = initial_amount
    
    # Cálculo mês a mês
    for month in range(1, total_months + 1):
        balances[month] = balances[month - 1] * (1 + monthly_rate) + monthly_contribution
    
    # Totais
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
    
    # Anos para meta
    years_to_goal = 0
    if goal_amount > 0 and monthly_rate > 0:
        goal_reached_month = None
        for i, balance in enumerate(balances):
            if balance >= goal_amount:
                goal_reached_month = i
                break
        
        if goal_reached_month is not None:
            years_to_goal = goal_reached_month / 12
        else:
            years_to_goal = years * (goal_amount / final_balance) if final_balance > 0 else 0
    
    # Rentabilidade
    total_return_pct = (total_interest / total_invested * 100) if total_invested > 0 else 0
    
    # Meta
    goal_achieved = final_balance >= goal_amount if goal_amount > 0 else True
    goal_pct = (final_balance / goal_amount * 100) if goal_amount > 0 else 100
    
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
    
    return months, balances, yearly_projection, analysis


def run_full_simulation(params: SimulationParameters) -> SimulationResult:
    """
    Executa simulação completa (determinística + Monte Carlo se aplicável).
    
    Args:
        params: Parâmetros da simulação
    
    Returns:
        SimulationResult completo
    """
    # Valores determinísticos
    det_initial = params.initial_amount.get_deterministic_value()
    det_monthly = params.monthly_contribution.get_deterministic_value()
    det_rate = params.annual_rate.get_deterministic_value()
    
    # Simulação determinística
    months, balances, yearly_proj, analysis = calculate_deterministic(
        det_initial,
        det_monthly,
        det_rate,
        params.years,
        params.goal_amount
    )
    
    # Monte Carlo se houver ranges definidos
    monte_carlo = None
    if params.has_any_range():
        monte_carlo = run_monte_carlo_simulation(params)
        
        # Atualizar projeção anual com dados Monte Carlo
        for i, proj in enumerate(yearly_proj):
            month_idx = proj.year * 12
            proj.balance_mean = monte_carlo.mean_balances[month_idx]
            proj.balance_min = monte_carlo.min_balances[month_idx]
            proj.balance_max = monte_carlo.max_balances[month_idx]
    
    # Totais
    total_invested = det_initial + (det_monthly * params.years * 12)
    
    return SimulationResult(
        months=months,
        balances=balances,
        total_invested=total_invested,
        total_interest=balances[-1] - total_invested,
        final_balance=balances[-1],
        yearly_projection=yearly_proj,
        analysis=analysis,
        monte_carlo=monte_carlo
    )


# =============================================================================
# FUNÇÃO LEGADA (compatibilidade)
# =============================================================================

def calculate_compound_interest(
    initial_amount: float,
    monthly_contribution: float,
    annual_rate: float,
    years: int,
    goal_amount: float = 0
) -> SimulationResult:
    """
    Função legada para compatibilidade.
    Executa apenas simulação determinística.
    """
    params = SimulationParameters(
        initial_amount=ParameterRange(deterministic=initial_amount),
        monthly_contribution=ParameterRange(deterministic=monthly_contribution),
        annual_rate=ParameterRange(deterministic=annual_rate),
        years=years,
        goal_amount=goal_amount,
        num_simulations=1000
    )
    
    return run_full_simulation(params)


# =============================================================================
# UTILITÁRIOS
# =============================================================================

def format_currency(value: float) -> str:
    """Formata valor como moeda brasileira."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# =============================================================================
# ANÁLISE DE SENSIBILIDADE (Marginalidade)
# =============================================================================

@dataclass
class SensitivityMetrics:
    """Métricas de sensibilidade do investimento."""
    velocidade: float
    potencia_aporte: float
    eficiencia_capital: float
    sensibilidade_taxa: float


class InvestmentCalculator:
    """Calculadora de sensibilidade para investimentos."""
    
    def __init__(self, C: float, i_anual: float, t_anos: float, a_mensal: float):
        self.C = C
        self.i = i_anual / 100.0
        self.t = t_anos
        self.a_anual = a_mensal * 12
        
        if self.i <= 0:
            self.i = 0.000001

    def calculate_total_amount(self) -> float:
        juros_capital = self.C * math.pow(1 + self.i, self.t)
        juros_aportes = self.a_anual * ((math.pow(1 + self.i, self.t) - 1) / self.i)
        return juros_capital + juros_aportes

    def get_sensitivities(self) -> SensitivityMetrics:
        fator_acum = math.pow(1 + self.i, self.t)
        ln_i = math.log(1 + self.i)
        
        velocidade = ln_i * fator_acum * (self.C + (self.a_anual / self.i))
        potencia_aporte = (fator_acum - 1) / self.i
        eficiencia_cap = fator_acum
        
        termo_c = self.C * self.t * math.pow(1 + self.i, self.t - 1)
        num_a = (self.t * self.i * math.pow(1 + self.i, self.t - 1)) - fator_acum + 1
        termo_a = self.a_anual * (num_a / (self.i ** 2))
        sensib_taxa = termo_c + termo_a

        return SensitivityMetrics(
            velocidade=velocidade,
            potencia_aporte=potencia_aporte,
            eficiencia_capital=eficiencia_cap,
            sensibilidade_taxa=sensib_taxa
        )
