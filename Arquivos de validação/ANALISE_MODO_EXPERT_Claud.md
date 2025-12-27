# 🔬 Análise do Modo Expert - PyInvest

## 📋 Sumário Executivo

O **Modo Expert** é uma funcionalidade que permite ao usuário utilizar **dados históricos reais** de rendimentos para gerar simulações Monte Carlo mais realistas, em vez de depender apenas de distribuições estatísticas teóricas.

---

## 🏗️ Arquitetura Atual

### Componentes Envolvidos

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MODO EXPERT                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────┐         ┌─────────────────────────────────┐   │
│  │   UI/FRONTEND       │         │     CORE/BACKEND                 │   │
│  ├─────────────────────┤         ├─────────────────────────────────┤   │
│  │                     │         │                                  │   │
│  │ window_modern.py    │         │ statistics.py                    │   │
│  │ ├─ check_expert_mode│────────▶│ ├─ bootstrap_returns()          │   │
│  │ ├─ combo_method     │         │ ├─ normal_returns()             │   │
│  │ ├─ btn_historical   │         │ └─ t_student_returns()          │   │
│  │ ├─ historical_status│         │                                  │   │
│  │ └─ expert_options   │         │ monte_carlo.py                   │   │
│  │                     │         │ ├─ MonteCarloInput               │   │
│  │ historical_dialog.py│         │ ├─ MonteCarloEngine              │   │
│  │ └─ HistoricalReturn │         │ └─ MonteCarloResult              │   │
│  │     Dialog          │         │                                  │   │
│  │                     │         │                                  │   │
│  └─────────────────────┘         └─────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo de Dados

### 1. Ativação do Modo Expert

```
┌──────────────────┐     ┌───────────────────────────────────┐
│ Usuário clica em │────▶│ _on_expert_mode_changed(checked)  │
│ "🔬 Modo Expert" │     │                                   │
└──────────────────┘     │ 1. expert_options.setVisible(True)│
                         │ 2. status_bar.showMessage()       │
                         └───────────────────────────────────┘
```

### 2. Configuração de Dados Históricos

```
┌────────────────────┐     ┌─────────────────────────────────────┐
│ Usuário clica em   │────▶│ _on_open_historical()               │
│ "📊 Dados de       │     │                                     │
│  Rendimento"       │     │ 1. Abre HistoricalReturnsDialog     │
└────────────────────┘     │ 2. Conecta returns_confirmed Signal │
                           └─────────────────────────────────────┘
                                          │
                                          ▼
                           ┌─────────────────────────────────────┐
                           │ _on_historical_confirmed(returns)   │
                           │                                     │
                           │ 1. self.historical_returns = returns│
                           │ 2. _update_historical_status()      │
                           └─────────────────────────────────────┘
```

### 3. Validação e Preparação (ao clicar Calcular)

```
┌───────────────┐     ┌─────────────────────────────────────────────────┐
│ _validate_    │────▶│ MODO EXPERT ATIVADO?                            │
│ inputs()      │     │                                                 │
└───────────────┘     │ SE is_expert_mode AND has_historical >= 2:     │
                      │   ├─ Derivar rentabilidade dos dados históricos │
                      │   │   rent_range.deterministic = avg_return     │
                      │   ├─ Aporte opcional (assume 0 se vazio)        │
                      │   └─ Capital obrigatório                        │
                      │                                                 │
                      │ Criar MonteCarloInput:                          │
                      │   mc_input.expert_mode = True                   │
                      │   mc_input.historical_returns = [...]           │
                      │   mc_input.simulation_method = 'bootstrap'      │
                      └─────────────────────────────────────────────────┘
```

### 4. Execução da Simulação

```
┌─────────────────────┐     ┌─────────────────────────────────────┐
│ MonteCarloEngine    │────▶│ run()                               │
│ .run()              │     │                                     │
└─────────────────────┘     │ 🚨 PROBLEMA: Não usa expert_mode!   │
                            │                                     │
                            │ Sempre executa:                     │
                            │ - _calculate_monte_carlo_vectorized │
                            │   que usa ParameterRange.sample()   │
                            │   (distribuição Normal truncada)    │
                            │                                     │
                            │ IGNORA:                             │
                            │ - bootstrap_returns()               │
                            │ - normal_returns()                  │
                            │ - t_student_returns()               │
                            └─────────────────────────────────────┘
```

---

## 🐛 BUGS IDENTIFICADOS

### BUG #1: Modo Expert Não Implementado no Motor (CRÍTICO) ⚠️

**Descrição:** O `MonteCarloEngine.run()` **ignora completamente** os atributos `expert_mode`, `historical_returns` e `simulation_method` que são definidos em `_validate_inputs()`.

**Localização:** `core/monte_carlo.py` → `MonteCarloEngine.run()` (linha 354)

