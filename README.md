# 💰 PyInvest - Simulador de Investimentos

---

## 🚀 Novidades v6.0 (Bootstrap Mensal → Cenários Anuais Sintéticos)

### 🎯 Problema Resolvido
- Anteriormente, o Modo Expert usava apenas **9 amostras anuais** (2017-2025)
- Espaço amostral muito pequeno para estatísticas confiáveis
- Agora: **108 retornos mensais** → **até 100.000 cenários anuais sintéticos**

### 📊 Fase 1: Core Bootstrap (`core/bootstrap.py`)

```python
from core.bootstrap import BootstrapEngine, MonthlyReturnData

# Carregar dados mensais
data = MonthlyReturnData(periods=['Jan/2017', ...], returns=np.array([...]))

# Criar engine e diagnosticar autocorrelação
engine = BootstrapEngine(data)
diagnosis = engine.get_acf_diagnosis()
print(f"ACF(1): {diagnosis['acf_lag1']:.4f}")
print(f"Sugestão: {diagnosis['recommendation']}")

# Gerar cenários
result = engine.generate_simple_bootstrap(n_scenarios=10000, seed=42)
# ou
result = engine.generate_block_bootstrap(n_scenarios=10000, block_size=3, seed=42)

print(f"Média: {result.mean:.2f}%")
print(f"P5/P95: {result.p5:.2f}% / {result.p95:.2f}%")
```

### 🖥️ Fase 2: Wizard de Interface (`ui/monthly_data_wizard.py`)

**Wizard de 4 passos:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Passo 1: Tipo de Dados                                                     │
│  ───────────────────────                                                    │
│  ○ Retornos Mensais (Recomendado) - Gera até 100.000 cenários              │
│  ○ Retornos Anuais (Tradicional) - Método Bootstrap direto                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  Passo 2: Entrada de Dados                                                  │
│  ─────────────────────────                                                  │
│  • Tabela por ano (2017-2025) com 12 meses cada                            │
│  • Importação/Exportação CSV                                                │
│  • Status em tempo real (X/108 meses preenchidos)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Passo 3: Configuração Bootstrap                                            │
│  ──────────────────────────────────                                         │
│  • Bootstrap Simples (I.I.D.) vs Block Bootstrap                           │
│  • Diagnóstico automático de ACF                                            │
│  • Tamanho de bloco automático ou manual                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Passo 4: Geração                                                           │
│  ────────────────────                                                       │
│  • Número de cenários (1.000 - 100.000)                                    │
│  • Barra de progresso em tempo real                                         │
│  • Estatísticas e histograma dos resultados                                │
│  • Exportação CSV com metadados                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 🔧 Funcionalidades Implementadas

| Funcionalidade | Fase 1 (Core) | Fase 2 (UI) |
|----------------|---------------|-------------|
| Bootstrap Histórico | ✅ | ✅ |
| Block Bootstrap | ✅ | ✅ |
| Cálculo de ACF | ✅ | ✅ |
| Tamanho Bloco Automático | ✅ | ✅ |
| Importação CSV | ✅ | ✅ |
| Exportação CSV | ✅ | ✅ |
| Template CSV | ✅ | ✅ |
| Wizard 4 Passos | - | ✅ |
| Histograma Plotly | - | ✅ |
| Progress em Thread | - | ✅ |

### 📈 Composição de Retornos

```
R_anual = (1 + r₁) × (1 + r₂) × ... × (1 + r₁₂) - 1

Exemplo: 12 meses de 1% cada
R_anual = (1.01)^12 - 1 ≈ 12.68% (não 12%!)
```

### 🧪 Testes Unitários

```bash
python tests/test_bootstrap.py

# Resultado: 24 testes ✅
```

---

## 🚀 Novidades v5.3 (Correção Agregação de Trajetórias Monte Carlo)

### 🔧 Correção Crítica: Trajetórias de Percentis

**Problema corrigido**: Os percentis (P5, P10, P90, P95) e extremos (Min, Max) eram calculados **por mês independentemente**, criando "cenários Frankenstein" que não representavam nenhuma simulação real.

**Sintoma**: No modo normal, as taxas implícitas variavam ao longo dos anos quando deveriam ser constantes.

```
ANTES (Bug):
   P5 Ano 1: 15.95%  ← Simulação #4523
   P5 Ano 2: 15.56%  ← Simulação #8901 (DIFERENTE!)
   P5 Ano 3: 15.20%  ← Simulação #2156 (DIFERENTE!)
   
DEPOIS (Correto):
   P5 Ano 1: 10.55%  ← Simulação #2671
   P5 Ano 2: 10.55%  ← Simulação #2671 (MESMA!)
   P5 Ano 3: 10.55%  ← Simulação #2671 (MESMA!)
```

