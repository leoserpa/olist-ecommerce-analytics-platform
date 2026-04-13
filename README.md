# 📊 Olist E-commerce Analytics & Diagnostics
**Versão:** `v1.2.0` | **Status:** `Produção`

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine_Learning-orange)](https://scikit-learn.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-Gradient_Boosting-green)](https://xgboost.ai/)
[![DuckDB](https://img.shields.io/badge/DuckDB-Analytics-yellow)](https://duckdb.org/)

> **Uma plataforma analítica End-to-End desenhada para C-Levels e decisões estratégicas.**
> Este projeto investiga a operação da Olist (2016-2018), saindo da análise descritiva clássica para um diagnóstico acionável focado em **Perdas Financeiras**, **Eficiência Operacional** e **Inteligência Preditiva**.

---

## 🎯 Arquitetura de Dados & Inteligência
O fluxo foge de protótipos lentos e aposta em engenharia robusta e performance de ponta:

1.  **ETL Modular (`etl.py`)**: Utiliza `DuckDB` (banco analítico in-memory) associado ao Pandas para tratar ~100k pedidos brutais de múltiplos CSVs, persistindo em `Parquet` para máxima performance.
2.  **Hub Preditivo (Machine Learning)**: Pipeline treinado com `XGBoost` para prever riscos de insatisfação em tempo real. O modelo analisa 11 variáveis críticas, com foco no impacto exponencial do atraso (SLA).
3.  **App & UX (`dashboard/`)**: Construído com Streamlit sob o padrão **Senior Executive Design**:
    *   **Data-Ink Ratio Máximo**: Gráficos Plotly limpos, sem ruído visual e com cores semânticas.
    *   **Performance Zero-Latency**: Implementação de `@st.cache_resource` para modelos e `@st.fragment` para isolamento de simulações, eliminando reruns globais e piscadas de tela.
    *   **Actionable Insights**: Cards de tradução técnica para negócio, integrados diretamente em cada visualização.

---

## 💡 Principais Descobertas (Highlights Executivos)

*   **Dominância Logística (SLA)**: O descumprimento do prazo prometido impacta a percepção do cliente **2,5x mais** do que o tempo total de transporte. O SLA é a variável mestre do NPS.
*   **Qualidade do Atendimento**: A categoria *Cama, Mesa e Banho* isola-se negativamente com o maior volume massivo de detratores, exigindo auditoria imediata de fornecedores.
*   **Risco Transacional (CRM)**: Taxa de repetição de compra de míseros ~3%. O modelo preditivo ajuda a identificar esses 97% de risco e sugere ações de *Customer Recovery* proativas.

---

## 📁 Estrutura do Repositório (Senior Standard)

```text
projeto_Olist_EDA/
├── dashboard/             # Front-end da aplicação executiva
│   ├── main.py            # Entrypoint Streamlit (Sistema de Abas)
│   └── components/        # Dashboards modulares (Visualizações & IA)
├── ml/                    # Camada de Inteligência Preditiva
│   ├── models/            # Artefatos binários do pipeline (.pkl)
│   ├── reports/           # Métricas de performance (JSON)
│   └── trainer/           # Scripts de treinamento e engenharia de features
├── data/                  # Lakehouse local (Parquet)
├── etl.py                 # Pipeline de Engenharia de Dados Core
└── requirements.txt       # Stack unificada
```

---

## 🚀 Como Executar Localmente

1. **Instalação**: `pip install -r requirements.txt`
2. **Processar Dados**: `python etl.py`
3. **Lançar App**: `streamlit run dashboard/main.py`

---

*Desenvolvido com foco na conexão entre Engenharia de Dados, Advanced Analytics e Business Intelligence Strategy.*
