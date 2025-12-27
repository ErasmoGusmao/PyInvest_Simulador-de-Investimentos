# 🔴 Relatório de Bug: Taxa de Retorno Variando Ano-a-Ano

## Resumo Executivo

**Bug Identificado:** Os percentis e extremos (P5, P10, P50, P90, P95, Min, Max) estão sendo calculados **por mês independentemente**, criando "cenários Frankenstein" que não representam nenhuma simulação real.

**Impacto:** Afeta TODAS as saídas visuais e numéricas da aplicação.

**Severidade:** 🔴 CRÍTICO

---

## 1. Análise Completa do Impacto

### Componentes Afetados

| Componente | Dados Usados | Status |
|------------|--------------|--------|
| **Gráfico Evolução Patrimonial** | `balances_p5`, `balances_p95`, `balances_min`, `balances_max`, `balances_mean` | ❌ AFETADO |
| **Tabela Projeção Anual** | `yearly_projection` (P5, P10, P50, P90, P95, Min, Max) | ❌ AFETADO |
| **Histograma** | `sampled_final_balances` | ✅ **CORRETO** |
| **Estatísticas Percentis** | `percentile_stats` (calculado de final_balances) | ✅ **CORRETO** |
| **Cenários Representativos** | Extraídos de simulações reais | ✅ **CORRETO** |
| **Métricas de Risco** | VaR, CVaR calculados de final_balances | ✅ **CORRETO** |
| **Cards de Resumo** | `final_balance_mean`, `final_balance_min`, `final_balance_max` | ⚠️ Min/Max afetados |

### Por que o Histograma está CORRETO?

O histograma usa `sampled_final_balances = all_balances[:, -1]`, que são os saldos finais de TODAS as simulações. Cada saldo final corresponde a uma simulação real com parâmetros consistentes.

```python
# CORRETO - usa saldos finais de simulações reais
sampled_final_balances = all_balances[:, -1]  # Shape: (50000,)
```

### Por que o Gráfico de Evolução está INCORRETO?

O gráfico usa `balances_p5 = np.percentile(all_balances, 5, axis=0)`, que calcula o P5 para cada mês independentemente:

```python
# INCORRETO - mistura simulações diferentes
balances_p5 = np.percentile(all_balances, 5, axis=0)  # Shape: (145,)
# O P5 do mês 12 pode ser da Simulação #4523
# O P5 do mês 24 pode ser da Simulação #8901
```

---

## 2. Evidências do Bug

### Parâmetros da Simulação
```
Capital Inicial: R$ 1.400.000,00 (fixo, sem range)
Aporte Mensal: R$ 0 (base), máx R$ 8.500
Taxa Anual: 10.00% (mín) | 13.20% (base) | 22.00% (máx)
Período: 12 anos
Simulações: 50.000
```

### Análise do MÁXIMO (anomalia grave)

```
Ano 0 → 1: Taxa observada = 29.08%  ❌ Impossível! Máx configurado = 22%
Ano 1 → 2: Taxa observada = 27.49%
...
Ano 11 → 12: Taxa observada = 22.62%

Saldo máximo possível Ano 1 (taxa 22%): R$ 1.708.000,00
Saldo máximo observado Ano 1:          R$ 1.807.165,13
Diferença:                             R$ 99.165,13  ❌
```

**Explicação:** O "máximo" do Ano 1 combina:
- Simulação com taxa alta (~22%)
- Simulação com aporte alto (R$ 8.500/mês × 12 = R$ 102.000)

Mas essas podem ser simulações DIFERENTES! O resultado é um cenário impossível.

### Análise do MÍNIMO

```
Ano 0 → 1: Taxa = 10.97%
Ano 1 → 2: Taxa = 10.87%
...
Ano 11 → 12: Taxa = 10.32%

Taxa mínima configurada: 10.00%
Variação observada: 10.97% → 10.32% (decrescente)
```

Se fosse uma simulação real, a taxa seria CONSTANTE.

---

## 3. Fluxo de Dados (Diagrama Completo)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUXO DE DADOS ATUAL                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SIMULAÇÃO (50.000 cenários)                                                │
│  ════════════════════════════                                               │
│  all_balances: Matrix (50000 x 145 meses)                                  │
│                                                                             │
│  Cada linha = uma simulação com parâmetros FIXOS:                          │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Sim #0: taxa=10.5%, capital=1.4M, aporte=0    → [1.4M, 1.41M, ...]│    │
│  │ Sim #1: taxa=18.2%, capital=1.4M, aporte=5k   → [1.4M, 1.44M, ...]│    │
│  │ Sim #2: taxa=12.1%, capital=1.4M, aporte=2k   → [1.4M, 1.42M, ...]│    │
│  │ ...                                                                │    │
│  │ Sim #49999: taxa=15.8%, capital=1.4M, aporte=8k → [1.4M, ...]     │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  AGREGAÇÃO                                                                  │
│  ══════════                                                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ MÉTODO ATUAL (INCORRETO para trajetórias)                          │   │
│  │                                                                     │   │
│  │ balances_p5 = np.percentile(all_balances, 5, axis=0)               │   │
│  │                                                                     │   │
│  │ Resultado: Para cada coluna (mês), pega o P5 INDEPENDENTEMENTE     │   │
│  │                                                                     │   │
│  │ Mês 0:  P5 = Sim #8234 (taxa=10.2%, aporte=1k)                    │   │
│  │ Mês 12: P5 = Sim #4521 (taxa=10.8%, aporte=0)   ← DIFERENTE!      │   │
│  │ Mês 24: P5 = Sim #9012 (taxa=11.1%, aporte=500) ← DIFERENTE!      │   │
│  │                                                                     │   │
│  │ → Linha P5 é um "Frankenstein" de simulações diferentes!           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SAÍDAS AFETADAS                                                            │
│  ════════════════                                                           │
│                                                                             │
│  ❌ Gráfico Evolução: balances_p5, balances_p95, balances_min, balances_max│
│  ❌ Tabela Projeção: balance_p5, balance_p90, balance_min, balance_max     │
│  ❌ Cards: final_balance_min, final_balance_max                             │
│                                                                             │
│  SAÍDAS CORRETAS                                                            │
│  ════════════════                                                           │
│                                                                             │
│  ✅ Histograma: sampled_final_balances (saldos finais reais)               │
│  ✅ Estatísticas: percentile_stats (calculado de saldos finais)            │
│  ✅ Cenários Representativos: extraídos de simulações reais                │
│  ✅ VaR/CVaR: calculados de saldos finais                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Solução Proposta (Refinada)