**Evidência:**
```python
# Em window_modern.py (linhas 1446-1452) - ATRIBUTOS SÃO DEFINIDOS:
if is_expert_mode:
    mc_input.expert_mode = True
    mc_input.historical_returns = self.historical_returns
    mc_input.simulation_method = ['bootstrap', 'normal', 't_student'][...]

# Em monte_carlo.py - MonteCarloInput NÃO TEM ESSES CAMPOS:
@dataclass
class MonteCarloInput:
    capital_inicial: ParameterRange
    aporte_mensal: ParameterRange
    rentabilidade_anual: ParameterRange
    periodo_anos: int
    meta: float = 0.0
    n_simulations: int = 5000
    start_date: date = field(default_factory=date.today)
    events_manager: object = None
    # ❌ FALTAM: expert_mode, historical_returns, simulation_method
```

**Impacto:** 
- Usuário pensa que está usando Bootstrap com dados reais
- Na verdade, está usando distribuição Normal truncada baseada em min/max
- Resultados podem diferir significativamente da expectativa

**Prioridade:** 🔴 CRÍTICA

---

### BUG #2: Funções de Simulação Importadas mas Não Usadas

**Descrição:** As funções `bootstrap_returns()`, `normal_returns()` e `t_student_returns()` são importadas em `window_modern.py` mas **nunca são chamadas**.

**Localização:** `ui/window_modern.py` (linha 32)

**Evidência:**
```python
# Importadas:
from core.statistics import (
    ...
    bootstrap_returns, normal_returns, t_student_returns,
    ...
)

# Mas grep não encontra nenhuma chamada além do import
```

**Impacto:** Código morto, confusão para desenvolvedores

**Prioridade:** 🟡 MÉDIA

---

### BUG #3: Atributos Dinâmicos em Dataclass

**Descrição:** O código tenta adicionar atributos (`expert_mode`, `historical_returns`, `simulation_method`) dinamicamente a uma `@dataclass`, o que funciona em Python mas é má prática.

**Localização:** `ui/window_modern.py` (linhas 1447-1452)

**Evidência:**
```python
mc_input = MonteCarloInput(...)  # Dataclass com campos fixos

# Adição dinâmica (funciona, mas é frágil):
mc_input.expert_mode = True
mc_input.historical_returns = self.historical_returns
mc_input.simulation_method = 'bootstrap'
```

**Impacto:** 
- Sem validação de tipo
- IDE não oferece autocomplete
- Fácil de introduzir typos

**Prioridade:** 🟡 MÉDIA

---

### BUG #4: ProjectionChartExpert Não Utilizado

**Descrição:** A classe `ProjectionChartExpert` em `advanced_widgets.py` é definida e exportada, mas nunca é instanciada na interface atual.

**Localização:** `ui/advanced_widgets.py` (linha 495)

**Evidência:**
```python
# window_modern.py linha 2069:
# (Gráfico Expert removido - interface simplificada para 3 abas)
```

**Impacto:** Código morto, aumenta complexidade

**Prioridade:** 🟢 BAIXA

---

## 🔧 CORREÇÕES SUGERIDAS

### Correção #1: Implementar Modo Expert no MonteCarloEngine

```python
# core/monte_carlo.py

@dataclass
class MonteCarloInput:
    capital_inicial: ParameterRange
    aporte_mensal: ParameterRange
    rentabilidade_anual: ParameterRange
    periodo_anos: int
    meta: float = 0.0
    n_simulations: int = 5000
    start_date: date = field(default_factory=date.today)
    events_manager: object = None
    
    # NOVOS CAMPOS PARA MODO EXPERT:
    expert_mode: bool = False
    historical_returns: List[float] = field(default_factory=list)
    simulation_method: str = 'normal'  # 'bootstrap', 'normal', 't_student'


class MonteCarloEngine:
    
    def run(self) -> MonteCarloResult:
        # ... código existente ...
        
        # Verificar se há parâmetros probabilísticos
        has_mc = self.inputs.has_probabilistic_params()
        
        # NOVA LÓGICA: Modo Expert
        if self.inputs.expert_mode and len(self.inputs.historical_returns) >= 2:
            has_mc = True  # Forçar Monte Carlo
            
            # Gerar retornos baseado no método escolhido
            if self.inputs.simulation_method == 'bootstrap':
                annual_returns = bootstrap_returns(
                    self.inputs.historical_returns,
                    years,
                    self.inputs.n_simulations
                )
            elif self.inputs.simulation_method == 'normal':
                mean_ret = np.mean(self.inputs.historical_returns)
                std_ret = np.std(self.inputs.historical_returns)
                annual_returns = normal_returns(mean_ret, std_ret, years, self.inputs.n_simulations)
            elif self.inputs.simulation_method == 't_student':
                mean_ret = np.mean(self.inputs.historical_returns)
                std_ret = np.std(self.inputs.historical_returns)
                annual_returns = t_student_returns(mean_ret, std_ret, years, self.inputs.n_simulations)
            
            # Usar retornos gerados para simular
            all_balances = self._calculate_with_annual_returns(annual_returns)
        
        elif has_mc:
            # Modo atual: Monte Carlo com ranges
            all_balances, sampled_capitals, sampled_monthlies, sampled_rates = \
                self._calculate_monte_carlo_with_events(monthly_events)
        
        # ... resto do código ...
```

