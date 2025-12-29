"""
PyInvest - Módulo de Bootstrap para Retornos Mensais

Este módulo implementa a geração de cenários anuais sintéticos a partir de
retornos mensais históricos usando Bootstrap e Block Bootstrap.

Autor: PyInvest Team
Versão: 6.0
Data: Dezembro 2024
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum
import numpy as np
from datetime import datetime
import csv
import io


class BootstrapMethod(Enum):
    """Métodos de Bootstrap disponíveis."""
    SIMPLE = "bootstrap"
    BLOCK = "block_bootstrap"


@dataclass
class MonthlyReturnData:
    """
    Estrutura para armazenar retornos mensais históricos.
    
    Attributes:
        periods: Lista de períodos no formato 'Mmm/AAAA' (ex: 'Jan/2017')
        returns: Array NumPy com retornos mensais em percentual
        notes: Lista opcional de notas para cada período
    """
    periods: List[str]
    returns: np.ndarray
    notes: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validação após inicialização."""
        if len(self.periods) != len(self.returns):
            raise ValueError(
                f"Número de períodos ({len(self.periods)}) deve ser igual "
                f"ao número de retornos ({len(self.returns)})"
            )
        if self.notes is not None and len(self.notes) != len(self.returns):
            raise ValueError(
                f"Número de notas ({len(self.notes)}) deve ser igual "
                f"ao número de retornos ({len(self.returns)})"
            )
        # Garantir que returns é numpy array
        if not isinstance(self.returns, np.ndarray):
            self.returns = np.array(self.returns, dtype=float)
    
    @property
    def n_months(self) -> int:
        """Número total de meses."""
        return len(self.returns)
    
    @property
    def n_complete_years(self) -> int:
        """Número de anos completos (12 meses)."""
        return self.n_months // 12
    
    @property
    def start_period(self) -> str:
        """Primeiro período."""
        return self.periods[0] if self.periods else ""
    
    @property
    def end_period(self) -> str:
        """Último período."""
        return self.periods[-1] if self.periods else ""
    
    @property
    def period_range(self) -> str:
        """Range de períodos formatado."""
        return f"{self.start_period} - {self.end_period}"
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Valida os dados mensais.
        
        Returns:
            Tuple (é_válido, lista_de_erros)
        """
        errors = []
        
        # Mínimo de 12 meses
        if self.n_months < 12:
            errors.append(f"Mínimo de 12 meses necessário. Atual: {self.n_months}")
        
        # Verificar valores extremos
        extreme_high = np.where(self.returns > 50)[0]
        extreme_low = np.where(self.returns < -50)[0]
        
        if len(extreme_high) > 0:
            for idx in extreme_high[:3]:  # Mostrar até 3
                errors.append(
                    f"⚠️ Valor extremo alto em {self.periods[idx]}: {self.returns[idx]:.2f}%"
                )
        
        if len(extreme_low) > 0:
            for idx in extreme_low[:3]:
                errors.append(
                    f"⚠️ Valor extremo baixo em {self.periods[idx]}: {self.returns[idx]:.2f}%"
                )
        
        # Verificar intervalo válido
        invalid_high = np.where(self.returns > 1000)[0]
        invalid_low = np.where(self.returns <= -100)[0]
        
        if len(invalid_high) > 0:
            errors.append(f"Retornos acima de 1000% não são permitidos")
        
        if len(invalid_low) > 0:
            errors.append(f"Retornos de -100% ou menos não são permitidos")
        
        is_valid = len([e for e in errors if not e.startswith("⚠️")]) == 0
        return is_valid, errors
    
    def get_statistics(self) -> Dict[str, float]:
        """Calcula estatísticas dos retornos mensais."""
        n = len(self.returns)
        mean = float(np.mean(self.returns))
        std = float(np.std(self.returns))
        
        # Calcular skewness manualmente
        if std > 0 and n > 2:
            skewness = float(np.mean(((self.returns - mean) / std) ** 3))
        else:
            skewness = 0.0
        
        # Calcular kurtosis manualmente (excess kurtosis)
        if std > 0 and n > 3:
            kurtosis = float(np.mean(((self.returns - mean) / std) ** 4) - 3)
        else:
            kurtosis = 0.0
        
        return {
            'mean': mean,
            'std': std,
            'min': float(np.min(self.returns)),
            'max': float(np.max(self.returns)),
            'median': float(np.median(self.returns)),
            'skewness': skewness,
            'kurtosis': kurtosis,
            'p5': float(np.percentile(self.returns, 5)),
            'p95': float(np.percentile(self.returns, 95)),
        }


@dataclass
class SyntheticScenariosResult:
    """
    Resultado da geração de cenários anuais sintéticos.
    
    Attributes:
        annual_returns: Array com retornos anuais sintéticos (em %)
        n_scenarios: Número de cenários gerados
        method: Método usado ('bootstrap' ou 'block_bootstrap')
        block_size: Tamanho do bloco (se block bootstrap)
        source_period: Período fonte dos dados mensais
        source_n_months: Número de meses fonte
        generation_time: Tempo de geração em segundos
        seed: Seed usado para reprodutibilidade
    """
    annual_returns: np.ndarray
    n_scenarios: int
    method: str
    block_size: Optional[int]
    source_period: str
    source_n_months: int
    generation_time: float = 0.0
    seed: Optional[int] = None
    
    # Estatísticas (calculadas automaticamente)
    mean: float = field(default=0.0, init=False)
    std: float = field(default=0.0, init=False)
    median: float = field(default=0.0, init=False)
    p5: float = field(default=0.0, init=False)
    p10: float = field(default=0.0, init=False)
    p25: float = field(default=0.0, init=False)
    p50: float = field(default=0.0, init=False)
    p75: float = field(default=0.0, init=False)
    p90: float = field(default=0.0, init=False)
    p95: float = field(default=0.0, init=False)
    min_val: float = field(default=0.0, init=False)
    max_val: float = field(default=0.0, init=False)
    skewness: float = field(default=0.0, init=False)
    kurtosis: float = field(default=0.0, init=False)
    
    def __post_init__(self):
        """Calcula estatísticas após inicialização."""
        self._calculate_statistics()
    
    def _calculate_statistics(self):
        """Calcula todas as estatísticas dos cenários."""
        self.mean = float(np.mean(self.annual_returns))
        self.std = float(np.std(self.annual_returns))
        self.median = float(np.median(self.annual_returns))
        self.min_val = float(np.min(self.annual_returns))
        self.max_val = float(np.max(self.annual_returns))
        
        self.p5 = float(np.percentile(self.annual_returns, 5))
        self.p10 = float(np.percentile(self.annual_returns, 10))
        self.p25 = float(np.percentile(self.annual_returns, 25))
        self.p50 = float(np.percentile(self.annual_returns, 50))
        self.p75 = float(np.percentile(self.annual_returns, 75))
        self.p90 = float(np.percentile(self.annual_returns, 90))
        self.p95 = float(np.percentile(self.annual_returns, 95))
        
        # Calcular skewness e kurtosis manualmente (sem scipy)
        n = len(self.annual_returns)
        if self.std > 0 and n > 2:
            standardized = (self.annual_returns - self.mean) / self.std
            self.skewness = float(np.mean(standardized ** 3))
        else:
            self.skewness = 0.0
        
        if self.std > 0 and n > 3:
            standardized = (self.annual_returns - self.mean) / self.std
            self.kurtosis = float(np.mean(standardized ** 4) - 3)  # Excess kurtosis
        else:
            self.kurtosis = 0.0
    
    def get_method_display_name(self) -> str:
        """Retorna nome amigável do método."""
        if self.method == 'bootstrap':
            return "Bootstrap Histórico"
        elif self.method == 'block_bootstrap':
            return f"Block Bootstrap (bloco {self.block_size}m)"
        return self.method
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'n_scenarios': self.n_scenarios,
            'method': self.method,
            'method_display': self.get_method_display_name(),
            'block_size': self.block_size,
            'source_period': self.source_period,
            'source_n_months': self.source_n_months,
            'generation_time': self.generation_time,
            'seed': self.seed,
            'statistics': {
                'mean': self.mean,
                'std': self.std,
                'median': self.median,
                'min': self.min_val,
                'max': self.max_val,
                'p5': self.p5,
                'p10': self.p10,
                'p25': self.p25,
                'p50': self.p50,
                'p75': self.p75,
                'p90': self.p90,
                'p95': self.p95,
                'skewness': self.skewness,
                'kurtosis': self.kurtosis,
            }
        }


class BootstrapEngine:
    """
    Motor de geração de cenários anuais sintéticos via Bootstrap.
    
    Suporta dois métodos:
    - Bootstrap Histórico: Sorteia 12 meses com reposição (I.I.D.)
    - Block Bootstrap: Sorteia blocos de meses consecutivos (preserva autocorrelação)
    """
    
    def __init__(self, monthly_data: MonthlyReturnData):
        """
        Inicializa o motor de bootstrap.
        
        Args:
            monthly_data: Dados mensais históricos
        """
        self.monthly_data = monthly_data
        self._validate_data()
    
    def _validate_data(self):
        """Valida os dados de entrada."""
        is_valid, errors = self.monthly_data.validate()
        if not is_valid:
            raise ValueError(f"Dados inválidos: {'; '.join(errors)}")
    
    def calculate_acf(self, max_lag: int = 12) -> np.ndarray:
        """
        Calcula a função de autocorrelação (ACF) dos retornos mensais.
        
        Args:
            max_lag: Número máximo de lags a calcular
            
        Returns:
            Array com valores ACF para cada lag (0 a max_lag)
        """
        returns = self.monthly_data.returns
        n = len(returns)
        mean = np.mean(returns)
        var = np.var(returns)
        
        if var == 0:
            return np.zeros(max_lag + 1)
        
        acf = np.zeros(max_lag + 1)
        acf[0] = 1.0  # ACF(0) = 1 por definição
        
        for lag in range(1, min(max_lag + 1, n)):
            cov = np.sum((returns[:-lag] - mean) * (returns[lag:] - mean)) / n
            acf[lag] = cov / var
        
        return acf
    
    def calculate_optimal_block_size(self) -> int:
        """
        Calcula o tamanho ótimo de bloco baseado na autocorrelação.
        
        Usa a regra de Politis & White (2004) simplificada:
        - Se ACF(1) < 0.2: sem autocorrelação significativa → bloco 1
        - Se 0.2 <= ACF(1) < 0.4: autocorrelação moderada → bloco 3
        - Se ACF(1) >= 0.4: autocorrelação forte → bloco 4-6
        
        Returns:
            Tamanho de bloco sugerido (1 a 6 meses)
        """
        acf = self.calculate_acf(max_lag=6)
        acf_1 = abs(acf[1])
        
        n = self.monthly_data.n_months
        
        if acf_1 < 0.2:
            return 1  # Sem autocorrelação significativa
        elif acf_1 < 0.4:
            return 3  # Autocorrelação moderada
        elif acf_1 < 0.6:
            return 4  # Autocorrelação forte
        else:
            # Regra de bandwidth ótimo: n^(1/3)
            return min(6, max(4, int(n ** (1/3))))
    
    def get_acf_diagnosis(self) -> Dict[str, Any]:
        """
        Retorna diagnóstico completo de autocorrelação.
        
        Returns:
            Dicionário com ACF, interpretação e sugestões
        """
        acf = self.calculate_acf(max_lag=6)
        optimal_block = self.calculate_optimal_block_size()
        acf_1 = acf[1]
        
        # Intervalo de confiança (95%) para ACF
        n = self.monthly_data.n_months
        ci_95 = 1.96 / np.sqrt(n)
        
        # Interpretação
        if abs(acf_1) < ci_95:
            interpretation = "Sem autocorrelação significativa"
            recommendation = "Bootstrap Histórico recomendado"
            use_block = False
        elif abs(acf_1) < 0.4:
            interpretation = "Autocorrelação moderada detectada"
            recommendation = f"Block Bootstrap sugerido (bloco {optimal_block}m)"
            use_block = True
        else:
            interpretation = "Autocorrelação forte detectada"
            recommendation = f"Block Bootstrap recomendado (bloco {optimal_block}m)"
            use_block = True
        
        return {
            'acf_values': acf.tolist(),
            'acf_lag1': float(acf_1),
            'confidence_interval_95': float(ci_95),
            'is_significant': abs(acf_1) >= ci_95,
            'optimal_block_size': optimal_block,
            'interpretation': interpretation,
            'recommendation': recommendation,
            'use_block_bootstrap': use_block
        }
    
    def generate_simple_bootstrap(
        self,
        n_scenarios: int = 10000,
        seed: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> SyntheticScenariosResult:
        """
        Gera cenários anuais via Bootstrap Histórico (I.I.D.).
        
        Para cada cenário:
        1. Sorteia 12 meses com reposição do histórico
        2. Compõe retorno anual: R = (1+r₁)×(1+r₂)×...×(1+r₁₂) - 1
        
        Args:
            n_scenarios: Número de cenários a gerar
            seed: Seed para reprodutibilidade
            progress_callback: Função callback(progress_percent) para atualizar UI
            
        Returns:
            SyntheticScenariosResult com cenários gerados e estatísticas
        """
        import time
        start_time = time.time()
        
        if seed is not None:
            np.random.seed(seed)
        
        # Converter retornos % para fatores (1 + r/100)
        factors = 1 + self.monthly_data.returns / 100
        n_months = len(factors)
        
        annual_returns = np.zeros(n_scenarios)
        
        # Processar em chunks para callback de progresso
        chunk_size = max(1, n_scenarios // 20)  # 5% de progresso por chunk
        
        for i in range(n_scenarios):
            # Sortear 12 meses com reposição
            sampled_indices = np.random.choice(n_months, size=12, replace=True)
            sampled_factors = factors[sampled_indices]
            
            # Compor retorno anual (produto dos fatores - 1)
            annual_factor = np.prod(sampled_factors)
            annual_returns[i] = (annual_factor - 1) * 100
            
            # Callback de progresso
            if progress_callback and (i + 1) % chunk_size == 0:
                progress = int((i + 1) / n_scenarios * 100)
                progress_callback(progress)
        
        generation_time = time.time() - start_time
        
        return SyntheticScenariosResult(
            annual_returns=annual_returns,
            n_scenarios=n_scenarios,
            method='bootstrap',
            block_size=None,
            source_period=self.monthly_data.period_range,
            source_n_months=self.monthly_data.n_months,
            generation_time=generation_time,
            seed=seed
        )
    
    def generate_block_bootstrap(
        self,
        n_scenarios: int = 10000,
        block_size: Optional[int] = None,
        seed: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> SyntheticScenariosResult:
        """
        Gera cenários anuais via Block Bootstrap (preserva autocorrelação).
        
        Para cada cenário:
        1. Sorteia blocos de meses consecutivos
        2. Concatena até ter 12 meses
        3. Compõe retorno anual
        
        Args:
            n_scenarios: Número de cenários a gerar
            block_size: Tamanho do bloco (None = automático)
            seed: Seed para reprodutibilidade
            progress_callback: Função callback(progress_percent) para atualizar UI
            
        Returns:
            SyntheticScenariosResult com cenários gerados e estatísticas
        """
        import time
        start_time = time.time()
        
        if seed is not None:
            np.random.seed(seed)
        
        # Determinar tamanho do bloco
        if block_size is None:
            block_size = self.calculate_optimal_block_size()
        
        # Validar tamanho do bloco
        block_size = max(1, min(block_size, 6))
        
        factors = 1 + self.monthly_data.returns / 100
        n_months = len(factors)
        
        # Número de blocos necessários para 12 meses
        n_blocks_needed = 12 // block_size + (1 if 12 % block_size else 0)
        
        annual_returns = np.zeros(n_scenarios)
        chunk_size = max(1, n_scenarios // 20)
        
        for i in range(n_scenarios):
            sampled_factors = []
            
            for _ in range(n_blocks_needed):
                # Sortear índice inicial do bloco (circular para permitir wrap)
                max_start = n_months - block_size
                if max_start < 0:
                    max_start = 0
                start_idx = np.random.randint(0, max_start + 1)
                
                # Extrair bloco
                block = factors[start_idx:start_idx + block_size].tolist()
                sampled_factors.extend(block)
            
            # Pegar exatamente 12 meses
            sampled_factors = sampled_factors[:12]
            
            # Compor retorno anual
            annual_factor = np.prod(sampled_factors)
            annual_returns[i] = (annual_factor - 1) * 100
            
            if progress_callback and (i + 1) % chunk_size == 0:
                progress = int((i + 1) / n_scenarios * 100)
                progress_callback(progress)
        
        generation_time = time.time() - start_time
        
        return SyntheticScenariosResult(
            annual_returns=annual_returns,
            n_scenarios=n_scenarios,
            method='block_bootstrap',
            block_size=block_size,
            source_period=self.monthly_data.period_range,
            source_n_months=self.monthly_data.n_months,
            generation_time=generation_time,
            seed=seed
        )
    
    def generate(
        self,
        method: BootstrapMethod = BootstrapMethod.SIMPLE,
        n_scenarios: int = 10000,
        block_size: Optional[int] = None,
        seed: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> SyntheticScenariosResult:
        """
        Método unificado para gerar cenários.
        
        Args:
            method: Método de bootstrap (SIMPLE ou BLOCK)
            n_scenarios: Número de cenários
            block_size: Tamanho do bloco (apenas para BLOCK)
            seed: Seed para reprodutibilidade
            progress_callback: Callback de progresso
            
        Returns:
            SyntheticScenariosResult
        """
        if method == BootstrapMethod.SIMPLE:
            return self.generate_simple_bootstrap(
                n_scenarios=n_scenarios,
                seed=seed,
                progress_callback=progress_callback
            )
        else:
            return self.generate_block_bootstrap(
                n_scenarios=n_scenarios,
                block_size=block_size,
                seed=seed,
                progress_callback=progress_callback
            )


# =============================================================================
# FUNÇÕES DE IMPORTAÇÃO/EXPORTAÇÃO CSV
# =============================================================================

def generate_monthly_template_csv() -> str:
    """
    Gera template CSV para preenchimento de dados mensais.
    
    Formato:
        Nº do Mês;Retorno do Mês (%);Observação
        1;0.00;
        2;0.00;
        ...
    
    Returns:
        String com conteúdo CSV do template
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow(['Nº do Mês', 'Retorno do Mês (%)', 'Observação'])
    
    # Gerar 12 linhas de exemplo
    for month_num in range(1, 13):
        writer.writerow([str(month_num), '', ''])
    
    return output.getvalue()


