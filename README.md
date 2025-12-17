# 💰 PyInvest - Simulador de Investimentos

Uma aplicação desktop moderna para simulação de investimentos com juros compostos, desenvolvida em Python com interface gráfica profissional e tema claro inspirado em dashboards web financeiros.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Funcionalidades

### Simulação Completa
- ✅ Cálculo de juros compostos com aportes mensais
- ✅ Definição de meta/objetivo financeiro
- ✅ Projeção de tempo para atingir a meta
- ✅ Cálculo de rentabilidade total

### Interface Moderna
- ✅ Tema claro profissional (estilo dashboard web)
- ✅ Cards coloridos de resumo (Total Investido, Lucro, Saldo Final)
- ✅ Card de status da meta (Atingido/Não atingido)
- ✅ Caixa de análise textual da simulação

### Visualizações
- ✅ Gráfico de evolução patrimonial com marcadores anuais
- ✅ Gráfico de rosca (donut) da composição do saldo
- ✅ Tabela detalhada de projeção anual

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

### Gráficos
- **Evolução do Patrimônio**: Linha com área preenchida e marcadores nos pontos anuais
- **Composição do Saldo**: Gráfico de rosca mostrando proporção Capital vs Juros

### Tabela de Projeção
Mostra ano a ano:
- Aportes acumulados
- Juros acumulados  
- Saldo total
- Percentual da meta atingido

## 🛠️ Tecnologias

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **Python** | 3.10+ | Linguagem base |
| **PySide6** | 6.5+ | Interface gráfica (Qt) |
| **Matplotlib** | 3.7+ | Gráficos |
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
