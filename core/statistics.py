"""
PyInvest - Módulo de Persistência e Estatísticas Avançadas
Gerencia arquivos .pyinv e cálculos estatísticos (P5, P50, P95, etc.)
"""

import json
import math
import numpy as np
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any, Callable
from pathlib import Path


# =============================================================================
# TAXA LIVRE DE RISCO (CDI)
# =============================================================================

# Cache global para a taxa CDI
_cached_cdi_rate: Optional[float] = None
_cdi_last_fetch: Optional[datetime] = None
_cdi_source: str = "fallback"  # "b3", "manual", "fallback"

def fetch_cdi_rate_from_bcb() -> Optional[float]:
    """
    Busca a taxa CDI anualizada via API do Banco Central.
    
    O CDI (Taxa DI) é calculado e publicado oficialmente pela B3.
    O BCB disponibiliza esses dados via API do SGS (Série 12).
    
    Returns:
        Taxa CDI anualizada como decimal (ex: 0.1175 para 11.75%) ou None se falhar.
    """
    import urllib.request
    import ssl
    
    try:
        # URL da API do BCB - Série 12 (CDI da B3) - Último valor
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados/ultimos/1?formato=json"
        
        # Criar contexto SSL que ignora verificação (alguns sistemas têm problemas com certificados)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Fazer requisição com timeout
        request = urllib.request.Request(url, headers={'User-Agent': 'PyInvest/1.0'})
        with urllib.request.urlopen(request, timeout=10, context=context) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data and len(data) > 0:
                # O valor vem como string com vírgula brasileira (ex: "0,0453")
                # A Série 12 contém a taxa CDI DIÁRIA (overnight), não anualizada
                valor_str = data[0].get('valor', '0')
                valor_str = valor_str.replace(',', '.')
                taxa_diaria_percentual = float(valor_str)
                
                # Converter de percentual para decimal (0.0453% → 0.000453)
                taxa_diaria = taxa_diaria_percentual / 100.0
                
                # Anualizar usando juros compostos (252 dias úteis por ano)
                # Fórmula: (1 + taxa_diária)^252 - 1
                taxa_anual = (1 + taxa_diaria) ** 252 - 1
                
                return taxa_anual
        
        return None
        
    except Exception as e:
        print(f"[CDI] Erro ao buscar taxa do BCB: {e}")
        return None


def get_risk_free_rate(
    force_refresh: bool = False,
    fallback_rate: float = 0.10,
    on_manual_input_needed: Optional[Callable[[], Optional[float]]] = None
) -> float:
    """
    Obtém a taxa livre de risco (CDI) com cache e fallback.
    
    Args:
        force_refresh: Se True, ignora cache e busca novamente
        fallback_rate: Taxa padrão caso a busca falhe (10% = 0.10)
        on_manual_input_needed: Callback para solicitar input manual do usuário
        
    Returns:
        Taxa CDI anualizada como decimal (ex: 0.1175 para 11.75%)
    """
    global _cached_cdi_rate, _cdi_last_fetch, _cdi_source
    
    # Verificar cache (válido por 24 horas)
    if not force_refresh and _cached_cdi_rate is not None and _cdi_last_fetch is not None:
        cache_age = (datetime.now() - _cdi_last_fetch).total_seconds()
        if cache_age < 86400:  # 24 horas em segundos
            return _cached_cdi_rate
    
    # Tentar buscar do BCB
    rate = fetch_cdi_rate_from_bcb()
    
    if rate is not None:
        _cached_cdi_rate = rate
        _cdi_last_fetch = datetime.now()
        _cdi_source = "b3"
        print(f"[CDI] Taxa obtida da B3 (via API BCB): {rate * 100:.2f}% a.a.")
        return rate
    
    # Falha na busca - tentar input manual
    if on_manual_input_needed is not None:
        manual_rate = on_manual_input_needed()
        if manual_rate is not None:
            _cached_cdi_rate = manual_rate
            _cdi_last_fetch = datetime.now()
            _cdi_source = "manual"
            return manual_rate
    
    # Usar fallback
    _cdi_source = "fallback"
    print(f"[CDI] Usando taxa padrão: {fallback_rate * 100:.2f}% a.a.")
    return fallback_rate