def parse_monthly_csv(csv_content: str) -> MonthlyReturnData:
    """
    Faz parse de CSV com dados mensais.
    
    Aceita dois formatos:
    1. Novo formato: Nº do Mês;Retorno do Mês (%);Observação
    2. Formato legado: Período;Retorno (%);Notas (com Mmm/AAAA)
    
    Args:
        csv_content: Conteúdo do arquivo CSV
        
    Returns:
        MonthlyReturnData com dados parseados
        
    Raises:
        ValueError: Se formato inválido
    """
    # Detectar delimitador
    delimiter = ';' if ';' in csv_content else ','
    
    lines = csv_content.strip().split('\n')
    
    # Pular linhas de comentário (começam com #)
    data_lines = [l for l in lines if not l.strip().startswith('#')]
    
    if len(data_lines) < 2:
        raise ValueError("CSV deve ter pelo menos header + 1 linha de dados")
    
    reader = csv.reader(data_lines, delimiter=delimiter)
    
    # Ler header para detectar formato
    header = next(reader)
    header_lower = [h.lower().strip() for h in header]
    
    # Detectar se é formato novo (Nº do Mês) ou legado (Período com Mmm/AAAA)
    is_new_format = any('mês' in h or 'mes' in h or 'month' in h for h in header_lower)
    
    periods = []
    returns = []
    notes = []
    
    for row_num, row in enumerate(reader, start=2):
        if len(row) < 2:
            continue
        
        first_col = row[0].strip()
        
        # Pular linhas vazias
        if not first_col:
            continue
        
        # Parse do período/número
        if '/' in first_col:
            # Formato legado: Mmm/AAAA
            period = first_col
        else:
            # Formato novo: número sequencial
            try:
                month_num = int(first_col)
                period = f"Mês {month_num}"
            except ValueError:
                raise ValueError(f"Linha {row_num}: '{first_col}' não é número válido")
        
        # Parse do retorno (aceitar vírgula ou ponto como decimal)
        return_str = row[1].strip().replace(',', '.').replace('%', '')
        
        # Pular linhas sem retorno preenchido
        if not return_str:
            continue
            
        try:
            return_val = float(return_str)
        except ValueError:
            raise ValueError(f"Linha {row_num}: Retorno '{row[1]}' não é número válido")
        
        # Validar intervalo
        if return_val <= -100:
            raise ValueError(f"Linha {row_num}: Retorno {return_val}% não pode ser -100% ou menor")
        if return_val > 1000:
            raise ValueError(f"Linha {row_num}: Retorno {return_val}% não pode ser maior que 1000%")
        
        periods.append(period)
        returns.append(return_val)
        notes.append(row[2].strip() if len(row) > 2 else '')
    
    if len(periods) < 12:
        raise ValueError(f"Mínimo de 12 meses necessário. Encontrados: {len(periods)}")
    
    return MonthlyReturnData(
        periods=periods,
        returns=np.array(returns),
        notes=notes if any(notes) else None
    )


