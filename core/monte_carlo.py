"""
PyInvest - Motor de Simulação Monte Carlo
Implementa análise probabilística vetorizada com NumPy.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict
from enum import Enum
from datetime import date


class DistributionType(Enum):
    """Tipo de distribuição para amostragem."""
    NORMAL = "normal"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"


@dataclass
class ParameterRange:
    """
    Define um parâmetro com range de incerteza.
    
    Regras de Validação:
    - Se min e max definidos: deterministic deve estar entre eles
    - min <= deterministic <= max
    - Não pode ter preenchimento parcial inválido
    """
    min_value: Optional[float] = None
    deterministic: Optional[float] = None
    max_value: Optional[float] = None
    
    def validate(self) -> Tuple[bool, str]:
        """
        Valida o range do parâmetro.
        
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        has_min = self.min_value is not None
        has_det = self.deterministic is not None
        has_max = self.max_value is not None
        
        # Caso 1: Nenhum valor preenchido
        if not has_min and not has_det and not has_max:
            return False, "Pelo menos um valor deve ser preenchido."
        
        # Caso 2: Apenas determinístico (válido - cenário simples)
        if has_det and not has_min and not has_max:
            return True, ""
        
        # Caso 3: Preenchimento parcial inválido (Min + Det sem Max, ou Max + Det sem Min)
        if has_min and has_det and not has_max:
            return False, "Se informar Mínimo e Determinístico, deve informar também o Máximo."
        
        if has_max and has_det and not has_min:
            return False, "Se informar Máximo e Determinístico, deve informar também o Mínimo."
        
        if has_min and not has_det and not has_max:
            return False, "Não pode informar apenas o Mínimo. Informe também o Máximo ou use o Determinístico."
        
        if has_max and not has_det and not has_min:
            return False, "Não pode informar apenas o Máximo. Informe também o Mínimo ou use o Determinístico."
        
        # Caso 4: Min e Max definidos (com ou sem Det)
        if has_min and has_max:
            if self.min_value > self.max_value:
                return False, f"Mínimo ({self.min_value}) não pode ser maior que Máximo ({self.max_value})."
            
            if self.min_value == self.max_value:
                return False, "Mínimo e Máximo não podem ser iguais. Use o valor Determinístico."
            
            # Se tem determinístico, validar se está no range
            if has_det:
                if self.deterministic < self.min_value:
                    return False, f"Determinístico ({self.deterministic}) está abaixo do Mínimo ({self.min_value})."
                if self.deterministic > self.max_value:
                    return False, f"Determinístico ({self.deterministic}) está acima do Máximo ({self.max_value})."
        
        return True, ""
    
    def is_probabilistic(self) -> bool:
        """Verifica se este parâmetro tem range para simulação."""
        return self.min_value is not None and self.max_value is not None
    
    def get_deterministic_value(self) -> float:
        """
        Retorna o valor determinístico para cálculo simples.
        Se não definido, usa a média do range.
        """
        if self.deterministic is not None:
            return self.deterministic
        elif self.min_value is not None and self.max_value is not None:
            return (self.min_value + self.max_value) / 2
        else:
            raise ValueError("Parâmetro não possui valor válido.")
    
    def sample(self, n_samples: int, distribution: DistributionType = DistributionType.NORMAL) -> np.ndarray:
        """
        Gera amostras aleatórias para o parâmetro.
        
        Args:
            n_samples: Número de amostras
            distribution: Tipo de distribuição
            
        Returns:
            Array com n_samples valores
        """
        if not self.is_probabilistic():
            # Retorna valor fixo
            return np.full(n_samples, self.get_deterministic_value())
        
        if distribution == DistributionType.NORMAL:
            # Distribuição Normal: μ = média, σ = (max-min)/6
            mu = (self.min_value + self.max_value) / 2
            sigma = (self.max_value - self.min_value) / 6
            samples = np.random.normal(mu, sigma, n_samples)
            # Clip para garantir limites
            return np.clip(samples, self.min_value, self.max_value)
        
        elif distribution == DistributionType.UNIFORM:
            return np.random.uniform(self.min_value, self.max_value, n_samples)
        
        elif distribution == DistributionType.TRIANGULAR:
            mode = self.deterministic if self.deterministic else (self.min_value + self.max_value) / 2
            return np.random.triangular(self.min_value, mode, self.max_value, n_samples)
        
        else:
            raise ValueError(f"Distribuição não suportada: {distribution}")


