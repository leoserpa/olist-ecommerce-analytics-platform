# 📊 Dashboard Analítico Olist (E-Commerce Analysis)
**Versão:** `v2.0.0` | **Status:** `Mastered`

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![DuckDB](https://img.shields.io/badge/DuckDB-Analytics-yellow)](https://duckdb.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-Machine_Learning-green)](https://xgboost.ai/)
[![Segmentation](https://img.shields.io/badge/RFM-Segmentation-orange)](https://scikit-learn.org/)

> **Uma plataforma analítica End-to-End para portfólio sênior, focada em Business Intelligence e Inteligência Preditiva.**
> Este projeto investiga a operação da Olist (2016-2018), processando mais de **113k pedidos** para entregar um diagnóstico acionável sobre faturamento, logística e comportamento do cliente.

---

## 🎯 Arquitetura de Inteligência (v2.0.0)
O projeto foi totalmente reorganizado para seguir padrões de engenharia de software e ciência de dados profissional:

1.  **Engenharia de Dados (`src/etl.py`)**: Pipeline automatizado que utiliza `DuckDB` e `Fast Parquet` para processar dados brutos em segundos, gerando relatórios de qualidade automáticos em `reports/`.
2.  **Segmentação RFM (`src/train_rfm_clustering.py`)**: Implementação de clustering **K-Means** para agrupar clientes por Recência, Frequência e Valor Monetário, mapeando personas estratégicas para CRM (Ex: Clientes "Hibernando" vs "Alto Valor").
3.  **Motor Preditivo (`src/train_satisfaction.py`)**: Modelo **XGBoost** que prevê a probabilidade de um cliente se tornar um detrator antes mesmo da entrega, analisando variáveis como atraso no SLA e peso do frete.
4.  **UX Dashboard (`dashboard/`)**: Interface Streamlit de alta fidelidade com:
    -   **Design System Dark Mode**: Visual premium com ícones Remix e cores semânticas.
    -   **Performance Otimizada**: Uso de cache agressivo e fragmentos para navegação fluida.

---

## 💡 Highlights do Projeto

*   **Visão 360°**: Da receita bruta (`R$ 13M+`) ao detalhamento regional por estado.
*   **Diagnóstico Logístico**: Identificação de que **85% dos atrasos** concentram-se na malha de transporte e não no tempo de postagem do vendedor.
*   **Inteligência de Clientes**: Mapeamento de capital em risco nos segmentos detritos do RFM, permitindo ações proativas de retenção.
*   **Preparação para Produção**: Modelos persistidos em `.pkl` e estrutura pronta para deploy em nuvem.

---

## 📁 Estrutura do Repositório (Senior Standard)

```text
projeto_Olist_EDA/
├── src/                   # Motores de Processamento (Core Logic)
│   ├── etl.py             # Pipeline de Ingestão e Limpeza
│   ├── train_rfm.py       # Treinamento de Clusterização RFM
│   └── train_satisfaction.py # Treinamento de Modelo Preditivo
├── dashboard/             # Front-end da Aplicação
│   ├── main.py            # Entrypoint do Dashboard
│   └── components/        # Módulos visuais independentes
├── ml/                    # Camada de Inteligência Persistence
│   ├── models/            # Artefatos binários (.pkl)
│   └── reports/           # Métricas de IA (JSON)
├── data/                  # Base de Dados (Parquet / Raw CSVs)
├── reports/               # Relatórios de Qualidade Gerados
├── logs/                  # Logs de execução do Sistema
└── requirements.txt       # Dependências do Ambiente
```

---

## 🚀 Como Executar

1. **Setup**: `pip install -r requirements.txt`
2. **Ingestão**: `python src/etl.py`
3. **Treinamento (Opcional)**: `python src/train_rfm_clustering.py`
4. **Dashboard**: `streamlit run dashboard/main.py`

---

*Desenvolvido como um case de estudo avançado unindo Engenharia de Dados, Advanced Analytics e UX Design.*