def export_scenarios_csv(
    result: SyntheticScenariosResult,
    include_metadata: bool = True
) -> str:
    """
    Exporta cenários gerados para CSV.
    
    Args:
        result: Resultado da geração de cenários
        include_metadata: Se True, inclui metadados como comentários
        
    Returns:
        String com conteúdo CSV
    """
    output = io.StringIO()
    
    # Metadados como comentários
    if include_metadata:
        output.write(f"# Método: {result.get_method_display_name()}\n")
        output.write(f"# Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        output.write(f"# Período Fonte: {result.source_period}\n")
        output.write(f"# Meses Fonte: {result.source_n_months}\n")
        output.write(f"# Nº Cenários: {result.n_scenarios:,}\n")
        output.write(f"# Tempo de Geração: {result.generation_time:.2f}s\n")
        if result.seed is not None:
            output.write(f"# Seed: {result.seed}\n")
        output.write(f"# \n")
        output.write(f"# Estatísticas:\n")
        output.write(f"# Média: {result.mean:.2f}%\n")
        output.write(f"# Desvio Padrão: {result.std:.2f}%\n")
        output.write(f"# Mediana: {result.median:.2f}%\n")
        output.write(f"# P5: {result.p5:.2f}% | P95: {result.p95:.2f}%\n")
        output.write(f"# Mínimo: {result.min_val:.2f}% | Máximo: {result.max_val:.2f}%\n")
        output.write(f"# Skewness: {result.skewness:.4f} | Curtose: {result.kurtosis:.4f}\n")
        output.write(f"# \n")
    
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Cenário', 'Retorno Anual (%)'])
    
    for i, ret in enumerate(result.annual_returns, start=1):
        writer.writerow([i, f'{ret:.4f}'])
    
    return output.getvalue()


def import_scenarios_csv(csv_content: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Importa cenários de um CSV previamente exportado.
    
    Args:
        csv_content: Conteúdo do arquivo CSV
        
    Returns:
        Tuple (array de retornos anuais, dicionário de metadados)
    """
    delimiter = ';' if ';' in csv_content else ','
    lines = csv_content.strip().split('\n')
    
    metadata = {}
    data_lines = []
    
    for line in lines:
        if line.strip().startswith('#'):
            # Parse de metadados
            if ':' in line:
                key_val = line[1:].strip().split(':', 1)
                if len(key_val) == 2:
                    key = key_val[0].strip()
                    val = key_val[1].strip()
                    metadata[key] = val
        else:
            data_lines.append(line)
    
    if len(data_lines) < 2:
        raise ValueError("CSV deve ter pelo menos header + 1 linha de dados")
    
    reader = csv.reader(data_lines, delimiter=delimiter)
    header = next(reader)  # Pular header
    
    returns = []
    for row in reader:
        if len(row) >= 2:
            try:
                ret = float(row[1].strip().replace(',', '.'))
                returns.append(ret)
            except ValueError:
                continue
    
    if len(returns) < 100:
        raise ValueError(f"Poucos cenários encontrados: {len(returns)}. Mínimo: 100")
    
    return np.array(returns), metadata


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def estimate_generation_time(n_scenarios: int) -> float:
    """
    Estima tempo de geração em segundos.
    
    Args:
        n_scenarios: Número de cenários
        
    Returns:
        Tempo estimado em segundos
    """
    # Baseado em benchmarks: ~100k cenários/segundo em hardware típico
    return n_scenarios / 100000 * 5  # ~5 segundos para 100k


def format_time_estimate(seconds: float) -> str:
    """
    Formata estimativa de tempo para exibição.
    
    Args:
        seconds: Tempo em segundos
        
    Returns:
        String formatada (ex: "<1s", "~5s", "~30s")
    """
    if seconds < 1:
        return "<1s"
    elif seconds < 10:
        return f"~{int(seconds)}s"
    elif seconds < 60:
        return f"~{int(seconds)}s"
    else:
        minutes = int(seconds / 60)
        return f"~{minutes}min"


# =============================================================================
# CLASSE PARA INTEGRAÇÃO COM MONTE CARLO
# =============================================================================

@dataclass
class SyntheticDataConfig:
    """
    Configuração de dados sintéticos para uso no Monte Carlo.
    
    Esta classe é usada para passar os cenários gerados para o motor
    Monte Carlo existente.
    """
    annual_returns: np.ndarray
    method: str
    source_info: str
    n_scenarios: int
    statistics: Dict[str, float]
    
    @classmethod
    def from_result(cls, result: SyntheticScenariosResult) -> 'SyntheticDataConfig':
        """Cria configuração a partir de resultado de bootstrap."""
        return cls(
            annual_returns=result.annual_returns,
            method=result.get_method_display_name(),
            source_info=f"{result.source_period} ({result.source_n_months} meses)",
            n_scenarios=result.n_scenarios,
            statistics={
                'mean': result.mean,
                'std': result.std,
                'p5': result.p5,
                'p95': result.p95,
                'min': result.min_val,
                'max': result.max_val,
            }
        )