@dataclass
class MonteCarloInput:
    """Parâmetros de entrada para simulação Monte Carlo."""
    capital_inicial: ParameterRange
    aporte_mensal: ParameterRange
    rentabilidade_anual: ParameterRange
    periodo_anos: int  # Período sempre fixo
    meta: float = 0.0
    n_simulations: int = 5000
    start_date: date = field(default_factory=date.today)
    events_manager: object = None  # EventsManager (evita import circular)
    
    def validate_all(self) -> Tuple[bool, List[str]]:
        """
        Valida todos os parâmetros.
        
        Returns:
            Tuple[bool, List[str]]: (todos_válidos, lista_erros)
        """
        errors = []
        
        # Validar cada parâmetro
        params = [
            ("Capital Inicial", self.capital_inicial),
            ("Aporte Mensal", self.aporte_mensal),
            ("Rentabilidade Anual", self.rentabilidade_anual),
        ]
        
        for name, param in params:
            is_valid, error_msg = param.validate()
            if not is_valid:
                errors.append(f"{name}: {error_msg}")
        
        # Validar período
        if self.periodo_anos <= 0:
            errors.append("Período: deve ser maior que zero.")
        
        # Validar número de simulações
        if self.n_simulations < 100:
            errors.append("Número de simulações: deve ser pelo menos 100.")
        if self.n_simulations > 100000:
            errors.append("Número de simulações: máximo permitido é 100.000.")
        
        return len(errors) == 0, errors
    
    def has_probabilistic_params(self) -> bool:
        """Verifica se há parâmetros com range para Monte Carlo."""
        return (
            self.capital_inicial.is_probabilistic() or
            self.aporte_mensal.is_probabilistic() or
            self.rentabilidade_anual.is_probabilistic()
        )


@dataclass
class RepresentativeScenario:
    """
    Cenário representativo de um percentil específico.
    Contém os parâmetros REAIS que foram usados na simulação Monte Carlo
    e que geraram um saldo final próximo ao percentil desejado.
    """
    scenario_name: str          # "P5 (Pessimista)", "P50 (Mediana)", etc.
    percentile: str             # "P5", "P25", "P50", "P75", "P95"
    capital_inicial: float      # Valor REAL usado nesta simulação
    aporte_mensal: float        # Valor REAL usado nesta simulação
    rentabilidade_anual: float  # Taxa REAL usada nesta simulação
    saldo_final: float          # Resultado desta simulação
    scenario_type: str          # "Worst Case", "Típico", "Best Case", etc.


@dataclass
class YearlyProjectionMC:
    """Projeção anual com dados de Monte Carlo."""
    year: int
    total_invested: float
    balance_deterministic: float
    balance_mean: float
    balance_median: float       # Mediana (P50)
    balance_mode: float         # Moda (valor mais frequente)
    balance_min: float
    balance_max: float
    balance_p5: float           # Percentil 5
    balance_p10: float          # Percentil 10
    balance_p90: float          # Percentil 90
    balance_p95: float = 0.0    # Percentil 95 (IC 90% superior)
    extra_deposits: float = 0.0   # Aportes extras no ano
    withdrawals: float = 0.0      # Resgates no ano