### Correção #2: Novo Método para Calcular com Retornos Anuais

```python
# core/monte_carlo.py

def _calculate_with_annual_returns(
    self,
    annual_returns: np.ndarray  # Shape: (n_simulations, n_years)
) -> np.ndarray:
    """
    Calcula saldos usando retornos anuais gerados pelo Modo Expert.
    
    Args:
        annual_returns: Matriz (n_sim, n_years) com retornos anuais
        
    Returns:
        all_balances: Matriz (n_sim, n_months+1) com saldos mensais
    """
    n_sim = annual_returns.shape[0]
    years = annual_returns.shape[1]
    total_months = years * 12
    
    # Valores iniciais
    capitals = self.inputs.capital_inicial.sample(n_sim)
    monthlies = self.inputs.aporte_mensal.sample(n_sim)
    
    all_balances = np.zeros((n_sim, total_months + 1))
    all_balances[:, 0] = capitals
    
    for year in range(years):
        # Taxa anual para mensal
        annual_rate = annual_returns[:, year]  # Shape: (n_sim,)
        monthly_rate = (1 + annual_rate / 100) ** (1/12) - 1
        
        for month in range(12):
            month_idx = year * 12 + month + 1
            all_balances[:, month_idx] = (
                all_balances[:, month_idx - 1] * (1 + monthly_rate) + monthlies
            )
    
    return all_balances
```

### Correção #3: Remover Código Morto

```python
# ui/window_modern.py - Remover imports não usados:
# ANTES:
from core.statistics import (
    ...
    bootstrap_returns, normal_returns, t_student_returns,  # ❌ REMOVER
    ...
)

# ui/advanced_widgets.py - Mover ou remover ProjectionChartExpert se não usado
```

---

## 📊 Diagrama de Fluxo Corrigido (Proposta)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FLUXO CORRIGIDO                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  USUÁRIO                                                                 │
│    │                                                                     │
│    ▼                                                                     │
│  [Ativa Modo Expert] ──▶ [Seleciona Método] ──▶ [Adiciona Dados Hist.]  │
│                              │                         │                 │
│                              │                         ▼                 │
│                              │            ┌─────────────────────────┐   │
│                              │            │ historical_returns[]    │   │
│                              │            │ [2020: 15%, 2021: -5%...│   │
│                              │            └─────────────────────────┘   │
│                              ▼                         │                 │
│                    ┌─────────────────┐                 │                 │
│                    │ simulation_method│                 │                 │
│                    │ ├─ bootstrap    │                 │                 │
│                    │ ├─ normal       │                 │                 │
│                    │ └─ t_student    │                 │                 │
│                    └─────────────────┘                 │                 │
│                              │                         │                 │
│                              └────────────┬────────────┘                 │
│                                           │                              │
│                                           ▼                              │
│                              ┌─────────────────────────┐                │
│                              │ MonteCarloInput         │                │
│                              │ ├─ expert_mode = True   │                │
│                              │ ├─ historical_returns   │                │
│                              │ └─ simulation_method    │                │
│                              └─────────────────────────┘                │
│                                           │                              │
│                                           ▼                              │
│                              ┌─────────────────────────┐                │
│                              │ MonteCarloEngine.run()  │                │
│                              │                         │                │
│                              │ IF expert_mode:         │                │
│                              │   ├─ bootstrap_returns()│                │
│                              │   ├─ normal_returns()   │                │
│                              │   └─ t_student_returns()│                │
│                              │                         │                │
│                              │ ELSE:                   │                │
│                              │   └─ ParameterRange     │                │
│                              │       .sample()         │                │
│                              └─────────────────────────┘                │
│                                           │                              │
│                                           ▼                              │
│                              ┌─────────────────────────┐                │
│                              │ MonteCarloResult        │                │
│                              │ (com estatísticas)      │                │
│                              └─────────────────────────┘                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📝 Resumo das Ações

| # | Bug | Prioridade | Ação | Arquivos |
|---|-----|------------|------|----------|
| 1 | Modo Expert não implementado | 🔴 CRÍTICA | Implementar lógica no MonteCarloEngine | `monte_carlo.py` |
| 2 | Funções não usadas | 🟡 MÉDIA | Conectar ao engine ou remover | `window_modern.py`, `monte_carlo.py` |
| 3 | Atributos dinâmicos | 🟡 MÉDIA | Adicionar campos ao dataclass | `monte_carlo.py` |
| 4 | ProjectionChartExpert órfão | 🟢 BAIXA | Remover ou reintegrar | `advanced_widgets.py` |

---

## ⏭️ Próximos Passos

1. **Fase 1 (Crítica):** Implementar Correção #1 e #2 no `monte_carlo.py`
2. **Fase 2 (Melhoria):** Testes unitários para validar os três métodos de simulação
3. **Fase 3 (Limpeza):** Remover código morto e consolidar exports

---

*Documento gerado em: Dezembro 2024*
*Versão analisada: PyInvest v4.9*
