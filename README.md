# 💰 PyInvest - Simulador de Investimentos

Uma aplicação desktop moderna para simulação de investimentos com juros compostos e **análise probabilística Monte Carlo**, desenvolvida em Python com interface gráfica profissional e gráficos interativos Plotly.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)
![Plotly](https://img.shields.io/badge/Plotly-5.18+-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Monte Carlo](https://img.shields.io/badge/Monte_Carlo-50000_cenários-orange.svg)

## ✨ Novidades v4.6 (Redimensionamento Manual + Controle Total)

### 🖱️ Redimensionamento Manual das Colunas
- **Ambas as tabelas** ("Projeção Anual" e "Cenários Reproduzíveis") agora permitem redimensionamento manual com o mouse
- Modo `QHeaderView.Interactive` habilitado globalmente
- Largura mínima de **100px** para proteção contra compressão de valores monetários

### 🎯 Ajuste Inicial Automático
- `resizeColumnsToContents()` executado ao carregar dados
- Corrige problema de corte em títulos como "PERCENTIL"
- Larguras mínimas garantidas após o ajuste automático

### 📊 Comportamento por Quantidade de Colunas
| Colunas | Scroll Horizontal | Stretch Last | Comportamento |
|---------|-------------------|--------------|---------------|
| 5 | Desabilitado | Sim | Preenche tela |
| 10 | Habilitado | Sim | Preenche + manual |
| 12 | Obrigatório | Não | Scroll + manual |

---

## ✨ Novidades v4.5 (Tabela Responsiva + Alinhamento Centralizado)

### 📊 Lógica Híbrida de Colunas (10 vs 12)
- **10 colunas (sem eventos)**: Modo `Stretch` - tabela preenche 100% da largura disponível
- **12 colunas (com eventos)**: Modo `Interactive` + scroll horizontal
  - `resizeColumnsToContents()` para ajuste automático
  - Largura mínima de 100px para evitar compressão de valores monetários
  - Barra de scroll horizontal habilitada (`ScrollBarAsNeeded`)

### 🎯 Alinhamento Centralizado Total
- **Cabeçalhos**: `horizontalHeader().setDefaultAlignment(Qt.AlignCenter)`
- **Células**: Todos os `QTableWidgetItem` com `setTextAlignment(Qt.AlignCenter)`
- Melhor legibilidade e aparência visual consistente

### 🗑️ Limpeza de Código
- Removido método `reset_columns()` não utilizado

---

## ✨ Novidades v4.4 (Tabela de Projeção Expandida)

### 📊 Novas Colunas na Tabela de Projeção Anual
A tabela de projeção agora exibe estatísticas mais completas:

| Coluna | Descrição | Cor |
|--------|-----------|-----|
| Ano | Período da simulação | Verde (primary) |
| Total Investido | Capital + Aportes acumulados | — |
| Saldo (Det.) | Valor determinístico (sem variação) | Verde (destaque) |
| Média | Média das simulações Monte Carlo | Vermelho |
| Mediana | Valor central (P50) | Roxo |
| Moda | Valor mais frequente | Laranja |
| Mín | Pior cenário absoluto | Cinza |
| P5 | Percentil 5 (pessimista) | Vermelho escuro |
| P90 | Percentil 90 (otimista) | Verde |
| Máx | Melhor cenário absoluto | Azul |

---

## ✨ Novidades v4.3 (Correção Formatação pt-BR)

### 🔧 Correção: Duplo Clique em Cenários Reproduzíveis
- **Problema corrigido**: Ao clicar em um cenário para carregar os parâmetros, os valores agora são formatados corretamente no padrão **pt-BR**
- **Antes**: Valores eram inseridos com `.` como decimal (formato EN-US), causando leitura incorreta
- **Agora**: Valores formatados com `.` como milhar e `,` como decimal (1.400.000,00)

---

## ✨ Novidades v4.2 (Cenários Reproduzíveis Reais + IC 90%)

### 🎯 Correção Importante: Cenários Representativos
- **Problema corrigido**: A tabela "Cenários Reproduzíveis" agora mostra os parâmetros **REAIS** usados na simulação Monte Carlo
- **Antes**: Calculava taxas implícitas com capital/aporte fixos (inconsistente)
- **Agora**: Identifica as simulações reais que geraram cada percentil (P5, P25, P50, P75, P95)
- Cada cenário é **100% reproduzível** - use os parâmetros exatos para obter o mesmo resultado

### 📊 Como Funciona
1. O Monte Carlo executa N simulações (até 50.000)
2. Cada simulação usa combinação aleatória de (Capital × Aporte × Taxa)
3. Para cada percentil, encontramos a simulação **mais próxima** daquele valor
4. Extraímos os parâmetros **reais** daquela simulação específica

### 📉 Intervalo de Confiança Ajustado (IC 90%)
- **Alteração**: Túnel de confiança agora usa **P5-P95** (antes era P2.5-P97.5)
- **Por quê?** IC 90% é mais prático para planejamento financeiro
- **Na prática**: Faixa mais estreita e menos influenciada por outliers extremos
- **Visualização**: Legenda atualizada para "Intervalo de Confiança 90%"

## ✨ Novidades v3.1 (Modern UI + Plotly)

### 🎨 Interface Moderna (Flat Design)
- Cards brancos com sombras suaves e bordas arredondadas (16px)
- Tipografia Segoe UI com hierarquia clara
- Paleta de cores moderna (Emerald Green #10B981)
- Inputs com altura confortável (40px) e bordas suaves
- Botões com hover states e transições

### 📊 Gráficos Plotly Interativos
- **Hover Individual** (`hovermode='closest'`): tooltip apenas na curva apontada
- **Túnel de Confiança**: área sombreada Min-Max com `fill='tonexty'`
- **Linha Determinística**: sólida + marcadores (`mode='lines+markers'`)
- **Linha Média MC**: tracejada (`dash='dash'`)
- Renderizado em `QWebEngineView` para máxima interatividade

## 📋 Funcionalidades

### Simulação Completa
- ✅ Cálculo de juros compostos com aportes mensais
- ✅ Definição de meta/objetivo financeiro
- ✅ Projeção de tempo para atingir a meta
- ✅ Cálculo de rentabilidade total
- ✅ **Análise de Sensibilidade** (derivadas parciais)
- ✅ **Análise Probabilística Monte Carlo** (novo!)

### Interface Moderna
- ✅ Tema claro profissional (estilo dashboard web)
- ✅ Cards coloridos de resumo (Total Investido, Lucro, Saldo Final)
- ✅ Card de status da meta (Atingido/Não atingido)
- ✅ Caixa de análise textual com destaque visual
- ✅ **Dashboard de Sensibilidade** com 4 insights matemáticos
- ✅ **Inputs com Range** (Mín/Base/Máx) para Monte Carlo

### Visualizações Interativas
- ✅ Gráfico de evolução patrimonial com marcadores anuais
- ✅ **Túnel de Confiança** Monte Carlo (área sombreada)
- ✅ **Linha Média Probabilística** (tracejada)
- ✅ **Linha Determinística** (sólida com marcadores)
- ✅ Gráfico de rosca (donut) da composição do saldo
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

### Tabela de Cenários Reproduzíveis (v4.2)

A tabela mostra os parâmetros **exatos** que geraram cada percentil na simulação:

| Cenário | Percentil | Capital Inicial | Aporte Mensal | Rent. Anual | Saldo Final |
|---------|-----------|-----------------|---------------|-------------|-------------|
| P5 (Pessimista) | P5 | R$ 1.312.456 | R$ 2.345 | 15,00% | R$ 6.034.846 |
| P50 (Mediana) | P50 | R$ 1.423.789 | R$ 5.123 | 15,00% | R$ 6.969.179 |
| P95 (Otimista) | P95 | R$ 1.489.234 | R$ 7.654 | 15,00% | R$ 7.891.234 |

> **Nota**: Os valores de Capital e Aporte agora **variam** conforme o range definido!

## 🗂️ Estrutura do Projeto

```
pyinvest/
├── main.py                  # Ponto de entrada
├── requirements.txt         # Dependências
├── README.md               # Documentação
│
├── core/                    # Lógica de negócio
│   ├── __init__.py
│   ├── calculation.py       # Cálculos financeiros + sensibilidade
│   ├── monte_carlo.py       # Motor Monte Carlo vetorizado
│   └── worker.py            # QThread para execução assíncrona
│
└── ui/                      # Interface gráfica
    ├── __init__.py
    ├── window_mc.py         # Janela principal com Monte Carlo
    ├── widgets.py           # Componentes (RangeInput, Charts, etc.)
    └── styles.py            # Tema e estilos QSS
```

## 🚀 Instalação

### Pré-requisitos
- Python 3.10 ou superior
- pip (gerenciador de pacotes)

### Passo a Passo

```bash
# Clone o projeto
git clone <seu-repositorio>
cd pyinvest

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou: venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
```

## ▶️ Executando

```bash
python main.py
```

## 🎨 Interface

### Painel de Parâmetros (com Range)

| Campo | Mín | Base | Máx | Descrição |
|-------|-----|------|-----|-----------|
| Capital Inicial | 8.000 | 10.000 | 12.000 | Valor inicial |
| Aporte Mensal | 800 | 1.000 | 1.200 | Contribuição mensal |
| Rentabilidade | 8% | 10% | 12% | Taxa anual |

### Regras de Validação

1. **Determinístico fora do range**: Erro se `Det < Min` ou `Det > Max`
2. **Min > Max**: Combinação inválida
3. **Preenchimento parcial**: Min+Det sem Max (ou vice-versa)
4. **Apenas Base**: Simulação determinística (sem Monte Carlo)
5. **Min + Max**: Monte Carlo ativado automaticamente

### Gráfico de Evolução (Monte Carlo)

```
    ┌────────────────────────────────────────────┐
    │            Túnel Min-Max (azul claro)      │
    │        ┌────────────────────────────┐      │
    │        │   Túnel P10-P90 (azul)     │      │
    │        │    ╭───────────────────╮   │      │
    │        │   ╱ Média (tracejada)   ╲  │      │
    │    ●──●──●──●──●──●──●              │      │
    │    Determinística (sólida + markers)│      │
    └────────────────────────────────────────────┘
```

### Tabela Expandida (Monte Carlo)

| Ano | Total Investido | Saldo (Det.) | Saldo (Média) | Saldo (Mín) | Saldo (Máx) |
|-----|-----------------|--------------|---------------|-------------|-------------|
| 0   | R$ 10.000       | R$ 10.000    | R$ 10.000     | R$ 8.000    | R$ 12.000   |
| 5   | R$ 70.000       | R$ 93.890    | R$ 95.234     | R$ 78.456   | R$ 115.678  |
| 10  | R$ 130.000      | R$ 231.915   | R$ 245.123    | R$ 189.456  | R$ 312.789  |

## 🛠️ Tecnologias

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **Python** | 3.10+ | Linguagem base |
| **PySide6** | 6.5+ | Interface gráfica (Qt) |
| **PySide6-WebEngine** | 6.5+ | Renderização Plotly |
| **Plotly** | 5.18+ | Gráficos interativos |
| **NumPy** | 1.24+ | Monte Carlo vetorizado |
| **Matplotlib** | 3.7+ | Gráficos legados (opcional) |

## 📝 Fórmulas

### Juros Compostos
```
M(n) = M(n-1) × (1 + i) + PMT
```

### Monte Carlo - Distribuição Normal
```
μ = (Min + Max) / 2
σ = (Max - Min) / 6
X ~ N(μ, σ²) clipado em [Min, Max]
```

### Sensibilidade (Derivadas Parciais)
- **dM/dt**: Velocidade de crescimento
- **dM/da**: Potência do aporte
- **dM/dC**: Eficiência do capital
- **dM/di**: Sensibilidade à taxa

## 📄 Licença

Este projeto está sob a licença MIT.

---

**Desenvolvido com ❤️ em Python**

## 🗂️ Estrutura do Projeto

```
pyinvest/
├── main.py                  # Ponto de entrada
├── requirements.txt         # Dependências
├── README.md               # Documentação
│
├── core/                    # Lógica de negócio
│   ├── __init__.py
│   └── calculation.py       # Cálculos financeiros
│
└── ui/                      # Interface gráfica
    ├── __init__.py
    ├── window.py            # Janela principal
    ├── widgets.py           # Componentes reutilizáveis
    └── styles.py            # Tema e estilos QSS
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
| Capital Inicial | Valor que você já possui para investir |
| Aporte Mensal | Quanto pretende investir todo mês |
| Rentabilidade Anual | Taxa de juros esperada (% a.a.) |
| Objetivo (Meta) | Valor que deseja alcançar |
| Período | Tempo do investimento em anos |

### Cards de Resultado
| Card | Cor | Descrição |
|------|-----|-----------|
| Total Investido | Cinza escuro | Soma de todos os aportes |
| Lucro com Juros | Verde | Rendimento dos juros compostos |
| Saldo Final | Azul | Patrimônio total acumulado |
| Status da Meta | Laranja | Se a meta foi atingida e % alcançado |

### Gráficos Interativos
- **Evolução do Patrimônio**: 
  - Linha sólida: Saldo Total
  - Linha tracejada: Capital Investido
  - Tooltip ao passar o mouse mostrando valores
- **Composição do Saldo**: 
  - Gráfico de rosca mostrando proporção Capital vs Juros
  - Tooltip com valores ao passar o mouse

### Tabela de Projeção
Mostra ano a ano:
- Aportes acumulados
- Juros acumulados  
- Saldo total
- Percentual da meta atingido

**Botão "Exportar CSV"**: Salva os dados da tabela em formato CSV compatível com Excel.

## 🛠️ Tecnologias

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **Python** | 3.10+ | Linguagem base |
| **PySide6** | 6.5+ | Interface gráfica (Qt) |
| **Matplotlib** | 3.7+ | Gráficos interativos |
| **NumPy** | 1.24+ | Cálculos vetoriais |

## 📝 Fórmula de Juros Compostos

```
M(n) = M(n-1) × (1 + i) + PMT
```

Onde:
- `M(n)` = Montante no mês n
- `i` = Taxa mensal (convertida: `(1 + taxa_anual)^(1/12) - 1`)
- `PMT` = Aporte mensal

## 📄 Licença

Este projeto está sob a licença MIT.

---

**Desenvolvido com ❤️ em Python**