### 📊 Novo Método: `_aggregate_trajectories()`

```python
# ANTES: percentil por mês (ERRADO)
balances_p5 = np.percentile(all_balances, 5, axis=0)

# DEPOIS: trajetória completa de UMA simulação (CORRETO)
sorted_indices = np.argsort(all_balances[:, -1])  # Ordena por saldo final
idx_p5 = sorted_indices[int(n_sim * 0.05)]
balances_p5 = all_balances[idx_p5, :]  # Trajetória completa!
```

### ✅ Componentes Corrigidos

| Componente | Status |
|------------|--------|
| Gráfico Evolução Patrimonial (bandas P5/P95/Min/Max) | ✅ Corrigido |
| Tabela Projeção Anual | ✅ Corrigido |
| Cards Min/Max | ✅ Corrigido |
| Histograma | ✅ Já estava correto |
| Estatísticas Percentis | ✅ Já estava correto |

### 📝 Nota sobre Modo Expert (Bootstrap)

No **Modo Expert com Bootstrap**, as taxas continuam variando ano-a-ano - **isso é comportamento correto!** O Bootstrap sorteia uma taxa do histórico **para cada ano**, simulando a volatilidade real do mercado.

| Modo | Taxa ao Longo do Tempo | Status |
|------|------------------------|--------|
| Normal (Monte Carlo) | CONSTANTE | ✅ Corrigido na v5.3 |
| Expert (Bootstrap) | VARIÁVEL | ✅ Comportamento esperado |

---

## 🚀 Novidades v5.2 (Correção Histograma Plotly)

### 🔧 Correção: Histograma não renderizava
- **Problema**: O histograma na aba "Distribuição" mostrava apenas a legenda HTML, sem o gráfico Plotly.
- **Causa**: Carregamento manual do Plotly.js via CDN não funcionava no QWebEngineView.
- **Solução**: Reescrito usando `plotly.graph_objects` com `fig.to_html(include_plotlyjs='cdn')`.

### 📊 Melhorias no Histograma
- Bins dinâmicos (Regra de Sturges)
- Linhas verticais P5/P50/P95
- Validação de metadados
- Labels de método no Modo Expert

---

## 🚀 Novidades v5.1 (Modo Expert + Estatísticas Avançadas)

### 🧪 Modo Expert
- **Bootstrap Histórico**: Sorteia retornos reais do passado
- **Distribuição Normal**: Assume retornos normalmente distribuídos
- **Distribuição t-Student**: Captura caudas pesadas (eventos extremos)

### 📊 Estatísticas Avançadas
- Upload de arquivo CSV com rendimentos históricos
- Média, desvio padrão, assimetria (skewness), curtose
- VaR e CVaR calculados corretamente

---

## 🚀 Novidades v4.8 (Correção Capital Total Investido)

### 🔧 Correção Crítica: Capital Total Investido
- **Problema corrigido**: O Capital Total Investido agora inclui **todos os aportes extraordinários** (eventos extras).
- **Fórmula correta**: `Capital Total = Capital Inicial + (Aporte Mensal × Meses) + Σ(Aportes Extras)`
- **Impacto**: Métricas de risco (Prob. Ruína, Ganho Esperado) agora refletem o custo real da estratégia.

### 📊 Probabilidade de Ruína Corrigida
- **Antes**: Comparava saldo final apenas com Capital Inicial
- **Agora**: Compara saldo final com **Capital Total Investido** (incluindo extras)
- **Fórmula**: `P(Ruína) = (# Saldos < Capital Total) ÷ N × 100%`

### 💡 Definições Atualizadas

| Métrica | Definição |
|---------|-----------|
| **Capital Total Investido** | Soma total de todo o capital desembolsado pelo investidor, compreendendo o valor inicial, os aportes mensais recorrentes e todos os eventos extraordinários de entrada de capital. |
| **Critério de Ruína** | Cenário onde o patrimônio final acumulado é inferior ao valor nominal total investido (perda de capital principal). |
| **Ganho Esperado** | Diferença entre o saldo médio esperado e o capital total investido. |

---

## 🚀 Novidades v4.7 (CDI B3 + Métricas de Risco Avançadas)

### 🏦 CDI Oficial da B3 (via API do Banco Central)
- O simulador agora obtém automaticamente a **taxa CDI** diretamente da B3 (fonte oficial), via API do Banco Central (Série 12).
- Cálculo anualizado correto, com fallback manual e cache inteligente.
- Card dedicado mostra a taxa utilizada, fonte e tooltip explicativo.

### 📊 Grid 2x4 de Métricas de Risco
- Cartões de risco expandidos: Prob. Sucesso, Prob. Ruína, VaR 95%, **CVaR 95%**, Volatilidade, Risco/Retorno, Sharpe Ratio, **CDI**.
- Tooltips matemáticos detalhados em cada card, com fórmulas e explicações.
- Layout responsivo, fontes otimizadas e integração total com o painel de resumo.