@dataclass
class MonteCarloResult:
    """Resultado completo da simulação Monte Carlo."""
    # Dados mensais - Determinístico
    months: np.ndarray
    balances_deterministic: np.ndarray
    
    # Dados mensais - Monte Carlo (agregados)
    balances_mean: np.ndarray      # Média das simulações
    balances_min: np.ndarray       # Mínimo (pior cenário)
    balances_max: np.ndarray       # Máximo (melhor cenário)
    balances_p10: np.ndarray       # Percentil 10
    balances_p90: np.ndarray       # Percentil 90
    balances_p5: np.ndarray        # IC 90% inferior (P5)
    balances_p95: np.ndarray       # IC 90% superior (P95)
    
    # Totais Determinísticos
    total_invested: float
    total_interest_det: float
    final_balance_det: float
    
    # Totais Monte Carlo
    final_balance_mean: float
    final_balance_min: float
    final_balance_max: float
    
    # Projeção anual (com default)
    yearly_projection: List[YearlyProjectionMC] = field(default_factory=list)
    
    # Metadados (com default)
    n_simulations: int = 5000
    has_monte_carlo: bool = False
    
    # Parâmetros usados (com default)
    params_used: dict = field(default_factory=dict)
    
    # Eventos extraordinários consolidados por ano
    yearly_events: Dict[int, Tuple[float, float]] = field(default_factory=dict)
    
    # Insolvência (mês onde ocorreu, se houver)
    insolvency_month: Optional[int] = None
    insolvency_year: Optional[float] = None
    
    # Cenários representativos (parâmetros REAIS de cada percentil)
    representative_scenarios: List[RepresentativeScenario] = field(default_factory=list)
    
    # Parâmetros amostrados (para análise posterior, se necessário)
    sampled_capitals: Optional[np.ndarray] = None
    sampled_monthlies: Optional[np.ndarray] = None
    sampled_rates: Optional[np.ndarray] = None
    sampled_final_balances: Optional[np.ndarray] = None


