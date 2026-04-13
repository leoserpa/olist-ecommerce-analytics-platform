import streamlit as st
import pandas as pd
import plotly.express as px
from components.distribuicao_status import render_distribuicao_status
from components.evolucao_vendas import render_evolucao_vendas
from components.metodos_pagamento import render_metodos_pagamento
from components.top_categorias import render_top_categorias
from components.top_ticket import render_top_ticket
from components.receita_estados import render_receita_estados
from components.frete_estados import render_frete_estados
from components.satisfacao_cliente import render_satisfacao_cliente
from components.paradoxo_valor import render_paradoxo_valor
from components.impacto_atraso import render_impacto_atraso
from components.concentracao_vendedores import render_concentracao_vendedores
from components.comportamento_compra import render_comportamento_compra
from components.recorrencia_clientes import render_recorrencia_clientes
from components.peso_frete import render_peso_frete
from components.churn_receita import render_churn_receita
from components.mapa_churn import render_mapa_churn
from components.pareto_detratoras import render_pareto_detratoras
from components.atraso_vendedor import render_atraso_vendedor
from components.diagnostico_culpabilidade import render_diagnostico_culpabilidade
from components.ai_diagnostics import render_ai_diagnostics
from utils.ui import mostrar_insight_card

# Configuração da Página
st.set_page_config(
    page_title="Olist E-Commerce Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Carregamento de Dados com Cache
@st.cache_data
def load_data():
    try:
        # Base filtrada para métricas financeiras (Olist Parte 1)
        df_receita = pd.read_parquet("data/olist_receita.parquet")
        # Base completa para métricas operacionais e logísticas (Cancelamentos, etc)
        df_completo = pd.read_parquet("data/olist_completo.parquet")
        return df_receita, df_completo
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_receita, df_completo = load_data()

# ═══════════════════════════════════════════════════════
#  CSS — DESIGN SYSTEM LIMPO (DATA-INK RATIO MÁXIMO)
# ═══════════════════════════════════════════════════════
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
<style>
    /* ═══ FUNDO ESCURO LIMPO ═══ */
    .stApp {
        background-color: #1a1a1a !important;
    }

    /* ═══ TEXTOS — BRANCO PURO, SEM FIRULA ═══ */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    .stMarkdown p, .stMarkdown span {
        color: #FFFFFF !important;
    }

    /* ═══ HEADER DASHBOARD ═══ */
    .dash-header {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 20px 0 16px 0;
    }
    .dash-logo {
        width: 38px;
        height: 38px;
        background-color: #4A9BD9;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        flex-shrink: 0;
    }
    .dash-title {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2;
    }
    .dash-subtitle {
        font-size: 13px !important;
        color: #808080 !important;
        margin: 0 !important;
        padding: 0 !important;
        font-weight: 400 !important;
    }

    /* ═══ TABS — LIMPO E DISCRETO ═══ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background: transparent;
        border-bottom: 1px solid #333333;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        background-color: transparent;
        border-radius: 0px;
        padding: 8px 20px;
        color: #808080;
        font-weight: 500;
        font-size: 14px;
        border: none;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #CCCCCC !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: transparent !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #4A9BD9 !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* ═══ KPI CARDS — FLAT, CLEAN ═══ */
    [data-testid="stMetric"] {
        background-color: #242424 !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        padding: 20px 24px !important;
    }
    [data-testid="stMetricLabel"] {
        color: #808080 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }

    /* ═══ GRÁFICOS — DENTRO DE CARDS ALINHADOS ═══ */
    [data-testid="stPlotlyChart"] {
        background-color: #242424;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 8px;
    }

    /* ═══ COLUNAS IGUAIS — GRID ALINHADO ═══ */
    /* Força as colunas lado-a-lado a terem a mesma altura */
    [data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
        gap: 12px !important;
    }
    /* Cada coluna interna expande para preencher */
    [data-testid="stColumn"] {
        display: flex !important;
        flex-direction: column !important;
    }
    /* O chart preenche o espaço vertical disponível */
    [data-testid="stColumn"] > div {
        flex: 1 !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
    }
    [data-testid="stColumn"] [data-testid="stPlotlyChart"] {
        flex: 0 0 auto !important;
    }

    /* ═══ DIVIDER — LINHA FINA ═══ */
    hr {
        border: none !important;
        height: 1px !important;
        background-color: #333333 !important;
        margin: 16px 0 !important;
    }

    /* ═══ SCROLLBAR DISCRETA ═══ */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #333333; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #555555; }

    /* ═══ INSIGHT CARDS ALINHADOS (DENTRO DE COLUNAS) ═══ */
    [data-testid="stColumn"] .insight-card {
        min-height: 110px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }

    /* ═══ MICRO-INTERAÇÕES: EFEITO HOVER ═══ */

    /* Insight Cards — levitar suavemente */
    .insight-card {
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
        cursor: default;
    }
    .insight-card:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4) !important;
    }

    /* KPI Metrics — levitar sem borda brilhante */
    [data-testid="stMetric"] {
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4) !important;
    }

    /* KPI Cards Customizados com ícone */
    .kpi-card {
        background-color: #242424;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 20px 24px;
        display: flex;
        align-items: center;
        gap: 16px;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        cursor: default;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
    }
    .kpi-icon {
        font-size: 28px;
        color: #4A9BD9;
        flex-shrink: 0;
        opacity: 0.9;
    }
    .kpi-label {
        font-size: 13px;
        color: #808080;
        font-weight: 500;
        margin: 0 0 4px 0;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0;
        line-height: 1.1;
    }

    /* Gráficos Plotly — levitar discretamente */
    [data-testid="stPlotlyChart"] {
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
    }
    [data-testid="stPlotlyChart"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35) !important;
    }



    /* ═══ INFO BOX ═══ */
    .stAlert {
        background-color: #242424 !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
    }

    /* ═══ STREAMLIT HEADER — LIMPO ═══ */
    header[data-testid="stHeader"] {
        background-color: #1a1a1a !important;
    }

    /* ═══ BLOCK PADDING ═══ */
    .block-container {
        padding-top: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  HEADER — LIMPO COMO A REFERÊNCIA
# ═══════════════════════════════════════════════════════
st.markdown("""
<div class="dash-header">
    <div class="dash-logo">📊</div>
    <div>
        <div class="dash-title">Dashboard</div>
        <div class="dash-subtitle">Análise Exploratória · Olist E-Commerce</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  ABAS PRINCIPAIS
# ═══════════════════════════════════════════════════════
aba1, aba2, aba3 = st.tabs(["Análise Exploratória", "Diagnóstico", "Análise Preditiva"])

# Aba 1: Análise Exploratória
with aba1:
    if not df_receita.empty and not df_completo.empty:
        # --- KPIs ---
        receita_total = df_receita['price'].sum()
        pedidos_unicos = df_receita['order_id'].nunique()
        ticket_medio = receita_total / pedidos_unicos
        total_abs_pedidos = df_completo['order_id'].nunique()
        pedidos_entregues = df_completo[df_completo['order_status'] == 'delivered']['order_id'].nunique()
        taxa_entrega = (pedidos_entregues / total_abs_pedidos) * 100

        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        with kpi_col1:
            st.markdown(f"""
            <div class="kpi-card">
                <i class="ri-money-dollar-circle-line kpi-icon"></i>
                <div>
                    <p class="kpi-label">Faturamento Total</p>
                    <p class="kpi-value">R$ {receita_total/1e6:.2f}M</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with kpi_col2:
            st.markdown(f"""
            <div class="kpi-card">
                <i class="ri-shopping-cart-2-line kpi-icon"></i>
                <div>
                    <p class="kpi-label">Pedidos Faturados</p>
                    <p class="kpi-value">{pedidos_unicos/1e3:.1f}k</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with kpi_col3:
            st.markdown(f"""
            <div class="kpi-card">
                <i class="ri-price-tag-2-line kpi-icon"></i>
                <div>
                    <p class="kpi-label">Ticket Médio</p>
                    <p class="kpi-value">R$ {ticket_medio:.2f}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with kpi_col4:
            st.markdown(f"""
            <div class="kpi-card">
                <i class="ri-truck-line kpi-icon"></i>
                <div>
                    <p class="kpi-label">Eficiência de Entrega</p>
                    <p class="kpi-value">{taxa_entrega:.1f}%</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # --- GRÁFICOS (SUB-ABAS) ---
        sub_aba1, sub_aba2, sub_aba3, sub_aba_comportamento, sub_aba4, sub_aba5, sub_aba6 = st.tabs(["Performance", "Mix de Produtos", "Geografia", "Comportamento", "Satisfação", "Logística", "Vendedores"])
        
        with sub_aba1:
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                fig_status = render_distribuicao_status(df_completo)
                st.plotly_chart(fig_status, use_container_width=True)
                mostrar_insight_card("ri-checkbox-circle-line", "Taxa de Sucesso Operacional", "A operação demonstra alta maturidade logística, com a imensa maioria dos pedidos (Entregues) consolidando o fluxo financeiro de forma saudável e previsível.")
            with row1_col2:
                fig_pagamentos = render_metodos_pagamento(df_receita)
                st.plotly_chart(fig_pagamentos, use_container_width=True)
                mostrar_insight_card("ri-bank-card-line", "Hegemonia do Crédito: 3 em cada 4 Pedidos são Financiados", "O Cartão de Crédito consolidou-se como o motor absoluto da operação, detendo 75,5% de market share interno. Este volume é quase 4x superior ao segundo colocado (Boleto), indicando que a conveniência do parcelamento e a aprovação instantânea são os pilares fundamentais para a conversão na plataforma.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            fig_evolucao = render_evolucao_vendas(df_receita)
            st.plotly_chart(fig_evolucao, use_container_width=True)
            mostrar_insight_card("ri-line-chart-line", "Crescimento Consistente e Sazonalidade", "Olist apresenta forte crescimento ano após ano (YoY). Note o pico marcante em Novembro de 2017, impulsionado agressivamente pelas campanhas de Black Friday.")

        with sub_aba2:
            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                fig_top_cat = render_top_categorias(df_receita)
                st.plotly_chart(fig_top_cat, use_container_width=True)
                mostrar_insight_card("ri-shopping-bag-3-line", "Composição do Faturamento por Categoria", "O Top 3 (Beleza, Relógios e Cama/Mesa) soma R$ 3,5M (~41%) do faturamento acumulado. Beleza e Saúde consolida-se como o principal driver financeiro, mantendo uma vantagem de R$ 300K em relação à terceira posição.")
            with row2_col2:
                fig_ticket = render_top_ticket(df_receita)
                st.plotly_chart(fig_ticket, use_container_width=True)
                mostrar_insight_card("ri-price-tag-3-line", "Análise de Ticket Médio: Dominância da Categoria de Computadores", "Embora o volume total seja pulverizado em itens de baixo custo, a categoria de Computadores isola-se com um ticket médio de R$ 1.098, valor 2,3x superior ao segundo colocado. Isso indica uma oportunidade de faturamento concentrado: cada pedido de hardware equivale a ~6 pedidos de móveis de jardim.")

        with sub_aba3:
            fig_geo = render_receita_estados(df_receita)
            if fig_geo:
                st.plotly_chart(fig_geo, use_container_width=True)
                mostrar_insight_card("ri-map-2-line", "Distribuição Geográfica: O Eixo Sul-Sudeste concentra ~80% da Receita", "A região Sudeste isola-se com ~65% do faturamento total, impulsionada pela dominância de São Paulo (38,3%). Somado ao Sul, o eixo Sul-Sudeste controla ~80% do mercado nacional, evidenciando uma alta densidade de consumo e infraestrutura logística nessas regiões.")

        with sub_aba_comportamento:
            st.markdown("<br>", unsafe_allow_html=True)
            row3_col1, row3_col2 = st.columns([1, 1]) # Duas colunas para não ficar muito largo
            
            with row3_col1:
                fig_comp = render_comportamento_compra(df_receita)
                if fig_comp:
                    st.plotly_chart(fig_comp, use_container_width=True)
                    mostrar_insight_card("ri-time-line", "Otimização Temporal: Janela de Conversão em Horário Comercial", "O volume de pedidos concentra-se entre Segunda e Sexta-feira das 10h às 16h. O desaquecimento acentuado aos finais de semana e madrugadas permite otimizar lances de mídia fora desses períodos.")
            
            with row3_col2:
                fig_recorrencia = render_recorrencia_clientes(df_receita)
                if fig_recorrencia:
                    st.plotly_chart(fig_recorrencia, use_container_width=True)
                    mostrar_insight_card("ri-user-heart-line", "Análise de Retenção: O Desafio da Recompra", "A taxa de retenção de ~3% evidencia um modelo de crescimento puramente transacional. Com 97% da base realizando apenas uma compra, a pressão sobre a margem para atrair novos usuários é constante. Implementar estratégias de CRM para estimular a recompra é vital para aumentar o valor de vida do cliente (LTV) e garantir a sustentabilidade do negócio.")
        
        with sub_aba4:
            row4_col1, row4_col2 = st.columns(2)
            with row4_col1:
                fig_satisfacao = render_satisfacao_cliente(df_completo)
                if fig_satisfacao:
                    st.plotly_chart(fig_satisfacao, use_container_width=True)
                    mostrar_insight_card("ri-star-line", "Polarização do Sentimento", "A grande maioria das experiências é positiva, com a nota 5 estrelas liderando o volume, seguida pela nota 4 estrelas (19,3%). Nota-se um comportamento extremista: a avaliação 1 estrela (11,5%) é individualmente mais frequente que as notas intermediárias 2 ou 3, indicando que o cliente raramente utiliza tons neutros para avaliar.")
            with row4_col2:
                fig_paradoxo = render_paradoxo_valor(df_receita)
                if fig_paradoxo:
                    st.plotly_chart(fig_paradoxo, use_container_width=True)
                    mostrar_insight_card("ri-money-dollar-circle-line", "Ticket Médio vs. Satisfação: O Custo da Expectativa", "O ticket médio das avaliações 1 estrela (R$ 165) é ~22% superior ao das avaliações 5 estrelas. Esse dado confirma que a tolerância ao erro é menor em produtos de alto valor agregado, onde falhas operacionais ou de qualidade geram as maiores frustrações no marketplace.")

        with sub_aba5:
            row5_col1, row5_col2 = st.columns(2)
            with row5_col1:
                fig_frete = render_frete_estados(df_receita)
                if fig_frete:
                    st.plotly_chart(fig_frete, use_container_width=True)
                    mostrar_insight_card("ri-truck-line", "Desigualdade Logística: Custo de Frete em RR é ~72% maior que em SP", "O peso do frete no Norte e Nordeste atua como um redutor direto de competitividade. Enquanto em São Paulo o impacto é de 18,7%, em estados como Roraima e Maranhão o custo ultrapassa os 32%. Essa disparidade de 13,5 pontos percentuais indica que a mesma venda no Norte pode ter sua margem de lucro severamente canibalizada pelo custo de última milha (Last Mile).", alerta=True)
            with row5_col2:
                fig_atraso = render_impacto_atraso(df_completo)
                if fig_atraso:
                    st.plotly_chart(fig_atraso, use_container_width=True)
                    mostrar_insight_card("ri-alert-line", "Elasticidade da Satisfação: O Impacto Exponencial do Atraso", "A tolerância ao atraso é mínima: ultrapassar o SLA em mais de 3 dias gera uma queda de ~50% na satisfação (de 4,0 para 2,04). Nota-se que mesmo atrasos curtos (1-3 dias) já derrubam a avaliação para 3,26, ficando significativamente abaixo da média geral de 4,13.", alerta=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            fig_peso = render_peso_frete(df_completo)
            if fig_peso:
                st.plotly_chart(fig_peso, use_container_width=True)
                mostrar_insight_card("ri-scales-3-line", "Física do Last Mile: O Custo Oculto de Dimensões Sub-Otimizadas", "A correlação clara e direta entre o peso e o valor tarifado de frete na regressão atua como limitador de margem para o vendedor. Incentivar lojistas a construírem um mix focado em produtos leves de alto valor agregado (como Eletrônicos) reduz drasticamente o atrito no funil de conversão causado por abandonos de carrinho em razão do frete caro.")
                    
        with sub_aba6:
            fig_vendedores = render_concentracao_vendedores(df_receita)
            if fig_vendedores:
                st.plotly_chart(fig_vendedores, use_container_width=True)
                mostrar_insight_card("ri-award-line", "Curva de Pareto: Concentração Crítica em Super Sellers", "O marketplace apresenta uma dependência severa: apenas 17,7% dos vendedores sustentam 80% do faturamento total. Enquanto o topo da pirâmide garante a estabilidade financeira, os outros 82,3% da base contribuem com apenas 20% da receita, evidenciando um ecossistema de 'cauda longa' com baixo impacto individual.")
            
    else:
        st.warning("Dados não carregados.")

# Aba 2: Diagnóstico
with aba2:
    if not df_completo.empty:
        # Espaçamento para o cabeçalho respirar
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Sub-abas de Diagnóstico
        diag_aba1, diag_aba2, diag_aba3 = st.tabs(["Perdas Financeiras", "Eficiência Operacional", "Qualidade do Produto"])
        
        with diag_aba1:
            row_diag1_col1, row_diag1_col2 = st.columns(2)
            with row_diag1_col1:
                fig_churn = render_churn_receita(df_completo)
                if fig_churn:
                    st.plotly_chart(fig_churn, use_container_width=True)
                    mostrar_insight_card("ri-bar-chart-grouped-line", "Performance de Receita: Conversão de 99,3%", "A operação retém 99,3% do faturamento potencial. O vazamento de R$ 97,2k concentra-se quase inteiramente em Cancelamentos (R$ 95,2k). O impacto por Falta de Estoque (R$ 2,0k) é residual, evidenciando boa gestão de inventário.", alerta=True)
            with row_diag1_col2:
                fig_mapa = render_mapa_churn(df_completo)
                if fig_mapa:
                    st.plotly_chart(fig_mapa, use_container_width=True)
                    mostrar_insight_card("ri-map-pin-2-line", "Disparidade Regional de Churn", "A concentração de cancelamentos em estados do Norte revela um desvio crítico em relação à média nacional. Corrigir essa disparidade regional é fundamental para estabilizar o desempenho operacional e reduzir a evasão de receita nessas localidades.", alerta=True)
        
        with diag_aba2:
            row_diag2_col1, row_diag2_col2 = st.columns(2)
            
            with row_diag2_col1:
                fig_atraso = render_atraso_vendedor(df_completo)
                if fig_atraso:
                    st.plotly_chart(fig_atraso, use_container_width=True)
                    mostrar_insight_card("ri-timer-line", "Gargalo na Postagem (SLA)", "A média de postagem de 2,4 dias aproxima a operação do limite, indicando que uma grande fatia de vendedores não possui margem de erro, transferindo o risco de atraso direto para a etapa de transporte.", alerta=True)

            with row_diag2_col2:
                fig_culpabilidade = render_diagnostico_culpabilidade(df_completo)
                if fig_culpabilidade:
                    st.plotly_chart(fig_culpabilidade, use_container_width=True)
                    mostrar_insight_card("ri-alarm-warning-line", "Foco no Operador Logístico", "Embora haja atritos e demoras na postagem pelo próprio Lojista (Vendedor), a esmagadora mancha de falhas nos SLAs reporta-se diretamente à logística ineficiente em trânsito.", alerta=True)
                
        with diag_aba3:
            fig_pareto = render_pareto_detratoras(df_completo)
            if fig_pareto:
                st.plotly_chart(fig_pareto, use_container_width=True)
                mostrar_insight_card("ri-box-3-line", "Concentração Crítica de Insatisfação", "A categoria de Cama, Mesa e Banho lidera isoladamente o ranking de avaliações negativas na plataforma. Essa predominância de detratores sinaliza um gargalo de qualidade específico no segmento e exige auditoria prioritária para preservar a reputação do catálogo.", alerta=True)

    else:
        st.warning("Dados completos não carregados.")

# Aba 3: Análise Preditiva
with aba3:
    render_ai_diagnostics()

