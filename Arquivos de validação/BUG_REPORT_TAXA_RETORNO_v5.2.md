# 🔴 Relatório de Bug: Taxa de Retorno Variando Ano-a-Ano

## Resumo Executivo

**Bug Identificado:** A taxa de retorno está variando ano-a-ano nas estatísticas agregadas (P5, P50, P90, etc.), quando deveria ser **ÚNICA por simulação** durante todo o período.

**Impacto:** Os percentis calculados (P5, P50, P90) NÃO representam cenários reais de investimento. Um investidor com taxa fixa de 10% não é representado corretamente.

**Severidade:** 🔴 CRÍTICO (afeta a interpretação dos resultados)

---

## 1. Evidências do Bug

### Parâmetros da Simulação (da imagem)
```
Capital Inicial: R$ 1.400.000,00
Aporte Mensal: R$ 0 (base), máx R$ 8.500
Taxa Anual: 10.00% (mín) | 13.20% (base) | 22.00% (máx)
Período: 12 anos
Simulações: 50.000
```

### Análise das Taxas Ano-a-Ano do CSV

#### Saldo Determinístico (CORRETO ✅)
```
Ano 0 → 1: Taxa 13.20%
Ano 1 → 2: Taxa 13.20%
Ano 2 → 3: Taxa 13.20%
...
Ano 11 → 12: Taxa 13.20%

✅ Taxa CONSTANTE de 13.20% a.a. (correto!)
```

#### P5 - Cenário Pessimista (INCORRETO ❌)
```
Ano 0 → 1: Taxa 15.95%   ← Deveria ser ~10-11%
Ano 1 → 2: Taxa 15.56%
Ano 2 → 3: Taxa 15.20%
Ano 3 → 4: Taxa 14.94%
Ano 4 → 5: Taxa 14.69%
Ano 5 → 6: Taxa 14.43%
Ano 6 → 7: Taxa 14.21%
Ano 7 → 8: Taxa 14.02%
Ano 8 → 9: Taxa 13.90%
Ano 9 → 10: Taxa 13.78%
Ano 10 → 11: Taxa 13.73%
Ano 11 → 12: Taxa 13.57%

❌ Taxa DECRESCENTE de 15.95% para 13.57%!
```

#### P90 - Cenário Otimista (INCORRETO ❌)
```
Ano 0 → 1: Taxa 22.98%   ← Próximo do máximo
Ano 1 → 2: Taxa 22.08%
Ano 2 → 3: Taxa 21.41%
Ano 3 → 4: Taxa 20.86%
...
Ano 11 → 12: Taxa 19.03%

❌ Taxa DECRESCENTE de 22.98% para 19.03%!
```

---

## 2. Comportamento Esperado vs Observado

### Comportamento ESPERADO (Taxa Única por Simulação)

Se cada simulação sorteia UMA taxa que permanece fixa durante todo o período:

```
Simulação #1: Taxa sorteada = 10.5%
  Ano 0: R$ 1.400.000
  Ano 1: R$ 1.547.000 (×1.105)
  Ano 2: R$ 1.709.435 (×1.105)
  Ano 3: R$ 1.888.925 (×1.105)
  ...
  Taxa ano-a-ano: SEMPRE 10.5%

Simulação #2: Taxa sorteada = 18.3%
  Ano 0: R$ 1.400.000
  Ano 1: R$ 1.656.200 (×1.183)
  Ano 2: R$ 1.959.285 (×1.183)
  ...
  Taxa ano-a-ano: SEMPRE 18.3%
```

**Resultado esperado no P5:**
- Representa simulações que sortearam taxas baixas (~10-11%)
- Taxa ano-a-ano do P5 seria CONSTANTE (~10-11%)

### Comportamento OBSERVADO (Taxa Variando)

O P5 do Ano 1 pega o percentil 5 de TODAS as simulações naquele mês.
O P5 do Ano 2 pega o percentil 5 de TODAS as simulações naquele mês.
...e assim por diante.

**Problema:** O P5 de cada ano NÃO vem necessariamente da mesma simulação!