class MonteCarloEngine:
    """
    Motor de simulação Monte Carlo vetorizado.
    Usa NumPy para máxima performance.
    """
    
    def __init__(self, inputs: MonteCarloInput):
        self.inputs = inputs
        self._validate()
    
    def _validate(self):
        """Valida os inputs antes de simular."""
        is_valid, errors = self.inputs.validate_all()
        if not is_valid:
            raise ValueError("\n".join(errors))
    
    def _calculate_single_scenario(
        self,
        initial: float,
        monthly: float,
        annual_rate: float,
        years: int
    ) -> np.ndarray:
        """
        Calcula evolução para um único cenário (vetorizado).
        
        Returns:
            Array com saldo mês a mês
        """
        total_months = years * 12
        monthly_rate = (1 + annual_rate / 100) ** (1/12) - 1
        
        balances = np.zeros(total_months + 1)
        balances[0] = initial
        
        for month in range(1, total_months + 1):
            balances[month] = balances[month - 1] * (1 + monthly_rate) + monthly
        
        return balances
    
    def _calculate_monte_carlo_vectorized(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Executa simulação Monte Carlo totalmente vetorizada.
        
        Returns:
            Tuple[all_balances, months]: Matriz (n_sim x n_months) e array de meses
        """
        n_sim = self.inputs.n_simulations
        years = self.inputs.periodo_anos
        total_months = years * 12
        
        # Gerar amostras para cada parâmetro
        capitals = self.inputs.capital_inicial.sample(n_sim)
        monthlies = self.inputs.aporte_mensal.sample(n_sim)
        rates = self.inputs.rentabilidade_anual.sample(n_sim)
        
        # Converter taxas anuais para mensais (vetorizado)
        monthly_rates = (1 + rates / 100) ** (1/12) - 1
        
        # Matriz de resultados: (n_simulations x total_months+1)
        all_balances = np.zeros((n_sim, total_months + 1))
        all_balances[:, 0] = capitals
        
        # Simulação mês a mês (vetorizada em todas as simulações)
        for month in range(1, total_months + 1):
            all_balances[:, month] = (
                all_balances[:, month - 1] * (1 + monthly_rates) + monthlies
            )
        
        months = np.arange(total_months + 1)
        return all_balances, months
    
    def run(self) -> MonteCarloResult:
        """
        Executa a simulação completa com suporte a eventos extraordinários.
        
        Returns:
            MonteCarloResult com todos os dados
        """
        years = self.inputs.periodo_anos
        total_months = years * 12
        
        # Valores determinísticos
        det_initial = self.inputs.capital_inicial.get_deterministic_value()
        det_monthly = self.inputs.aporte_mensal.get_deterministic_value()
        det_rate = self.inputs.rentabilidade_anual.get_deterministic_value()
        
        # Obter eventos consolidados por mês
        monthly_events = {}
        yearly_events = {}
        
        if self.inputs.events_manager and hasattr(self.inputs.events_manager, 'get_monthly_consolidated'):
            monthly_events = self.inputs.events_manager.get_monthly_consolidated(
                self.inputs.start_date, 
                total_months
            )
            yearly_events = self.inputs.events_manager.get_yearly_summary(
                self.inputs.start_date.year,
                years
            )
        
        # Cálculo determinístico COM eventos
        balances_det, insolvency_month = self._calculate_with_events(
            det_initial, det_monthly, det_rate, years, monthly_events
        )
        
        # Calcular total investido (inclui aportes extras)
        total_regular = det_initial + (det_monthly * total_months)
        total_extra_deposits = sum(dep for dep, _ in monthly_events.values())
        total_withdrawals = sum(wd for _, wd in monthly_events.values())
        total_invested = total_regular + total_extra_deposits
        
        final_balance_det = balances_det[-1]
        total_interest_det = final_balance_det - total_invested + total_withdrawals
        
        months = np.arange(total_months + 1)
        
        # Verificar se há parâmetros probabilísticos
        has_mc = self.inputs.has_probabilistic_params()
        
        # Variáveis para armazenar dados Monte Carlo
        sampled_capitals = None
        sampled_monthlies = None
        sampled_rates = None
        sampled_final_balances = None
        representative_scenarios = []
        
        if has_mc:
            # Executar Monte Carlo COM eventos - agora retorna também os parâmetros
            all_balances, sampled_capitals, sampled_monthlies, sampled_rates = \
                self._calculate_monte_carlo_with_events(monthly_events)
            
            # Saldos finais para análise
            sampled_final_balances = all_balances[:, -1]
            
            # Calcular estatísticas
            balances_mean = np.mean(all_balances, axis=0)
            balances_median = np.median(all_balances, axis=0)
            balances_min = np.min(all_balances, axis=0)
            balances_max = np.max(all_balances, axis=0)
            balances_p10 = np.percentile(all_balances, 10, axis=0)
            balances_p90 = np.percentile(all_balances, 90, axis=0)
            
            # IC 90% (Percentis 5 e 95)
            balances_p5 = np.percentile(all_balances, 5, axis=0)
            balances_p95 = np.percentile(all_balances, 95, axis=0)
            
            # Moda aproximada (usando histograma para cada mês)
            balances_mode = np.zeros(all_balances.shape[1])
            for i in range(all_balances.shape[1]):
                hist, bin_edges = np.histogram(all_balances[:, i], bins=50)
                mode_idx = np.argmax(hist)
                balances_mode[i] = (bin_edges[mode_idx] + bin_edges[mode_idx + 1]) / 2
            
            final_balance_mean = balances_mean[-1]
            final_balance_min = balances_min[-1]
            final_balance_max = balances_max[-1]
            
            # Extrair cenários representativos (parâmetros REAIS de cada percentil)
            representative_scenarios = extract_representative_scenarios(
                sampled_final_balances,
                sampled_capitals,
                sampled_monthlies,
                sampled_rates
            )
        else:
            # Sem Monte Carlo - usar valores determinísticos
            balances_mean = balances_det.copy()
            balances_median = balances_det.copy()
            balances_mode = balances_det.copy()
            balances_min = balances_det.copy()
            balances_max = balances_det.copy()
            balances_p10 = balances_det.copy()
            balances_p90 = balances_det.copy()
            balances_p5 = balances_det.copy()
            balances_p95 = balances_det.copy()
            
            final_balance_mean = final_balance_det
            final_balance_min = final_balance_det
            final_balance_max = final_balance_det
        
        # Projeção anual com eventos
        yearly_projection = []
        for year in range(years + 1):
            month_idx = year * 12
            invested = det_initial + (det_monthly * month_idx)
            
            # Adicionar aportes extras ao investido
            for m in range(year * 12):
                if m in monthly_events:
                    invested += monthly_events[m][0]
            
            # Eventos do ano
            extra_deps = yearly_events.get(year, (0, 0))[0]
            withdrawals = yearly_events.get(year, (0, 0))[1]
            
            yearly_projection.append(YearlyProjectionMC(
                year=year,
                total_invested=invested,
                balance_deterministic=balances_det[month_idx],
                balance_mean=balances_mean[month_idx],
                balance_median=balances_median[month_idx],
                balance_mode=balances_mode[month_idx],
                balance_min=balances_min[month_idx],
                balance_max=balances_max[month_idx],
                balance_p5=balances_p5[month_idx],
                balance_p10=balances_p10[month_idx],
                balance_p90=balances_p90[month_idx],
                balance_p95=balances_p95[month_idx],
                extra_deposits=extra_deps,
                withdrawals=withdrawals
            ))
        
        # Parâmetros usados
        params_used = {
            'capital_inicial': det_initial,
            'aporte_mensal': det_monthly,
            'rentabilidade_anual': det_rate,
            'periodo_anos': years,
            'meta': self.inputs.meta,
            'n_simulations': self.inputs.n_simulations,
            'total_extra_deposits': total_extra_deposits,
            'total_withdrawals': total_withdrawals
        }
        
        return MonteCarloResult(
            months=months,
            balances_deterministic=balances_det,
            balances_mean=balances_mean,
            balances_min=balances_min,
            balances_max=balances_max,
            balances_p10=balances_p10,
            balances_p90=balances_p90,
            balances_p5=balances_p5,
            balances_p95=balances_p95,
            total_invested=total_invested,
            total_interest_det=total_interest_det,
            final_balance_det=final_balance_det,
            final_balance_mean=final_balance_mean,
            final_balance_min=final_balance_min,
            final_balance_max=final_balance_max,
            yearly_projection=yearly_projection,
            n_simulations=self.inputs.n_simulations,
            has_monte_carlo=has_mc,
            params_used=params_used,
            yearly_events=yearly_events,
            insolvency_month=insolvency_month,
            insolvency_year=insolvency_month / 12 if insolvency_month else None,
            # Novos campos: cenários representativos com parâmetros REAIS
            representative_scenarios=representative_scenarios,
            sampled_capitals=sampled_capitals,
            sampled_monthlies=sampled_monthlies,
            sampled_rates=sampled_rates,
            sampled_final_balances=sampled_final_balances
        )
    
    def _calculate_with_events(
        self, 
        initial: float, 
        monthly: float, 
        annual_rate: float, 
        years: int,
        monthly_events: Dict[int, Tuple[float, float]]
    ) -> Tuple[np.ndarray, Optional[int]]:
        """
        Calcula saldos com eventos extraordinários.
        
        Returns:
            Tuple (balances_array, insolvency_month ou None)
        """
        total_months = years * 12
        monthly_rate = (1 + annual_rate / 100) ** (1/12) - 1
        
        balances = np.zeros(total_months + 1)
        balances[0] = initial
        
        insolvency_month = None
        
        for m in range(1, total_months + 1):
            # Juros sobre saldo anterior
            balances[m] = balances[m-1] * (1 + monthly_rate)
            
            # Aporte mensal regular
            balances[m] += monthly
            
            # Eventos do mês
            if m in monthly_events:
                deposits, withdrawals = monthly_events[m]
                balances[m] += deposits
                
                if withdrawals > 0:
                    if balances[m] < withdrawals:
                        # Insolvência!
                        if insolvency_month is None:
                            insolvency_month = m
                        balances[m] = 0
                    else:
                        balances[m] -= withdrawals
            
            # Garantir não negativo
            if balances[m] < 0:
                balances[m] = 0
                if insolvency_month is None:
                    insolvency_month = m
        
        return balances, insolvency_month
    
    def _calculate_monte_carlo_with_events(
        self,
        monthly_events: Dict[int, Tuple[float, float]]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Executa simulação Monte Carlo vetorizada com eventos.
        
        Os eventos são fixos (nominais) em todos os cenários.
        
        Returns:
            Tuple contendo:
            - all_balances: Matriz (n_sim x meses) com saldos
            - initials: Array com capitais iniciais amostrados
            - monthlies: Array com aportes mensais amostrados
            - rates: Array com taxas anuais amostradas
        """
        n = self.inputs.n_simulations
        years = self.inputs.periodo_anos
        total_months = years * 12
        
        # Gerar parâmetros aleatórios
        initials = self.inputs.capital_inicial.sample(n)
        monthlies = self.inputs.aporte_mensal.sample(n)
        rates = self.inputs.rentabilidade_anual.sample(n)
        
        # Converter taxa anual para mensal
        monthly_rates = (1 + rates / 100) ** (1/12) - 1
        
        # Matriz de saldos
        all_balances = np.zeros((n, total_months + 1))
        all_balances[:, 0] = initials
        
        for m in range(1, total_months + 1):
            # Juros
            all_balances[:, m] = all_balances[:, m-1] * (1 + monthly_rates)
            
            # Aporte mensal
            all_balances[:, m] += monthlies
            
            # Eventos do mês (fixos para todos os cenários)
            if m in monthly_events:
                deposits, withdrawals = monthly_events[m]
                all_balances[:, m] += deposits
                all_balances[:, m] -= withdrawals
            
            # Garantir não negativo
            all_balances[:, m] = np.maximum(0, all_balances[:, m])
        
        return all_balances, initials, monthlies, rates


def extract_representative_scenarios(
    final_balances: np.ndarray,
    capitals: np.ndarray,
    monthlies: np.ndarray,
    rates: np.ndarray
) -> List[RepresentativeScenario]:
    """
    Extrai cenários representativos para cada percentil.
    
    Para cada percentil, encontra a simulação cujo saldo final
    está mais próximo do valor do percentil e retorna seus
    parâmetros REAIS.
    
    Args:
        final_balances: Array com saldos finais de todas as simulações
        capitals: Array com capitais iniciais amostrados
        monthlies: Array com aportes mensais amostrados
        rates: Array com taxas anuais amostradas
        
    Returns:
        Lista de RepresentativeScenario para cada percentil
    """
    scenarios_config = [
        ("P5 (Pessimista)", "P5", 5, "Worst Case"),
        ("P25 (Conservador)", "P25", 25, "Conservador"),
        ("P50 (Mediana)", "P50", 50, "Típico"),
        ("P75 (Bom)", "P75", 75, "Otimista"),
        ("P95 (Otimista)", "P95", 95, "Best Case"),
    ]
    
    results = []
    
    for name, percentile_label, percentile_value, scenario_type in scenarios_config:
        # Calcular o valor do percentil
        target_balance = float(np.percentile(final_balances, percentile_value))
        
        # Encontrar o índice da simulação mais próxima deste percentil
        idx = int(np.argmin(np.abs(final_balances - target_balance)))
        
        # Extrair os parâmetros REAIS desta simulação
        results.append(RepresentativeScenario(
            scenario_name=name,
            percentile=percentile_label,
            capital_inicial=float(capitals[idx]),
            aporte_mensal=float(monthlies[idx]),
            rentabilidade_anual=float(rates[idx]),
            saldo_final=float(final_balances[idx]),
            scenario_type=scenario_type
        ))
    
    # Adicionar cenário da Média (simulação mais próxima da média)
    mean_balance = float(np.mean(final_balances))
    idx_mean = int(np.argmin(np.abs(final_balances - mean_balance)))
    
    results.append(RepresentativeScenario(
        scenario_name="Média",
        percentile="MÉDIA",
        capital_inicial=float(capitals[idx_mean]),
        aporte_mensal=float(monthlies[idx_mean]),
        rentabilidade_anual=float(rates[idx_mean]),
        saldo_final=float(final_balances[idx_mean]),
        scenario_type="Valor Esperado"
    ))
    
    return results


# =============================================================================
# WORKER PARA EXECUÇÃO EM THREAD SEPARADA
# =============================================================================

from PySide6.QtCore import QObject, Signal, QRunnable, Slot


class MonteCarloSignals(QObject):
    """Sinais para comunicação do worker."""
    finished = Signal(object)  # Emite MonteCarloResult
    error = Signal(str)        # Emite mensagem de erro
    progress = Signal(int)     # Emite progresso (0-100)


class MonteCarloWorker(QRunnable):
    """
    Worker para executar Monte Carlo em thread separada.
    Evita congelamento da UI.
    """
    
    def __init__(self, inputs: MonteCarloInput):
        super().__init__()
        self.inputs = inputs
        self.signals = MonteCarloSignals()
    
    @Slot()
    def run(self):
        """Executa a simulação."""
        try:
            self.signals.progress.emit(10)
            
            engine = MonteCarloEngine(self.inputs)
            
            self.signals.progress.emit(30)
            
            result = engine.run()
            
            self.signals.progress.emit(100)
            self.signals.finished.emit(result)
            
        except Exception as e:
            self.signals.error.emit(str(e))