### 🍷 Novas Métricas Estatísticas
- **CVaR 95% (Expected Shortfall):** média das perdas nos 5% piores cenários.
- **Volatilidade:** desvio padrão dos saldos finais.
- **Sharpe Ratio:** retorno excedente ao CDI por unidade de risco.

---

## 📈 Métricas de Risco (Monte Carlo)

O painel de análise de risco exibe **8 cartões** com as principais métricas estatísticas:

| Card         | Descrição | Fórmula/Tooltip |
|--------------|-----------|-----------------|
| ✅ Prob. Sucesso | Chance de atingir a meta | P(Sucesso) = (# Saldos ≥ Meta) ÷ Total × 100% |
| ❌ Prob. Ruína   | Risco de perder capital **total** investido | P(Ruína) = (# Saldos < Capital Total) ÷ Total × 100% |
| ⚠️ VaR 95%       | Perda máxima esperada em 5% dos piores cenários | VaR₉₅ = Média − P₅ |
| 🍷 CVaR 95%      | Média das perdas nos 5% piores cenários | CVaR = E[X | X ≤ VaR] |
| 📊 Volatilidade  | Dispersão dos saldos finais | σ = √[ Σ(Saldo − Média)² ÷ N ] |
| ⚖️ Risco/Retorno | Quanto de risco por cada real de ganho | Razão = VaR₉₅ ÷ Ganho Esperado |
| 📈 Sharpe Ratio  | Retorno excedente ao CDI por unidade de risco | Sharpe = (CAGR − CDI) ÷ Volatilidade |
| 🏦 Taxa CDI      | Taxa livre de risco utilizada | Fonte: B3 (via API do Banco Central) |

---

## 📋 Funcionalidades

### Simulação Completa
- ✅ Cálculo de juros compostos com aportes mensais
- ✅ Definição de meta/objetivo financeiro
- ✅ Projeção de tempo para atingir a meta
- ✅ Cálculo de rentabilidade total
- ✅ **Análise de Sensibilidade** (derivadas parciais)
- ✅ **Análise Probabilística Monte Carlo** (até 50.000 cenários)
- ✅ **Modo Expert** (Bootstrap, Normal, t-Student)

### Interface Moderna
- ✅ Tema claro profissional (estilo dashboard web)
- ✅ Cards coloridos de resumo (Total Investido, Lucro, Saldo Final)
- ✅ Card de status da meta (Atingido/Não atingido)
- ✅ Caixa de análise textual com destaque visual
- ✅ **Dashboard de Sensibilidade** com 4 insights matemáticos
- ✅ **Inputs com Range** (Mín/Base/Máx) para Monte Carlo

### Visualizações Interativas
- ✅ Gráfico de evolução patrimonial com marcadores anuais
- ✅ **Túnel de Confiança** Monte Carlo (IC 90%)
- ✅ **Intervalo Total** (Min-Max)
- ✅ **Linha Média Probabilística** (tracejada)
- ✅ **Linha Determinística** (sólida com marcadores)
- ✅ Gráfico de rosca (donut) da composição do saldo
- ✅ **Histograma de Distribuição** com P5/P50/P95
- ✅ Tooltips inteligentes com posicionamento dinâmico
- ✅ Tabela detalhada de projeção anual expandida
- ✅ Exportação para CSV

### Análise Monte Carlo

| Funcionalidade | Descrição |
|----------------|-----------|
| 📊 50.000 simulações | Configurável de 100 a 50.000 |
| 📈 Distribuição Normal | μ = (Min+Max)/2, σ = (Max-Min)/6 |
| 🎯 Túnel de Confiança | Intervalo P5-P95 (IC 90%) e Min-Max |
| ⚡ Execução Paralela | QThread para não travar a UI |
| 🔄 Cenários Reproduzíveis | Parâmetros REAIS de cada percentil |
| 🧪 Modo Expert | Bootstrap, Normal, t-Student |

---

## 🗂️ Estrutura do Projeto

```
pyinvest/
├── main.py                  # Ponto de entrada
├── requirements.txt         # Dependências
├── README.md               # Documentação
│
├── core/                    # Lógica de negócio
│   ├── __init__.py
│   ├── calculation.py       # Cálculos financeiros
│   ├── monte_carlo.py       # Simulação Monte Carlo
│   └── statistics.py        # Estatísticas e métricas
│
├── ui/                      # Interface gráfica
│   ├── __init__.py
│   ├── window_modern.py     # Janela principal moderna
│   ├── widgets.py           # Componentes reutilizáveis
│   ├── advanced_widgets.py  # Widgets avançados (histograma, etc)
│   ├── plotly_charts.py     # Gráficos Plotly
│   └── styles.py            # Tema e estilos QSS
│
└── tests/                   # Testes automatizados
    ├── test_monte_carlo.py
    └── test_expert_mode.py
```

## 🚀 Instalação

### Pré-requisitos
- Python 3.10 ou superior
- pip (gerenciador de pacotes)

### Passo a Passo

1. **Clone ou baixe o projeto:**
   ```bash
   git clone <seu-repositorio>
   cd pyinvest
   ```

2. **Crie um ambiente virtual (recomendado):**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

## ▶️ Executando

```bash
python main.py
```

## 🎨 Interface

### Painel de Parâmetros

| Campo | Descrição |
|-------|-----------|
| Capital Inicial | Valor que você já possui para investir (Mín/Base/Máx) |
| Aporte Mensal | Quanto pretende investir todo mês (Mín/Base/Máx) |
| Rentabilidade Anual | Taxa de juros esperada (% a.a.) (Mín/Base/Máx) |
| Objetivo (Meta) | Valor que deseja alcançar |
| Período | Tempo do investimento em anos |

### Configuração Monte Carlo

| Campo | Descrição |
|-------|-----------|
| Número de Simulações | 100 a 50.000 (padrão: 10.000) |
| Modo Expert | Habilita métodos avançados |
| Método de Simulação | Bootstrap, Normal ou t-Student |
| Dados de Rendimento | Upload de CSV com histórico |

### Cards de Resultado

| Card | Cor | Descrição |
|------|-----|-----------|
| Total Investido | Cinza escuro | Soma de todos os aportes |
| Lucro com Juros | Verde | Rendimento dos juros compostos |
| Saldo Final | Azul | Patrimônio total acumulado |
| Status da Meta | Laranja | Se a meta foi atingida e % alcançado |

### Gráficos Interativos

- **Evolução do Patrimônio**: 
  - Área clara: Intervalo Total (Min-Max)
  - Área escura: Intervalo de Confiança 90% (P5-P95)
  - Linha tracejada: Média Monte Carlo
  - Linha sólida com marcadores: Cenário Determinístico
  
- **Composição do Saldo**: 
  - Gráfico de rosca mostrando proporção Capital vs Juros
  
- **Histograma de Distribuição**:
  - Distribuição dos saldos finais
  - Linhas verticais P5, P50 (mediana), P95

## 🛠️ Tecnologias

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **Python** | 3.10+ | Linguagem base |
| **PySide6** | 6.5+ | Interface gráfica (Qt) |
| **Plotly** | 5.18+ | Gráficos interativos |
| **NumPy** | 1.24+ | Cálculos vetoriais |
| **Pandas** | 2.0+ | Manipulação de dados |

## 📝 Fórmulas

### Juros Compostos
```
M(n) = M(n-1) × (1 + i) + PMT
```
Onde:
- `M(n)` = Montante no mês n
- `i` = Taxa mensal (convertida: `(1 + taxa_anual)^(1/12) - 1`)
- `PMT` = Aporte mensal

### Agregação de Trajetórias (v5.3)
```python
# Ordena simulações pelo saldo final
sorted_indices = np.argsort(all_balances[:, -1])

# Extrai trajetória completa de UMA simulação
idx_p5 = sorted_indices[int(n_sim * 0.05)]
balances_p5 = all_balances[idx_p5, :]
```

### VaR e CVaR
```
VaR₉₅ = Média - Percentil₅
CVaR₉₅ = E[X | X ≤ Percentil₅]
```

### Sharpe Ratio
```
Sharpe = (CAGR - CDI) / Volatilidade
```

## 📄 Licença

Este projeto está sob a licença MIT.

---

## 📌 Histórico de Versões

| Versão | Data | Principais Mudanças |
|--------|------|---------------------|
| v6.0 | Dez/2024 | Bootstrap Mensal → Cenários Sintéticos (Fase 1 Core + Fase 2 UI Wizard) |
| v5.3 | Dez/2024 | Correção agregação de trajetórias Monte Carlo |
| v5.2 | Dez/2024 | Correção histograma Plotly |
| v5.1 | Dez/2024 | Modo Expert (Bootstrap, Normal, t-Student) |
| v4.8 | Dez/2024 | Correção Capital Total Investido |
| v4.7 | Dez/2024 | CDI B3 + Métricas de Risco |
| v4.6 | Dez/2024 | Redimensionamento manual tabelas |
| v4.5 | Dez/2024 | Tabela responsiva |
| v4.4 | Dez/2024 | Colunas expandidas na projeção |
| v4.3 | Dez/2024 | Correção formatação pt-BR |
| v4.2 | Dez/2024 | Cenários reproduzíveis reais |

---

**Desenvolvido com ❤️ em Python**