### Objetivo
Garantir que TODAS as saídas representem trajetórias de simulações REAIS.

### Implementação

```python
def _aggregate_trajectories(self, all_balances: np.ndarray) -> dict:
    """
    Agrega trajetórias ordenando pelo saldo FINAL.
    
    Cada percentil representa uma simulação REAL com parâmetros consistentes.
    """
    n_sim = all_balances.shape[0]
    final_balances = all_balances[:, -1]
    
    # Ordenar índices pelo saldo final
    sorted_indices = np.argsort(final_balances)
    
    # Extrair trajetórias completas para cada percentil
    def get_trajectory(percentile: float) -> np.ndarray:
        idx = sorted_indices[int(n_sim * percentile / 100)]
        return all_balances[idx, :]
    
    # Trajetórias de simulações REAIS
    return {
        'p5': get_trajectory(5),      # Simulação no P5
        'p10': get_trajectory(10),
        'p25': get_trajectory(25),
        'p50': get_trajectory(50),    # Mediana
        'p75': get_trajectory(75),
        'p90': get_trajectory(90),
        'p95': get_trajectory(95),
        'min': all_balances[sorted_indices[0], :],      # Pior cenário real
        'max': all_balances[sorted_indices[-1], :],     # Melhor cenário real
        
        # Média continua sendo média de todas (correto matematicamente)
        'mean': np.mean(all_balances, axis=0),
        
        # Índices para extrair parâmetros
        'indices': {
            'p5': sorted_indices[int(n_sim * 0.05)],
            'p50': sorted_indices[int(n_sim * 0.50)],
            'p95': sorted_indices[int(n_sim * 0.95)],
            'min': sorted_indices[0],
            'max': sorted_indices[-1]
        }
    }
```

### Vantagens

1. **P5 representa uma simulação REAL** que sorteou parâmetros pessimistas
2. **Taxa constante ao longo do tempo** em cada trajetória
3. **Parâmetros extraíveis** (pode mostrar "P5: taxa=10.2%, aporte=R$500")
4. **Consistência** entre gráfico, tabela e estatísticas

### Nota sobre a Média

A **média** (`balances_mean`) continua sendo calculada como `np.mean(all_balances, axis=0)` porque:
- É matematicamente correta (média de todas as simulações em cada ponto)
- Não representa uma simulação específica, e sim o valor esperado
- É assim que o usuário espera interpretar

---

## 5. Validação Pós-Correção

### Teste 1: Taxa Constante
```
Trajetória P5:
  Ano 0 → 1: Taxa ≈ 10.x%
  Ano 1 → 2: Taxa ≈ 10.x%  (IGUAL)
  ...
  Ano 11 → 12: Taxa ≈ 10.x% (IGUAL)
```

### Teste 2: Máximo Possível
```
Saldo máximo Ano 1 ≤ Capital × (1 + taxa_max) + aporte_max × 12
1.708.000 + 102.000 = R$ 1.810.000 (se for da MESMA simulação)
```

### Teste 3: Consistência Gráfico-Tabela
```
Valor P5 no gráfico (mês 144) = Valor P5 na tabela (ano 12) = Valor P5 no histograma
```

---

## 6. Arquivos a Modificar

| Arquivo | Modificação |
|---------|-------------|
| `core/monte_carlo.py` | Novo método `_aggregate_trajectories()` |
| `core/monte_carlo.py` | `run()`: usar trajetórias ordenadas |
| `core/monte_carlo.py` | `MonteCarloResult`: armazenar índices |
| `ui/plotly_charts.py` | Nenhuma (usa dados do result) |
| `ui/window_modern.py` | Nenhuma (usa dados do result) |
| `ui/advanced_widgets.py` | Nenhuma (usa dados do result) |

**A correção é centralizada no core!** Todas as UIs usam os dados do `MonteCarloResult`, então corrigir a fonte corrige tudo.

---

## 7. Resumo

| Aspecto | Antes | Depois |
|---------|-------|--------|
| P5/P95/Min/Max | Percentil por mês (Frankenstein) | Trajetória de simulação real |
| Taxa no P5 | Variando (15.9% → 13.6%) | Constante (~10.x%) |
| Máximo Ano 1 | R$ 1.807.165 (impossível) | ≤ R$ 1.810.000 (possível) |
| Consistência | Gráfico ≠ Tabela ≠ Histograma | Todos iguais |
| Parâmetros | Não extraíveis | Extraíveis (taxa, capital, aporte) |

---

*Relatório gerado em: Dezembro 2024*
*Versão analisada: PyInvest v5.2*