def get_cdi_info() -> dict:
    """
    Retorna informações sobre a taxa CDI atual.
    
    Returns:
        Dict com 'rate' (taxa anual), 'monthly' (taxa mensal), 
        'source' (origem) e 'source_label' (descrição da origem)
    """
    global _cached_cdi_rate, _cdi_source
    
    rate = _cached_cdi_rate if _cached_cdi_rate is not None else 0.10
    
    # Calcular taxa mensal equivalente: (1 + taxa_anual)^(1/12) - 1
    monthly_rate = (1 + rate) ** (1/12) - 1
    
    source_labels = {
        "b3": "🌐 B3 - Bolsa do Brasil (Online)",
        "manual": "✏️ Digitado pelo usuário",
        "fallback": "⚙️ Valor padrão (10%)"
    }
    
    return {
        'rate': rate,
        'rate_percent': rate * 100,
        'monthly': monthly_rate,
        'monthly_percent': monthly_rate * 100,
        'source': _cdi_source,
        'source_label': source_labels.get(_cdi_source, "Desconhecido")
    }


def clear_cdi_cache():
    """Limpa o cache da taxa CDI."""
    global _cached_cdi_rate, _cdi_last_fetch, _cdi_source
    _cached_cdi_rate = None
    _cdi_last_fetch = None
    _cdi_source = "fallback"


# =============================================================================
# ESTRUTURAS DE DADOS
# =============================================================================

@dataclass
class ParameterSet:
    """Conjunto de parâmetros com min/base/max."""
    min_value: Optional[float] = None
    base_value: float = 0.0
    max_value: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            'min': self.min_value,
            'base': self.base_value,
            'max': self.max_value
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ParameterSet':
        return cls(
            min_value=data.get('min'),
            base_value=data.get('base', 0),
            max_value=data.get('max')
        )


