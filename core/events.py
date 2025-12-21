"""
PyInvest - Eventos Extraordinários
Sistema para gerenciar aportes extras e resgates programados.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import numpy as np


@dataclass
class ExtraordinaryEvent:
    """
    Representa um evento extraordinário (aporte extra ou resgate).
    
    Attributes:
        date: Data do evento
        description: Descrição do evento (máx 35 caracteres)
        deposit: Valor do aporte extra (positivo)
        withdrawal: Valor do resgate (positivo, será subtraído)
    """
    date: date
    description: str
    deposit: float = 0.0
    withdrawal: float = 0.0
    
    def __post_init__(self):
        """Valida e normaliza os dados."""
        # Limitar descrição a 35 caracteres
        if len(self.description) > 35:
            self.description = self.description[:35]
        
        # Garantir valores não negativos
        self.deposit = max(0.0, self.deposit)
        self.withdrawal = max(0.0, self.withdrawal)
    
    @property
    def net_amount(self) -> float:
        """Retorna o valor líquido (positivo = entrada, negativo = saída)."""
        return self.deposit - self.withdrawal
    
    @property
    def month_key(self) -> str:
        """Retorna chave ano-mês para agrupamento."""
        return f"{self.date.year}-{self.date.month:02d}"
    
    @property
    def year(self) -> int:
        """Retorna o ano do evento."""
        return self.date.year
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            'date': self.date.strftime('%d/%m/%Y'),
            'description': self.description,
            'deposit': self.deposit,
            'withdrawal': self.withdrawal
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExtraordinaryEvent':
        """Cria evento a partir de dicionário."""
        date_str = data.get('date', '')
        
        # Tentar diferentes formatos de data
        for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Formato de data inválido: {date_str}")
        
        return cls(
            date=parsed_date,
            description=data.get('description', ''),
            deposit=float(data.get('deposit', 0) or 0),
            withdrawal=float(data.get('withdrawal', 0) or 0)
        )


@dataclass
class EventsManager:
    """
    Gerenciador de eventos extraordinários.
    Consolida eventos por mês e calcula impactos.
    """
    events: List[ExtraordinaryEvent] = field(default_factory=list)
    
    def add_event(self, event: ExtraordinaryEvent):
        """Adiciona um evento à lista."""
        self.events.append(event)
        self._sort_events()
    
    def remove_event(self, index: int):
        """Remove evento por índice."""
        if 0 <= index < len(self.events):
            self.events.pop(index)
    
    def clear(self):
        """Remove todos os eventos."""
        self.events.clear()
    
    def _sort_events(self):
        """Ordena eventos por data."""
        self.events.sort(key=lambda e: e.date)
    
    def get_monthly_consolidated(self, start_date: date, months: int) -> Dict[int, Tuple[float, float]]:
        """
        Consolida eventos por mês relativo ao início da simulação.
        
        Args:
            start_date: Data de início da simulação
            months: Número total de meses da simulação
            
        Returns:
            Dict com mês relativo (0 a months-1) -> (total_deposits, total_withdrawals)
        """
        consolidated = {}
        
        for event in self.events:
            # Calcular mês relativo
            months_diff = (event.date.year - start_date.year) * 12 + (event.date.month - start_date.month)
            
            # Ignorar eventos fora do período
            if months_diff < 0 or months_diff >= months:
                continue
            
            if months_diff not in consolidated:
                consolidated[months_diff] = [0.0, 0.0]
            
            consolidated[months_diff][0] += event.deposit
            consolidated[months_diff][1] += event.withdrawal
        
        # Converter para tuplas
        return {k: tuple(v) for k, v in consolidated.items()}
    
    def get_yearly_summary(self, start_year: int, years: int) -> Dict[int, Tuple[float, float]]:
        """
        Retorna resumo anual de eventos.
        
        Args:
            start_year: Ano de início
            years: Número de anos
            
        Returns:
            Dict com ano relativo (0 a years) -> (total_deposits, total_withdrawals)
        """
        summary = {y: (0.0, 0.0) for y in range(years + 1)}
        
        for event in self.events:
            year_rel = event.year - start_year
            
            if 0 <= year_rel <= years:
                deposits, withdrawals = summary[year_rel]
                summary[year_rel] = (
                    deposits + event.deposit,
                    withdrawals + event.withdrawal
                )
        
        return summary
    
    def export_to_csv(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """Exporta eventos para CSV."""
        try:
            import csv
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['Data', 'Evento', 'Aporte Extra (R$)', 'Resgate (R$)'])
                
                for event in self.events:
                    writer.writerow([
                        event.date.strftime('%d/%m/%Y'),
                        event.description,
                        f"{event.deposit:.2f}".replace('.', ',') if event.deposit > 0 else '',
                        f"{event.withdrawal:.2f}".replace('.', ',') if event.withdrawal > 0 else ''
                    ])
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    def import_from_csv(self, filepath: str) -> Tuple[bool, Optional[str], int]:
        """
        Importa eventos de CSV.
        
        Returns:
            Tuple (success, error_message, count_imported)
        """
        try:
            import csv
            
            imported = []
            
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                for row in reader:
                    try:
                        # Normalizar nomes de colunas
                        date_str = row.get('Data', row.get('data', ''))
                        desc = row.get('Evento', row.get('evento', row.get('Descrição', '')))
                        
                        deposit_str = row.get('Aporte Extra (R$)', row.get('Aporte', row.get('aporte', '0')))
                        withdrawal_str = row.get('Resgate (R$)', row.get('Resgate', row.get('resgate', '0')))
                        
                        # Limpar valores monetários
                        def clean_currency(s):
                            if not s:
                                return 0.0
                            s = s.replace('R$', '').replace(' ', '').strip()
                            if ',' in s and '.' in s:
                                s = s.replace('.', '').replace(',', '.')
                            elif ',' in s:
                                s = s.replace(',', '.')
                            return float(s) if s else 0.0
                        
                        event = ExtraordinaryEvent(
                            date=datetime.strptime(date_str, '%d/%m/%Y').date(),
                            description=desc[:35],
                            deposit=clean_currency(deposit_str),
                            withdrawal=clean_currency(withdrawal_str)
                        )
                        imported.append(event)
                        
                    except Exception as e:
                        continue  # Pular linhas com erro
            
            if imported:
                self.events.extend(imported)
                self._sort_events()
                return True, None, len(imported)
            else:
                return False, "Nenhum evento válido encontrado no arquivo.", 0
                
        except FileNotFoundError:
            return False, "Arquivo não encontrado.", 0
        except Exception as e:
            return False, str(e), 0
    
    @property
    def total_deposits(self) -> float:
        """Total de aportes extras."""
        return sum(e.deposit for e in self.events)
    
    @property
    def total_withdrawals(self) -> float:
        """Total de resgates."""
        return sum(e.withdrawal for e in self.events)
    
    @property
    def count(self) -> int:
        """Número de eventos."""
        return len(self.events)
    
    def __len__(self) -> int:
        return len(self.events)


@dataclass
class InsolvencyEvent:
    """Marca um ponto de insolvência na simulação."""
    month: int
    year_relative: float
    balance_before: float
    withdrawal_attempted: float
    scenario_id: int = 0  # Para Monte Carlo


def apply_extraordinary_events(
    balances: np.ndarray,
    monthly_events: Dict[int, Tuple[float, float]],
    monthly_rate: float
) -> Tuple[np.ndarray, List[InsolvencyEvent]]:
    """
    Aplica eventos extraordinários a uma série de saldos.
    
    Args:
        balances: Array de saldos mensais
        monthly_events: Dict mês -> (deposits, withdrawals)
        monthly_rate: Taxa mensal de juros
        
    Returns:
        Tuple (modified_balances, insolvency_events)
    """
    modified = balances.copy()
    insolvencies = []
    
    for month, (deposits, withdrawals) in monthly_events.items():
        if month >= len(modified):
            continue
        
        # Aplicar aporte extra
        if deposits > 0:
            # Recalcular juros sobre o novo valor
            for m in range(month, len(modified)):
                if m == month:
                    modified[m] += deposits
                else:
                    # O aporte extra também rende juros
                    periods = m - month
                    extra_with_interest = deposits * ((1 + monthly_rate) ** periods)
                    modified[m] = modified[m] + extra_with_interest - deposits * ((1 + monthly_rate) ** (periods - 1)) if periods > 0 else modified[m]
        
        # Aplicar resgate
        if withdrawals > 0:
            if modified[month] < withdrawals:
                # Insolvência!
                insolvencies.append(InsolvencyEvent(
                    month=month,
                    year_relative=month / 12,
                    balance_before=modified[month],
                    withdrawal_attempted=withdrawals
                ))
                # Zerar saldo deste ponto em diante
                modified[month:] = 0
            else:
                # Recalcular série após resgate
                for m in range(month, len(modified)):
                    if m == month:
                        modified[m] -= withdrawals
                    # Ajuste simplificado - o resgate remove capital que renderia juros
    
    return modified, insolvencies


def apply_events_to_simulation(
    initial_balance: float,
    monthly_contribution: float,
    monthly_rate: float,
    months: int,
    events_manager: EventsManager,
    start_date: date
) -> Tuple[np.ndarray, List[InsolvencyEvent]]:
    """
    Executa simulação completa com eventos extraordinários.
    
    Args:
        initial_balance: Saldo inicial
        monthly_contribution: Aporte mensal regular
        monthly_rate: Taxa mensal
        months: Número de meses
        events_manager: Gerenciador de eventos
        start_date: Data de início
        
    Returns:
        Tuple (balances_array, insolvency_events)
    """
    # Obter eventos consolidados
    monthly_events = events_manager.get_monthly_consolidated(start_date, months)
    
    # Array de saldos
    balances = np.zeros(months + 1)
    balances[0] = initial_balance
    
    insolvencies = []
    is_insolvent = False
    
    for m in range(1, months + 1):
        if is_insolvent:
            balances[m] = 0
            continue
        
        # Saldo anterior + juros + aporte regular
        balances[m] = balances[m-1] * (1 + monthly_rate) + monthly_contribution
        
        # Aplicar eventos do mês
        if m in monthly_events:
            deposits, withdrawals = monthly_events[m]
            
            # Adicionar aportes extras
            balances[m] += deposits
            
            # Verificar e aplicar resgates
            if withdrawals > 0:
                if balances[m] < withdrawals:
                    # Insolvência
                    insolvencies.append(InsolvencyEvent(
                        month=m,
                        year_relative=m / 12,
                        balance_before=balances[m],
                        withdrawal_attempted=withdrawals
                    ))
                    balances[m] = 0
                    is_insolvent = True
                else:
                    balances[m] -= withdrawals
    
    return balances, insolvencies
