# 💰 PyInvest - Simulador de Investimentos

Uma aplicação desktop moderna para simulação de investimentos com juros compostos, desenvolvida em Python com interface gráfica profissional.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)
![License](https://img.shields.io/badge/License-ERASMO-yellow.svg)

## 📋 Funcionalidades

- ✅ Cálculo de juros compostos com aportes mensais
- ✅ Interface moderna com tema escuro
- ✅ Gráfico interativo de evolução do patrimônio
- ✅ Cards de resumo (Total Investido, Juros, Valor Final)
- ✅ Comparativo visual entre valor investido e patrimônio total

## 🗂️ Estrutura do Projeto

```
pyinvest/
├── main.py              # Ponto de entrada da aplicação
├── requirements.txt     # Dependências do projeto
├── README.md           # Este arquivo
├── core/
│   ├── __init__.py
│   └── calculation.py   # Lógica de cálculos financeiros
└── ui/
    ├── __init__.py
    └── window.py        # Interface gráfica (PySide6)
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)

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

Com o ambiente virtual ativado, execute:

```bash
python main.py
```

## 🎨 Screenshots

A aplicação apresenta:
- **Painel Lateral:** Inputs para montante inicial, aporte mensal, taxa de juros e período
- **Dashboard:** Cards de resumo e gráfico de evolução do patrimônio

## 📊 Como Usar

1. **Montante Inicial:** Valor que você já possui para investir
2. **Aporte Mensal:** Quanto você pretende investir todo mês
3. **Taxa de Juros Anual:** Rentabilidade esperada (ex: 12% a.a.)
4. **Tempo:** Período do investimento em anos

Clique em **"Calcular Simulação"** para ver os resultados!

## 🛠️ Tecnologias

| Tecnologia | Uso |
|------------|-----|
| **PySide6** | Interface gráfica (Qt for Python) |
| **Matplotlib** | Gráficos integrados |
| **NumPy** | Cálculos vetoriais |

## 📝 Fórmula Utilizada

O cálculo segue a fórmula de juros compostos com aportes regulares:

```
M(n) = M(n-1) × (1 + i) + PMT
```

Onde:
- `M(n)` = Montante no mês n
- `i` = Taxa de juros mensal (convertida da anual)
- `PMT` = Aporte mensal

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

**Desenvolvido em Python**