```
P5 do Ano 1: Pode ser da Simulação #4523
P5 do Ano 2: Pode ser da Simulação #8901
P5 do Ano 3: Pode ser da Simulação #2156
...
```

Isso cria um "cenário Frankenstein" que não representa nenhum investidor real.

---

## 3. Causa Raiz

### Código Atual (monte_carlo.py, linha 860-908)

```python
def _calculate_monte_carlo_with_events(self, monthly_events):
    n = self.inputs.n_simulations
    years = self.inputs.periodo_anos
    total_months = years * 12
    
    # Gerar parâmetros aleatórios (CORRETO)
    initials = self.inputs.capital_inicial.sample(n)
    monthlies = self.inputs.aporte_mensal.sample(n)
    rates = self.inputs.rentabilidade_anual.sample(n)  # ← Taxa ÚNICA por simulação
    
    # Converter taxa anual para mensal (CORRETO)
    monthly_rates = (1 + rates / 100) ** (1/12) - 1  # ← Shape: (n,)
    
    # Matriz de saldos
    all_balances = np.zeros((n, total_months + 1))
    all_balances[:, 0] = initials
    
    for m in range(1, total_months + 1):
        # Aplicar taxa FIXA para cada simulação (CORRETO)
        all_balances[:, m] = all_balances[:, m-1] * (1 + monthly_rates)
        all_balances[:, m] += monthlies
        ...
```

✅ **O cálculo está CORRETO!** Cada simulação usa taxa fixa.

### O Problema está nos PERCENTIS

```python
# Linhas 569-570
balances_p5 = np.percentile(all_balances, 5, axis=0)
balances_p95 = np.percentile(all_balances, 95, axis=0)
```

**O que acontece:**
- `np.percentile(all_balances, 5, axis=0)` calcula o P5 **para cada mês independentemente**
- O P5 do mês 12 NÃO é necessariamente da mesma simulação que o P5 do mês 24

---

## 4. Fluxo de Dados (Diagrama)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUXO ATUAL (COM BUG)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ENTRADA                                                                    │
│  ├── rates = sample(n=50000)  →  [10.5%, 15.2%, 11.8%, 21.3%, ...]         │
│  │                                                                          │
│  SIMULAÇÃO (CORRETO ✅)                                                     │
│  ├── all_balances: Matrix (50000 x 145)                                    │
│  │                                                                          │
│  │   Sim #0 (taxa=10.5%): [1.4M, 1.41M, 1.42M, ..., 4.8M]  ← taxa fixa    │
│  │   Sim #1 (taxa=15.2%): [1.4M, 1.42M, 1.44M, ..., 8.1M]  ← taxa fixa    │
│  │   Sim #2 (taxa=11.8%): [1.4M, 1.41M, 1.43M, ..., 5.5M]  ← taxa fixa    │
│  │   ...                                                                    │
│  │                                                                          │
│  AGREGAÇÃO (PROBLEMA ❌)                                                    │
│  ├── balances_p5 = np.percentile(all_balances, 5, axis=0)                  │
│  │                                                                          │
│  │   Para cada coluna (mês), pega o valor que está no percentil 5          │
│  │   MAS cada mês pode vir de uma simulação diferente!                     │
│  │                                                                          │
│  │   Mês 0:  P5 da coluna 0  → Sim #8234 (taxa=10.2%)                     │
│  │   Mês 12: P5 da coluna 12 → Sim #4521 (taxa=10.8%)  ← DIFERENTE!       │
│  │   Mês 24: P5 da coluna 24 → Sim #9012 (taxa=11.1%)  ← DIFERENTE!       │
│  │   ...                                                                    │
│  │                                                                          │
│  │   Resultado: "Cenário P5" é um FRANKENSTEIN de simulações diferentes!   │
│  │                                                                          │
│  SAÍDA (INCORRETA)                                                          │
│  └── yearly_projection com P5 que não representa nenhum cenário real        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Por Que as Taxas do P5 Começam Altas e Diminuem?

### Explicação Matemática

No Ano 1, para estar no P5 do saldo, você precisa ter:
- Capital baixo E/OU
- Taxa baixa E/OU
- Aporte baixo

