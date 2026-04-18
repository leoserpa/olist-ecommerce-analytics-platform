# 📊 Olist Intelligence Dashboard 2.1
**Versão/Version:** `v2.1.0` | **Status:** `Produção/Production (Finalizado)` | **Design:** `Senior Executive` | **Framework:** `Streamlit`

---

### 🌐 Idioma / Language
- [🇧🇷 Português (Brasil)](#-português-brasil)
- [🇺🇸 English (US)](#-english-us)

---

## 🇧🇷 Português (Brasil)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![DuckDB](https://img.shields.io/badge/DuckDB-Analytics-yellow)](https://duckdb.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine_Learning-orange)](https://scikit-learn.org/)

> **A plataforma definitiva de Advanced Analytics para o ecossistema Olist.** 
> Projetada para transformar dados brutos em decisões estratégicas de alto impacto, esta versão consolida engenharia de dados robusta, modelos preditivos de última geração e segmentação comportamental profunda.

### 🏛️ Arquitetura Analítica (End-to-End)

A solução está estruturada em quatro pilares fundamentais, cada um focado em uma camada de maturidade analítica:

1.  **Engenharia de Performance (Core)**: 
    *   Pipeline ETL modular utilizando **DuckDB** para processamento analítico ultra-rápido.
    *   Armazenamento em formato **Parquet** (Lakehouse local), garantindo latência quase zero no carregamento.
2.  **Dashboard Executivo (`dashboard/`)**:
    *   Interface minimalista focada no **Data-Ink Ratio**, eliminando distrações visuais.
    *   Navegação por Abas Estratégicas: *Exploratória, Diagnóstico, Preditiva e Segmentação*.
3.  **Machine Learning Hub (`ml/`)**:
    *   **Análise Preditiva**: Modelo XGBoost para previsão de satisfação e risco operacional.
    *   **Segmentação RFM**: Clusterização K-Means para mapeamento de personas (Campeões, Em Risco, etc.).
4.  **UX & Performance Analytics**:
    *   Uso intensivo de `@st.cache_data` e `@st.fragment` para uma experiência de usuário fluida e sem interrupções (Zero Rerun Lag).

### 📸 Galeria do Dashboard

| | |
| :---: | :---: |
| ![Screenshot 1](assets/img1.png) | ![Screenshot 2](assets/img2.png) |
| ![Screenshot 3](assets/img3.png) | ![Screenshot 4](assets/img4.png) |

---

### 📁 Estrutura do Ecossistema (Senior Standard)

```text
projeto_Olist_EDA/
├── assets/                  # Galeria de Screenshots e Documentação Visual
├── dashboard/               # Interface de Consumo Executivo
│   ├── main.py              # Entrypoint da Aplicação (Layout & Navegação)
│   ├── components/          # Módulos Visuais e Lógica de Abas
│   └── utils/               # Helpers de UI (Design System)
├── ml/                      # Camada de Ciência de Dados & Modelos
│   ├── models/              # Artefatos Binários (.pkl) dos Modelos Treinados
│   ├── reports/             # Métricas de Performance e Profile dos Clusters
│   └── trainer/             # Pipeline de Treinamento e Feature Engineering
├── data/                    # Lakehouse Local (Base Processada)
├── notebooks/               # Estudos de Exploração e Prototipagem
├── etl.py                   # Motor de Engenharia de Dados (DuckDB + Pandas)
├── requirements.txt         # Stack Tecnológica Completa
└── README.md                # Documentação do Projeto
```

### 🧠 Novidades da Versão 2.0 (Highlight)

#### 💎 Segmentação RFM + Modelagem Preditiva
O dashboard conta com um motor de segmentação proprietário que agrupa +95k clientes em **6 Personas Estratégicas**.
*   **Campeões**: Clientes de alta recorrência e alto ticket.
*   **Em Risco**: Clientes valiosos que não compram há muito tempo.
*   **Hibernando**: Clientes que realizaram apenas uma compra e sumiram.

#### 🛡️ Diagnóstico de Culpabilidade
Uma nova engine analítica na aba de "Diagnóstico" que separa atrasos causados pelo **Vendedor** daqueles causados pelo **Operador Logístico**.

### 🚀 Deployment Local

1.  **Configurar Ambiente**: `pip install -r requirements.txt`
2.  **Processar Lakehouse**: `python etl.py`
3.  **Habilitar Modelos (Opcional)**: Scripts em `ml/trainer/`.
4.  **Executar Dashboard**: `streamlit run dashboard/main.py`

---

## 🇺🇸 English (US)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![DuckDB](https://img.shields.io/badge/DuckDB-Analytics-yellow)](https://duckdb.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine_Learning-orange)](https://scikit-learn.org/)

> **The definitive Advanced Analytics platform for the Olist ecosystem.**
> Designed to transform raw data into high-impact strategic decisions, this version consolidates robust data engineering, state-of-the-art predictive models, and deep behavioral segmentation.

### 🏛️ Analytical Architecture (End-to-End)

The solution is structured into four fundamental pillars, each focused on a layer of analytical maturity:

1.  **Performance Engineering (Core)**: 
    *   Modular ETL pipeline using **DuckDB** for ultra-fast analytical processing.
    *   Storage in **Parquet** format (local Lakehouse), ensuring near-zero loading latency.
2.  **Executive Dashboard (`dashboard/`)**:
    *   Minimalist interface focused on **Data-Ink Ratio**.
    *   Strategic Tab Navigation: *Exploratory, Diagnostic, Predictive, and Segmentation*.
3.  **Machine Learning Hub (`ml/`)**:
    *   **Predictive Analysis**: XGBoost model for satisfaction forecasting and operational risk.
    *   **RFM Segmentation**: K-Means clustering for persona mapping (Champions, At Risk, etc.).
4.  **UX & Performance Analytics**:
    *   Intensive use of `@st.cache_data` and `@st.fragment` for a fluid and interruption-free user experience.

### 📸 Dashboard Gallery

| | |
| :---: | :---: |
| ![Screenshot 1](assets/img1.png) | ![Screenshot 2](assets/img2.png) |
| ![Screenshot 3](assets/img3.png) | ![Screenshot 4](assets/img4.png) |

---

### 📁 Ecosystem Structure (Senior Standard)

```text
projeto_Olist_EDA/
├── assets/                  # Screenshot Gallery and Visual Documentation
├── dashboard/               # Executive Consumption Interface
│   ├── main.py              # Application Entrypoint
│   ├── components/          # Visual Modules and Tab Logic
│   └── utils/               # UI Helpers (Design System)
├── ml/                      # Data Science & Models Layer
│   ├── models/              # Trained Model Binary Artifacts (.pkl)
│   ├── reports/             # Performance Metrics and Cluster Profiles
│   └── trainer/             # Training Pipeline and Feature Engineering
├── data/                    # Local Lakehouse (Processed Base)
├── notebooks/               # Exploration and Prototyping Studies
├── etl.py                   # Data Engineering Engine
├── requirements.txt         # Complete Tech Stack
└── README.md                # Project Documentation
```

### 🧠 What's New in Version 2.0 (Highlights)

#### 💎 RFM Segmentation + Predictive Modeling
The dashboard features a proprietary segmentation engine that groups +95k customers into **6 Strategic Personas**.
*   **Champions**: High frequency and high ticket customers.
*   **At Risk**: Valuable customers who haven't purchased in a long time.
*   **Hibernating**: Customers who made a single purchase and disappeared.

#### 🛡️ Culpability Diagnosis
A new analytical engine in the "Diagnostics" tab that separates delays caused by the **Seller** from those caused by the **Logistics Operator**.

### 🚀 Local Deployment

1.  **Configure Environment**: `pip install -r requirements.txt`
2.  **Process Lakehouse**: `python etl.py`
3.  **Enable Models (Optional)**: Run scripts in `ml/trainer/`.
4.  **Run Dashboard**: `streamlit run dashboard/main.py`

---

*Desenvolvido com foco na conexão entre Engenharia de Dados, Advanced Analytics e Business Intelligence Strategy.*
*Developed with a focus on the connection between Data Engineering, Advanced Analytics, and Business Intelligence Strategy.*