@dataclass
class HistoricalReturn:
    """Retorno histórico de um ano."""
    year: int
    return_rate: float  # Ex: 0.1263 para 12.63%
    notes: str = ""
    
    def to_dict(self) -> dict:
        return {
            'ano': self.year,
            'retorno': self.return_rate,
            'notas': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HistoricalReturn':
        return cls(
            year=data.get('ano', 0),
            return_rate=data.get('retorno', 0),
            notes=data.get('notas', '')
        )


@dataclass
class ExtraordinaryEventData:
    """Evento extraordinário para persistência."""
    date_str: str
    month_simulation: int
    description: str
    extra_deposit: float = 0.0
    withdrawal: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            'data': self.date_str,
            'mes_simulacao': self.month_simulation,
            'descricao': self.description,
            'aporte_extra': self.extra_deposit,
            'resgate': self.withdrawal
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExtraordinaryEventData':
        return cls(
            date_str=data.get('data', ''),
            month_simulation=data.get('mes_simulacao', 0),
            description=data.get('descricao', ''),
            extra_deposit=data.get('aporte_extra', 0),
            withdrawal=data.get('resgate', 0)
        )


@dataclass
class MonteCarloConfig:
    """Configuração do Monte Carlo."""
    n_simulations: int = 9000
    method: str = "bootstrap"  # bootstrap, normal, t_student
    expert_mode: bool = False
    random_seed: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            'n_simulacoes': self.n_simulations,
            'metodo': self.method,
            'modo_expert': self.expert_mode,
            'seed_aleatoriedade': self.random_seed
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MonteCarloConfig':
        return cls(
            n_simulations=data.get('n_simulacoes', 9000),
            method=data.get('metodo', 'bootstrap'),
            expert_mode=data.get('modo_expert', False),
            random_seed=data.get('seed_aleatoriedade')
        )


@dataclass
class ProjectData:
    """Dados completos do projeto PyInvest."""
    # Metadados
    name: str = "Novo Projeto"
    created_at: str = ""
    last_modified: str = ""
    version: str = "2.0"
    
    # Parâmetros
    capital_inicial: ParameterSet = field(default_factory=ParameterSet)
    aporte_mensal: ParameterSet = field(default_factory=ParameterSet)
    rentabilidade_anual: ParameterSet = field(default_factory=ParameterSet)
    meta_final: float = 0.0
    periodo_anos: int = 10
    start_date: str = ""
    
    # Dados históricos
    historical_returns: List[HistoricalReturn] = field(default_factory=list)
    
    # Configuração Monte Carlo
    monte_carlo_config: MonteCarloConfig = field(default_factory=MonteCarloConfig)
    
    # Eventos extraordinários
    extraordinary_events: List[ExtraordinaryEventData] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_modified:
            self.last_modified = self.created_at
        if not self.start_date:
            self.start_date = date.today().strftime('%Y-%m-%d')
    
    def to_dict(self) -> dict:
        """Converte para dicionário JSON-serializável."""
        return {
            'metadata': {
                'name': self.name,
                'created_at': self.created_at,
                'last_modified': datetime.now().isoformat(),
                'version': self.version
            },
            'parametros': {
                'capital_inicial': self.capital_inicial.to_dict(),
                'aporte_mensal': self.aporte_mensal.to_dict(),
                'rentabilidade_anual': {
                    **self.rentabilidade_anual.to_dict(),
                    'unidade': '%'
                },
                'meta_final': self.meta_final,
                'periodo_anos': self.periodo_anos,
                'data_inicio': self.start_date
            },
            'dados_historicos': [r.to_dict() for r in self.historical_returns],
            'configuracao_monte_carlo': self.monte_carlo_config.to_dict(),
            'eventos_extraordinarios': [e.to_dict() for e in self.extraordinary_events]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProjectData':
        """Cria instância a partir de dicionário."""
        metadata = data.get('metadata', {})
        params = data.get('parametros', {})
        
        return cls(
            name=metadata.get('name', 'Projeto Importado'),
            created_at=metadata.get('created_at', ''),
            last_modified=metadata.get('last_modified', ''),
            version=metadata.get('version', '2.0'),
            
            capital_inicial=ParameterSet.from_dict(params.get('capital_inicial', {})),
            aporte_mensal=ParameterSet.from_dict(params.get('aporte_mensal', {})),
            rentabilidade_anual=ParameterSet.from_dict(params.get('rentabilidade_anual', {})),
            meta_final=params.get('meta_final', 0),
            periodo_anos=params.get('periodo_anos', 10),
            start_date=params.get('data_inicio', ''),
            
            historical_returns=[
                HistoricalReturn.from_dict(r) 
                for r in data.get('dados_historicos', [])
            ],
            
            monte_carlo_config=MonteCarloConfig.from_dict(
                data.get('configuracao_monte_carlo', {})
            ),
            
            extraordinary_events=[
                ExtraordinaryEventData.from_dict(e)
                for e in data.get('eventos_extraordinarios', [])
            ]
        )


# =============================================================================
# PERSISTÊNCIA (.PYINV)
# =============================================================================

def save_project(filepath: str, project: ProjectData) -> Tuple[bool, Optional[str]]:
    """
    Salva projeto em arquivo .pyinv (JSON).
    
    Args:
        filepath: Caminho do arquivo
        project: Dados do projeto
        
    Returns:
        Tuple (sucesso, mensagem_erro)
    """
    try:
        path = Path(filepath)
        if not path.suffix.lower() == '.pyinv':
            path = path.with_suffix('.pyinv')
        
        data = project.to_dict()
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True, None
        
    except PermissionError:
        return False, "Permissão negada para salvar o arquivo."
    except Exception as e:
        return False, f"Erro ao salvar: {str(e)}"


def load_project(filepath: str) -> Tuple[Optional[ProjectData], Optional[str]]:
    """
    Carrega projeto de arquivo .pyinv.
    
    Args:
        filepath: Caminho do arquivo
        
    Returns:
        Tuple (projeto, mensagem_erro)
    """
    try:
        path = Path(filepath)
        
        if not path.exists():
            return None, "Arquivo não encontrado."
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validar versão
        version = data.get('metadata', {}).get('version', '1.0')
        if version.split('.')[0] not in ['1', '2']:
            return None, f"Versão do arquivo não suportada: {version}"
        
        project = ProjectData.from_dict(data)
        return project, None
        
    except json.JSONDecodeError:
        return None, "Arquivo inválido (não é JSON válido)."
    except Exception as e:
        return None, f"Erro ao carregar: {str(e)}"


# =============================================================================
# ESTATÍSTICAS AVANÇADAS
# =============================================================================

@dataclass
class PercentileStats:
    """Estatísticas de percentis."""
    p5: float = 0.0
    p10: float = 0.0
    p25: float = 0.0
    p50: float = 0.0  # Mediana
    p75: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    mean: float = 0.0
    mode: float = 0.0
    std_dev: float = 0.0
    variance: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    coef_variation: float = 0.0  # CV = std_dev / mean


@dataclass
class ImplicitParameters:
    """Parâmetros implícitos de um cenário."""
    scenario_name: str
    percentile: str
    capital_inicial: float
    aporte_mensal: float
    rentabilidade_anual: float
    saldo_final: float
    scenario_type: str  # "Pessimista", "Conservador", "Típico", "Otimista", "Best Case"


@dataclass 
class RiskMetrics:
    """Métricas de risco."""
    prob_success: float = 0.0      # Probabilidade de atingir meta (%)
    prob_ruin: float = 0.0         # Probabilidade de ruína/insolvência (%)
    var_95: float = 0.0            # Value at Risk 95%
    cvar_95: float = 0.0           # Conditional VaR (Expected Shortfall)
    sharpe_ratio: float = 0.0      # Índice de Sharpe
    risk_return_ratio: float = 0.0 # Razão Risco/Retorno
    volatility: float = 0.0        # Volatilidade (desvio padrão anualizado)


def calculate_percentiles(final_balances: np.ndarray) -> PercentileStats:
    """
    Calcula percentis e estatísticas dos saldos finais.
    
    Args:
        final_balances: Array com saldos finais das simulações
        
    Returns:
        PercentileStats com todas as estatísticas
    """
    n = len(final_balances)
    if n == 0:
        return PercentileStats()
    
    sorted_balances = np.sort(final_balances)
    
    # Percentis
    p5 = sorted_balances[int(0.05 * n)]
    p10 = sorted_balances[int(0.10 * n)]
    p25 = sorted_balances[int(0.25 * n)]
    p50 = sorted_balances[int(0.50 * n)]  # Mediana
    p75 = sorted_balances[int(0.75 * n)]
    p90 = sorted_balances[int(0.90 * n)]
    p95 = sorted_balances[int(0.95 * n)]
    
    # Estatísticas básicas
    mean = np.mean(final_balances)
    std_dev = np.std(final_balances)
    variance = np.var(final_balances)
    min_val = np.min(final_balances)
    max_val = np.max(final_balances)
    
    # Coeficiente de variação
    coef_variation = (std_dev / mean * 100) if mean > 0 else 0
    
    # Moda: encontrar classe modal do histograma
    try:
        hist, bins = np.histogram(final_balances, bins=30)
        idx_modal = np.argmax(hist)
        mode = (bins[idx_modal] + bins[idx_modal + 1]) / 2
    except:
        mode = p50  # Fallback para mediana
    
    return PercentileStats(
        p5=float(p5),
        p10=float(p10),
        p25=float(p25),
        p50=float(p50),
        p75=float(p75),
        p90=float(p90),
        p95=float(p95),
        mean=float(mean),
        mode=float(mode),
        std_dev=float(std_dev),
        variance=float(variance),
        min_value=float(min_val),
        max_value=float(max_val),
        coef_variation=float(coef_variation)
    )


def find_implicit_rate(
    target_balance: float,
    capital_inicial: float,
    aporte_mensal: float,
    periodo_anos: int,
    tolerance: float = 1000.0,
    max_iterations: int = 100
) -> Optional[float]:
    """
    Encontra a taxa de rentabilidade anual que reproduz um saldo final alvo.
    
    Usa busca binária para encontrar: r_anual = f(saldo_final)
    
    Args:
        target_balance: Saldo final desejado
        capital_inicial: Capital inicial
        aporte_mensal: Aporte mensal
        periodo_anos: Período em anos
        tolerance: Tolerância em R$
        max_iterations: Máximo de iterações
        
    Returns:
        Taxa anual (%) ou None se não convergir
    """
    r_min, r_max = -30.0, 50.0  # -30% a +50% ao ano
    
    def simulate_deterministic(rate_annual: float) -> float:
        """Simula cenário determinístico."""
        rate_monthly = (1 + rate_annual / 100) ** (1/12) - 1
        balance = capital_inicial
        
        for _ in range(periodo_anos * 12):
            balance = balance * (1 + rate_monthly) + aporte_mensal
        
        return balance
    
    for _ in range(max_iterations):
        r_mid = (r_min + r_max) / 2
        simulated_balance = simulate_deterministic(r_mid)
        
        if abs(simulated_balance - target_balance) < tolerance:
            return r_mid
        
        if simulated_balance < target_balance:
            r_min = r_mid
        else:
            r_max = r_mid
    
    # Retorna melhor aproximação mesmo sem convergir
    return (r_min + r_max) / 2


def extract_implicit_parameters(
    percentile_stats: PercentileStats,
    capital_inicial: float,
    aporte_mensal: float,
    periodo_anos: int
) -> List[ImplicitParameters]:
    """
    Extrai parâmetros implícitos para cada cenário/percentil.
    
    Args:
        percentile_stats: Estatísticas calculadas
        capital_inicial: Capital inicial usado
        aporte_mensal: Aporte mensal usado
        periodo_anos: Período usado
        
    Returns:
        Lista de ImplicitParameters para cada cenário
    """
    scenarios = [
        ("P5 (Pessimista)", "P5", percentile_stats.p5, "Worst Case"),
        ("P25 (Conservador)", "P25", percentile_stats.p25, "Conservador"),
        ("P50 (Mediana)", "P50", percentile_stats.p50, "Típico"),
        ("P75 (Bom)", "P75", percentile_stats.p75, "Otimista"),
        ("P95 (Otimista)", "P95", percentile_stats.p95, "Best Case"),
        ("Média", "MÉDIA", percentile_stats.mean, "Valor Esperado"),
        ("Moda", "MODA", percentile_stats.mode, "Mais Frequente"),
    ]
    
    results = []
    
    for name, percentile, target_balance, scenario_type in scenarios:
        rate = find_implicit_rate(
            target_balance, capital_inicial, aporte_mensal, periodo_anos
        )
        
        if rate is not None:
            results.append(ImplicitParameters(
                scenario_name=name,
                percentile=percentile,
                capital_inicial=capital_inicial,
                aporte_mensal=aporte_mensal,
                rentabilidade_anual=rate,
                saldo_final=target_balance,
                scenario_type=scenario_type
            ))
    
    return results


def calculate_risk_metrics(
    final_balances: np.ndarray,
    meta: float,
    capital_inicial: float,
    aporte_mensal: float = 0.0,
    periodo_anos: int = 1,
    risk_free_rate: float = 0.10  # CDI ~10% a.a.
) -> RiskMetrics:
    """
    Calcula métricas de risco.
    
    Args:
        final_balances: Array com saldos finais das simulações
        meta: Meta de patrimônio
        capital_inicial: Capital inicial investido
        aporte_mensal: Valor do aporte mensal
        periodo_anos: Período em anos da simulação
        risk_free_rate: Taxa livre de risco anual (para Sharpe)
        
    Returns:
        RiskMetrics com todas as métricas
    """
    n = len(final_balances)
    if n == 0:
        return RiskMetrics()
    
    # Capital total investido (inicial + aportes)
    meses = periodo_anos * 12
    capital_total_investido = capital_inicial + (aporte_mensal * meses)
    
    # Estatísticas básicas
    saldo_medio = np.mean(final_balances)
    volatility = np.std(final_balances)
    p5 = np.percentile(final_balances, 5)
    
    # =========================================================================
    # 1. PROBABILIDADE DE SUCESSO (atingir meta)
    # =========================================================================
    success_count = np.sum(final_balances >= meta)
    prob_success = (success_count / n) * 100
    
    # =========================================================================
    # 2. PROBABILIDADE DE RUÍNA (saldo < capital inicial)
    # =========================================================================
    ruin_count = np.sum(final_balances < capital_inicial)
    prob_ruin = (ruin_count / n) * 100
    
    # =========================================================================
    # 3. VaR 95% (Value at Risk Relativo à Média)
    # "Em relação ao saldo médio esperado, no pior caso (5%) você terá X a menos"
    # =========================================================================
    var_95 = saldo_medio - p5
    var_95 = max(0, var_95)  # VaR não pode ser negativo
    
    # =========================================================================
    # 4. CVaR (Conditional VaR / Expected Shortfall - Relativo à Média)
    # "Perda média esperada nos 5% piores cenários, em relação à média"
    # =========================================================================
    worst_cases = final_balances[final_balances <= p5]
    worst_mean = np.mean(worst_cases) if len(worst_cases) > 0 else p5
    cvar_95 = saldo_medio - worst_mean
    cvar_95 = max(0, cvar_95)
    
    # =========================================================================
    # 5. RAZÃO RISCO/RETORNO (usando capital TOTAL investido)
    # =========================================================================
    ganho_esperado = saldo_medio - capital_total_investido
    if ganho_esperado > 0:
        risk_return_ratio = var_95 / ganho_esperado
    else:
        risk_return_ratio = float('inf') if var_95 > 0 else 0
    
    # =========================================================================
    # 6. ÍNDICE DE SHARPE (retorno anualizado - CAGR)
    # =========================================================================
    if capital_total_investido > 0 and periodo_anos > 0:
        # CAGR = Taxa de crescimento anual composta
        cagr = (saldo_medio / capital_total_investido) ** (1 / periodo_anos) - 1
    else:
        cagr = 0
    
    # Retorno excedente (vs taxa livre de risco)
    retorno_excedente = cagr - risk_free_rate
    
    # Volatilidade anualizada (aproximação: std / média * 100 para %)
    volatilidade_percentual = (volatility / saldo_medio * 100) if saldo_medio > 0 else 0
    
    # Sharpe = Retorno excedente / Volatilidade (em termos relativos)
    if volatilidade_percentual > 0:
        sharpe_ratio = (retorno_excedente * 100) / volatilidade_percentual
    else:
        sharpe_ratio = 0 if retorno_excedente <= 0 else float('inf')
    
    return RiskMetrics(
        prob_success=float(prob_success),
        prob_ruin=float(prob_ruin),
        var_95=float(var_95),
        cvar_95=float(cvar_95),
        sharpe_ratio=float(sharpe_ratio),
        risk_return_ratio=float(risk_return_ratio),
        volatility=float(volatility)
    )


# =============================================================================
# MÉTODOS DE SIMULAÇÃO
# =============================================================================

def bootstrap_returns(
    historical_returns: List[float],
    n_years: int,
    n_simulations: int,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Gera retornos via Bootstrap Histórico.
    
    Reamostra com reposição os retornos históricos.
    
    Args:
        historical_returns: Lista de retornos anuais históricos
        n_years: Número de anos a simular
        n_simulations: Número de simulações
        seed: Seed para reprodutibilidade
        
    Returns:
        Array (n_simulations, n_years) de retornos
    """
    if seed is not None:
        np.random.seed(seed)
    
    returns = np.array(historical_returns)
    
    # Reamostrar com reposição
    simulated_returns = np.random.choice(
        returns, 
        size=(n_simulations, n_years),
        replace=True
    )
    
    return simulated_returns


def normal_returns(
    mean_return: float,
    std_return: float,
    n_years: int,
    n_simulations: int,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Gera retornos via Distribuição Normal.
    
    Args:
        mean_return: Retorno médio anual
        std_return: Desvio padrão dos retornos
        n_years: Número de anos
        n_simulations: Número de simulações
        seed: Seed para reprodutibilidade
        
    Returns:
        Array (n_simulations, n_years) de retornos
    """
    if seed is not None:
        np.random.seed(seed)
    
    return np.random.normal(mean_return, std_return, (n_simulations, n_years))


def t_student_returns(
    mean_return: float,
    std_return: float,
    n_years: int,
    n_simulations: int,
    df: int = 5,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Gera retornos via Distribuição t-Student.
    
    Captura caudas gordas (eventos extremos).
    
    Args:
        mean_return: Retorno médio anual
        std_return: Desvio padrão dos retornos
        n_years: Número de anos
        n_simulations: Número de simulações
        df: Graus de liberdade (menor = caudas mais gordas)
        seed: Seed para reprodutibilidade
        
    Returns:
        Array (n_simulations, n_years) de retornos
    """
    if seed is not None:
        np.random.seed(seed)
    
    # t-Student padronizada, depois escalar
    t_samples = np.random.standard_t(df, (n_simulations, n_years))
    
    # Escalar para média e desvio desejados
    # Ajustar variância: Var(t) = df/(df-2) para df > 2
    scale_factor = std_return * math.sqrt((df - 2) / df) if df > 2 else std_return
    
    return mean_return + scale_factor * t_samples


# =============================================================================
# EXPORTAÇÃO CSV
# =============================================================================

def export_percentiles_csv(
    filepath: str,
    implicit_params: List[ImplicitParameters]
) -> Tuple[bool, Optional[str]]:
    """
    Exporta tabela de parâmetros implícitos para CSV.
    
    Args:
        filepath: Caminho do arquivo
        implicit_params: Lista de parâmetros implícitos
        
    Returns:
        Tuple (sucesso, erro)
    """
    try:
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            
            # Header
            writer.writerow([
                'Cenário', 'Percentil', 'Capital Inicial (R$)', 
                'Aporte Mensal (R$)', 'Rentabilidade Anual (%)', 
                'Saldo Final (R$)', 'Tipo'
            ])
            
            for p in implicit_params:
                writer.writerow([
                    p.scenario_name,
                    p.percentile,
                    f"{p.capital_inicial:,.2f}".replace(',', '.'),
                    f"{p.aporte_mensal:,.2f}".replace(',', '.'),
                    f"{p.rentabilidade_anual:.2f}".replace('.', ','),
                    f"{p.saldo_final:,.2f}".replace(',', '.'),
                    p.scenario_type
                ])
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def export_historical_returns_csv(
    filepath: str,
    returns: List[HistoricalReturn]
) -> Tuple[bool, Optional[str]]:
    """
    Exporta dados históricos para CSV.
    """
    try:
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['Ano', 'Retorno (%)', 'Notas'])
            
            for r in returns:
                writer.writerow([
                    r.year,
                    f"{r.return_rate * 100:.2f}".replace('.', ','),
                    r.notes
                ])
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def import_historical_returns_csv(
    filepath: str
) -> Tuple[Optional[List[HistoricalReturn]], Optional[str]]:
    """
    Importa dados históricos de CSV.
    
    Formatos aceitos:
    - ano;retorno (0.1263 ou 12.63)
    - Ano;Retorno (%);Notas
    """
    try:
        import csv
        
        returns = []
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            for row in reader:
                try:
                    year = int(row.get('ano', row.get('Ano', 0)))
                    
                    # Tentar diferentes formatos de retorno
                    ret_str = row.get('retorno', row.get('Retorno (%)', '0'))
                    ret_str = ret_str.replace(',', '.').replace('%', '').strip()
                    ret_value = float(ret_str)
                    
                    # Se valor > 1, provavelmente é percentual (12.63%)
                    if ret_value > 1:
                        ret_value = ret_value / 100
                    
                    notes = row.get('notas', row.get('Notas', ''))
                    
                    returns.append(HistoricalReturn(
                        year=year,
                        return_rate=ret_value,
                        notes=notes
                    ))
                    
                except (ValueError, KeyError):
                    continue
        
        if not returns:
            return None, "Nenhum dado válido encontrado no arquivo."
        
        return sorted(returns, key=lambda r: r.year), None
        
    except Exception as e:
        return None, str(e)
