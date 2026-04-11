# 📊 Olist E-commerce Analytics & Diagnostics
**Versão:** `v1.0.0` | **Status:** `Produção`

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![DuckDB](https://img.shields.io/badge/DuckDB-Analytics-yellow)](https://duckdb.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive_Charts-blueviolet)](https://plotly.com/)

> **Uma plataforma analítica End-to-End desenhada para C-Levels e decisões estratégicas.**
> Este projeto investiga a operação da Olist (2016-2018), saindo da análise descritiva clássica para um diagnóstico acionável focado em **Perdas Financeiras**, **Eficiência Operacional** e **Qualidade Logística**.

---

## 🎯 Arquitetura de Dados (Modern Data Stack)
O fluxo foge de protótipos lentos e aposta em engenharia robusta:
1. **ETL Modular (`etl.py`)**: Utiliza `DuckDB` (banco analítico in-memory) associado ao Pandas para tratar ~100k pedidos brutais de múltiplos CSVs.
2. **Storage (`data/`)**: Os dados processados são convertidos para `Parquet` puro. Isso reduz o peso do dataset em ~70% e acelera a leitura em memória.
3. **App (`dashboard/main.py`)**: Construído com Streamlit. O *State Management* e o cache nativo (`@st.cache_data`) alimentam gráficos Plotly interativos que seguem os princípios de *Data Storytelling* de Edward Tufte (Dark Mode, Data-Ink ratio máximo, cores semânticas).

---

## 💡 Principais Descobertas (Highlights Executivos)

*   **O Paradoxo do Custo de Frete**: Identificamos que fretes caros reduzem matematicamente as avaliações 5-estrelas em até 14%. O cliente pune o produto pela falha ou lentidão do serviço logístico.
*   **Vazamento Geográfico (Churn)**: Estados da Região Norte possuem taxa de abandono logístico até 2x maior que a média nacional (SP). Isso indica a necessidade de hubs avançados de distribuição.
*   **Qualidade do Atendimento**: A categoria *Cama, Mesa e Banho* isola-se negativamente. Ela atrai o maior volume massivo de detratores (1 a 2 estrelas), exigindo uma auditoria de qualidade nos fornecedores.
*   **Risco Transacional (CRM)**: Taxa de repetição de compra de míseros ~3%. A plataforma queima capital na base (CAC) e sofre enorme pressão para sustentar a margem, escancarando a ausência de um motor de relacionamento estruturado (LTV frágil).

---

## 📁 Estrutura do Repositório (Senior Standard)

```text
projeto_Olist_EDA/
├── dashboard/             # Front-end da aplicação executiva
│   ├── main.py            # Entrypoint Streamlit (Abas e Tabs)
│   └── components/        # Scripts modulares de Plotly separados por unidade
├── data/                  # Lakehouse local
│   └── raw/               # (Necessário colocar os CSVs originais aqui)
├── docs/                  # Documentações secundárias e checklists
├── notebooks/             # Ambiente exploratório raw (Onde nasceram as hipóteses)
│   └── olist.ipynb
├── logs/                  # Trilha de auditoria gerada pelo motor de ETL
├── etl.py                 # Pipeline de Engenharia de Dados Core
└── requirements.txt       # Stack unificada
```

---

## 🚀 Como Executar Localmente

**1. Instalação de Dependências**
```bash
pip install -r requirements.txt
```

**2. Processar Dados (Pipeline)**
*Certifique-se de que os dados originais brutos da Olist estão em `data/raw/`.*
```bash
python etl.py
```

**3. Lançar Dashboard Executivo**
```bash
streamlit run dashboard/main.py
```

---

*Desenvolvido com foco na conexão entre Engenharia de Dados, Advanced Analytics e Business Intelligence.*
