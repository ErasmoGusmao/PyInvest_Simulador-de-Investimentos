# 💰 PyInvest - Simulador de Investimentos

Uma aplicação desktop moderna para simulação de investimentos com juros compostos e **análise probabilística Monte Carlo**, desenvolvida em Python com interface gráfica profissional e gráficos interativos Plotly.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)
![Plotly](https://img.shields.io/badge/Plotly-5.18+-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Monte Carlo](https://img.shields.io/badge/Monte_Carlo-5000_cenários-orange.svg)

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
| 📊 5.000 simulações | Configurável de 100 a 50.000 |
| 📈 Distribuição Normal | μ = (Min+Max)/2, σ = (Max-Min)/6 |
| 🎯 Túnel de Confiança | Intervalo P10-P90 e Min-Max |
| ⚡ Execução Paralela | QThread para não travar a UI |

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