Mas como o **capital é fixo** (R$ 1.4M base) e **aporte é 0**, a variação vem principalmente da **taxa**.

**Porém**, ao longo dos anos, a variância acumulada cresce:
- Simulações com taxas altas crescem exponencialmente
- Simulações com taxas baixas crescem menos

No Ano 1:
- Spread das simulações é pequeno
- P5 ≈ média × 0.95 (próximo da média)

No Ano 12:
- Spread das simulações é enorme
- P5 ≈ média × 0.70 (muito abaixo da média)

**Resultado:** A taxa implícita do P5 diminui ao longo do tempo porque o percentil 5 representa uma parcela cada vez mais "pessimista" da distribuição, não uma simulação específica.

---

## 6. Impacto no Usuário

### Interpretação ERRADA (atual)
> "Se eu investir com rendimento pessimista (P5), minha taxa será ~15% no primeiro ano e ~13.5% no último ano"

### Interpretação CORRETA (esperada)
> "Se eu investir com rendimento pessimista (P5), terei taxa de ~10-11% CONSTANTE durante todos os 12 anos"

---

## 7. Soluções Propostas

### Solução A: Percentis por Saldo Final (Recomendada)

Ordenar simulações pelo saldo FINAL e extrair trajetórias completas:

```python
# Ordenar pelo saldo final
final_balances = all_balances[:, -1]
sorted_indices = np.argsort(final_balances)

# P5 = trajetória completa da simulação no percentil 5
p5_idx = sorted_indices[int(n * 0.05)]
balances_p5 = all_balances[p5_idx, :]  # Trajetória completa!

# P50 = mediana
p50_idx = sorted_indices[int(n * 0.50)]
balances_p50 = all_balances[p50_idx, :]

# P95
p95_idx = sorted_indices[int(n * 0.95)]
balances_p95 = all_balances[p95_idx, :]
```

**Vantagem:** O P5 representa uma simulação REAL com taxa única.

### Solução B: Média de Simulações Próximas ao Percentil

```python
# Selecionar simulações próximas ao P5 (ex: entre P4 e P6)
p4_idx = int(n * 0.04)
p6_idx = int(n * 0.06)
p5_simulations = all_balances[sorted_indices[p4_idx:p6_idx], :]
balances_p5 = np.mean(p5_simulations, axis=0)
```

**Vantagem:** Suaviza outliers enquanto mantém coerência.

### Solução C: Fan Chart com Bandas de Confiança

Manter percentis por mês MAS deixar claro na UI que são bandas de confiança, não trajetórias reais.

---

## 8. Recomendação

**Implementar Solução A** com as seguintes modificações:

1. Ordenar simulações pelo saldo final
2. Extrair trajetórias completas para P5, P25, P50, P75, P95
3. Armazenar parâmetros (taxa, capital, aporte) de cada cenário representativo
4. Mostrar na UI: "Cenário P5: Taxa 10.8% | Capital R$ 1.38M | Aporte R$ 0"

---

## 9. Arquivos Afetados

| Arquivo | Função/Método | Modificação |
|---------|---------------|-------------|
| `core/monte_carlo.py` | `MonteCarloEngine.run()` | Calcular percentis por saldo final |
| `core/monte_carlo.py` | `_calculate_monte_carlo_with_events()` | Manter (já está correto) |
| `ui/window_modern.py` | `_update_advanced_statistics()` | Atualizar exibição |

---

## 10. Validação Pós-Correção

Após a correção, verificar:

1. **Taxa do P5 deve ser CONSTANTE:**
```
Ano 0 → 1: Taxa ~10.5%
Ano 1 → 2: Taxa ~10.5%
...
Ano 11 → 12: Taxa ~10.5%
```

2. **Taxa do P95 deve ser CONSTANTE:**
```
Ano 0 → 1: Taxa ~21%
Ano 1 → 2: Taxa ~21%
...
Ano 11 → 12: Taxa ~21%
```

3. **Cenários representativos devem ter parâmetros coerentes**

---

*Relatório gerado em: Dezembro 2024*
*Versão analisada: PyInvest v5.2*
