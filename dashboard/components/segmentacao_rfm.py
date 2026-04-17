import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import json
import os
from utils.ui import mostrar_insight_card

# ── Cache dos artefatos ML (carrega 1x) ──
@st.cache_resource(show_spinner=False)
def _load_model(path):
    return joblib.load(path)

@st.cache_data(show_spinner=False)
def _load_rfm_metrics(path):
    with open(path, "r") as f:
        return json.load(f)

# ── Cache do cálculo RFM (evita recalcular a cada rerun) ──
@st.cache_data(show_spinner=False)
def _calcular_rfm(df):
    """Calcula a tabela RFM a partir do dataset de receita."""
    snapshot_date = df['order_purchase_timestamp'].max() + pd.Timedelta(days=1)

    rfm = df.groupby('customer_unique_id').agg({
        'order_purchase_timestamp': lambda x: (snapshot_date - x.max()).days,
        'order_id': 'nunique',
        'price': lambda x: (x + df.loc[x.index, 'freight_value']).sum()
    }).rename(columns={
        'order_purchase_timestamp': 'Recency',
        'order_id': 'Frequency',
        'price': 'Monetary'
    })
    return rfm

# ── Mapeamento de Clusters para Personas de Negócio ──
def _mapear_personas(rfm, metrics):
    """Atribui nomes de negócio com base no perfil dos centros dos clusters."""
    profiles = metrics.get("cluster_profiles", {})

    # Rankear clusters por Monetary (maior = melhor)
    ranking_monetary = sorted(profiles.items(), key=lambda x: x[1]["Monetary"], reverse=True)
    # Rankear clusters por Recency (menor = mais recente = melhor)
    ranking_recency = sorted(profiles.items(), key=lambda x: x[1]["Recency"])

    persona_map = {}
    nomes_usados = set()

    for cluster_id, profile in profiles.items():
        r = profile["Recency"]
        f = profile["Frequency"]
        m = profile["Monetary"]

        # Lógica baseada em conhecimento de negócio
        if f > 1.5 and m > 200:
            nome = "Campeões"
        elif r < 100 and m > 100:
            nome = "Promissores"
        elif m > 400:
            nome = "Alto Valor"
        elif r > 250 and m < 80:
            nome = "Hibernando"
        elif r > 200 and m < 200:
            nome = "Em Risco"
        else:
            nome = "Regulares"

        # Evitar nomes duplicados
        if nome in nomes_usados:
            nome = f"{nome} ({cluster_id})"
        nomes_usados.add(nome)
        persona_map[int(cluster_id)] = nome

    rfm["Persona"] = rfm["Cluster"].map(persona_map)
    return rfm, persona_map


def render_segmentacao_rfm(df_receita):
    # Cabeçalho Padronizado
    st.markdown("""
        <div class="dash-header" style="padding: 0; margin-bottom: 30px;">
            <div style="color: #4A9BD9; font-size: 28px; padding-right: 12px; display: flex; align-items: center;">
                <i class="ri-group-line"></i>
            </div>
            <div>
                <h1 class="dash-title" style="font-size: 20px !important;">Inteligência de Segmentação (RFM)</h1>
                <p class="dash-subtitle">Entenda quem é o seu cliente: Perfis mapeados por Tempo, Frequência e Volume de Compras</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Caminhos dos artefatos
    path_scaler = "ml/models/rfm_scaler.pkl"
    path_kmeans = "ml/models/rfm_kmeans.pkl"
    path_metrics = "ml/reports/rfm_metrics.json"

    # Verificação de existência
    if not all(os.path.exists(p) for p in [path_scaler, path_kmeans, path_metrics]):
        st.info("💡 Os modelos de segmentação ainda não foram treinados. Execute o script `ml/train_rfm_clustering.py` no Google Colab primeiro.")
        return

    # Carregar artefatos
    try:
        scaler = _load_model(path_scaler)
        kmeans = _load_model(path_kmeans)
        metrics = _load_rfm_metrics(path_metrics)
    except Exception as e:
        st.error(f"Erro ao carregar os modelos de segmentação: {e}")
        return

    # ── Calcular RFM e aplicar modelo ──
    rfm = _calcular_rfm(df_receita)
    rfm_log = np.log1p(rfm)
    rfm_scaled = scaler.transform(rfm_log)
    rfm["Cluster"] = kmeans.predict(rfm_scaled)

    # ── Mapear Personas ──
    rfm, persona_map = _mapear_personas(rfm, metrics)

    # ── KPIs de Resumo ──
    sil_score = metrics.get("silhouette_score", 0)
    n_clusters = metrics.get("n_clusters", 0)
    total_clientes = len(rfm)
    total_transacionado = (df_receita['price'] + df_receita['freight_value']).sum()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon"><i class="ri-money-dollar-box-line"></i></div>
                <div>
                    <p class="kpi-label">Volume Total (R$)</p>
                    <p class="kpi-value" style="font-size: 22px;">R$ {total_transacionado/1e6:.2f}M</p>
                    <p style="font-size: 11px; color: #808080; margin: 0;">Receita + Frete acumulados</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon"><i class="ri-user-3-line"></i></div>
                <div>
                    <p class="kpi-label">Total de Clientes</p>
                    <p class="kpi-value" style="font-size: 22px;">{total_clientes:,}</p>
                    <p style="font-size: 11px; color: #808080; margin: 0;">Base de consumidores únicos</p>
                </div>
            </div>
        """.replace(",", "."), unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon"><i class="ri-pie-chart-2-line"></i></div>
                <div>
                    <p class="kpi-label">Segmentos</p>
                    <p class="kpi-value" style="font-size: 22px;">{n_clusters}</p>
                    <p style="font-size: 11px; color: #808080; margin: 0;">Agrupamentos via ML</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon"><i class="ri-shield-check-line"></i></div>
                <div>
                    <p class="kpi-label">Qualidade</p>
                    <p class="kpi-value" style="font-size: 22px;">{sil_score:.2%}</p>
                    <p style="font-size: 11px; color: #808080; margin: 0;">Índice de Coesão (Silhouette)</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Sub-abas ──
    tab_visao, tab_busca = st.tabs(["Visão Geral dos Segmentos", "Consultar Cliente"])

    with tab_visao:
        # ── 1. Distribuição dos Segmentos (Barras) ──
        col_bar, col_table = st.columns(2)

        with col_bar:
            dist = rfm.groupby("Persona").size().reset_index(name="Clientes")
            dist = dist.sort_values("Clientes", ascending=True)

            # Padrão Exploratório: Destaque para o maior segmento
            cores_exploratorio = ['#808080'] * (len(dist) - 1) + ['#e67e22']

            # Formatação de rótulos padrão Olist (K + Percentual)
            total_segmentados = dist['Clientes'].sum()
            labels_dist = []
            for v in dist['Clientes']:
                pct = (v / total_segmentados * 100)
                pct_str = f"{pct:.1f}%".replace('.', ',')
                
                if v >= 1000:
                    v_str = f"{v/1000:.1f}k".replace('.', ',')
                else:
                    v_str = str(v)
                
                labels_dist.append(f"{v_str} ({pct_str})")

            fig_dist = px.bar(
                dist, x="Clientes", y="Persona",
                orientation="h",
                title="<b>Concentração por Perfil de Cliente</b><br><span style='font-size:13px; color:rgba(255,255,255,0.6);'>Quantidade de consumidores únicos em cada categoria de comportamento</span>",
                text=labels_dist
            )
            fig_dist.update_traces(
                marker_color=cores_exploratorio,
                textposition="outside",
                textfont=dict(color="white", size=11),
                marker_line_color="rgba(0,0,0,0)",
                marker_line_width=0,
                width=0.85,
                cliponaxis=False
            )
            
            # Espaçamento extra no eixo X para o rótulo não sumir (Padrão Data-Ink Ratio)
            max_clientes = dist['Clientes'].max()
            fig_dist.update_xaxes(
                range=[0, max_clientes * 1.3], # 30% de margem no eixo
                showgrid=False, showline=False, zeroline=False, showticklabels=False, title=None
            )
            fig_dist.update_layout(
                height=420,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                showlegend=False,
                margin=dict(l=0, r=100, t=110, b=40), # Reduzi margem r pois o range_x já cuida disso
                bargap=0.1
            )
            fig_dist.update_yaxes(showgrid=False, showline=False, zeroline=False, title=None, tickfont=dict(size=12))

            st.plotly_chart(fig_dist, width="stretch")
            mostrar_insight_card(
                "ri-bar-chart-box-line",
                "A Pirâmide do Crescimento: Onde Focar?",
                "Perceba que a maioria da base é composta por clientes de compra única. O 'segredo do lucro' "
                "não é apenas atrair novos nomes, mas sim fazer os 'Regulares' subirem de nível. "
                "Cada cliente que migra para o topo desta barra aumenta drasticamente a previsibilidade de caixa da operação."
            )

        with col_table:
            # ── 2. Tabela de Perfis ──
            perfil = rfm.groupby("Persona").agg({
                "Recency": "mean",
                "Frequency": "mean",
                "Monetary": "mean",
                "Cluster": "count"
            }).rename(columns={
                "Recency": "Recência (dias)",
                "Frequency": "Frequência",
                "Monetary": "Valor Médio (R$)",
                "Cluster": "Qtd. Clientes"
            }).reset_index()

            perfil["Recência (dias)"] = perfil["Recência (dias)"].round(0).astype(int)
            perfil["Frequência"] = perfil["Frequência"].round(2)
            perfil["Valor Médio (R$)"] = perfil["Valor Médio (R$)"].round(2)

            st.markdown("#### Perfil Detalhado dos Segmentos")
            
            # --- Styling do Dataframe (Nível Sênior/Executivo) ---
            perfil_ordenado = perfil.sort_values("Valor Médio (R$)", ascending=False)
            
            # Função para destacar a linha "Campeões"
            def highlight_campeoes(s):
                return ['background-color: #1f77b4; color: white; font-weight: bold' if "Campeões" in str(s.Persona) else '' for _ in s]

            st.dataframe(
                perfil_ordenado.style.apply(highlight_campeoes, axis=1).format({
                    "Valor Médio (R$)": "R$ {:,.2f}",
                    "Frequência": "{:.2f}"
                }),
                use_container_width=True,
                hide_index=True,
                height=380
            )
            mostrar_insight_card(
                "ri-fingerprint-line",
                "Anatomia do Lucro: A Força dos Segmentos Premium",
                "Note a disparidade real: um cliente de 'Alto Valor' fatura, em média, 10x mais que um cliente "
                "'Hibernando' em um único pedido. O grande diferencial está na retenção: os Campeões são os únicos "
                "que rompem a barreira da compra única. O seu desafio estratégico é encurtar a Recência: "
                "quanto mais esse número cai, mais frequente é o fluxo de caixa."
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 3. Mapa de Valor por Segmento (Treemap) ──
        # Mapeamento de Cores Idêntico ao 'distribuicao_status.py'
        cores_map_senior = {
            "Campeões": "#1f77b4",     # Azul (Sucesso)
            "Em Risco": "#e67e22",    # Laranja (Alerta)
            "Hibernando": "#808080", # Cinza (Inativo)
            "Promissores": "#4F4F4F", # Grafite
            "Alto Valor": "#bdc3c7",  # Prata (Visível)
            "Regulares": "#2F2F2F"    # Base
        }

        # Mapeamento de Ícones Profissionais (Remix Icons)
        icon_map_senior = {
            "Campeões": "ri-vip-crown-2-line",
            "Em Risco": "ri-error-warning-line",
            "Hibernando": "ri-zzz-line",
            "Promissores": "ri-star-line",
            "Alto Valor": "ri-vip-diamond-fill",
            "Regulares": "ri-user-heart-line"
        }

        # Agregando para o Treemap
        treemap_data = rfm.groupby("Persona").agg({
            "Monetary": "sum",
            "Recency": "mean",
            "Frequency": "mean",
            "Cluster": "count"
        }).reset_index().rename(columns={"Cluster": "Qtd. Clientes"})

        # Aplicar as cores discretas do projeto
        treemap_data["cor"] = treemap_data["Persona"].map(cores_map_senior).fillna("#808080")

        fig_treemap = px.treemap(
            treemap_data,
            path=[px.Constant("Portfólio de Clientes Olist"), "Persona"],
            values="Monetary",
            title="<b>Participação Financeira por Segmento</b><br><span style='font-size:13px; color:rgba(255,255,255,0.6);'>Onde está a maior parte da receita: o tamanho do bloco indica o faturamento acumulado por perfil</span>",
            custom_data=["Recency", "Frequency", "Qtd. Clientes", "Persona"]
        )

        fig_treemap.update_traces(
            marker_colors=treemap_data["cor"],
            marker_line_width=0,
            marker_line_color="rgba(0,0,0,0)",
            textinfo="label+value",
            texttemplate="<b>%{label}</b><br>R$ %{value:,.0f}",
            textfont=dict(color="white"), # Força fonte branca em todos os blocos
            tiling_pad=0, # Deixa os blocos "grudados"
            hovertemplate="<b>%{label}</b><br>Faturamento: R$ %{value:,.2f}<br>Recência Média: %{customdata[0]:.0f} dias<br>Freq. Média: %{customdata[1]:.2f}<br>Clientes: %{customdata[2]:,.0f}"
        )

        fig_treemap.update_layout(
            height=600,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            title_x=0.02, # Alinha o título com o início do card
            margin=dict(l=15, r=15, t=90, b=20) # Margens refinadas para encaixe perfeito no card #242424
        )

        st.plotly_chart(fig_treemap, width="stretch")
        mostrar_insight_card(
            "ri-map-2-line",
            "Mapa do Tesouro: Identificando o Faturamento em Risco",
            "Este mapa mostra quem sustenta a empresa. Blocos Azuis são seu Porto Seguro; "
            "blocos Laranjas (Em Risco) são seu sinal de alerta: clientes valiosos que estão parando de comprar. "
            "O objetivo estratégico é evitar que blocos grandes se tornem Cinzas (Hibernando), o que seria uma perda definitiva de patrimônio."
        )

    with tab_busca:
        # ── Busca por Cliente — Envolvido em @st.fragment para não escurecer a tela ──
        @st.fragment
        def _busca_cliente_fragment():
            st.markdown("#### Consultar Perfil de Cliente")
            
            # --- Diretório de Referência ---
            with st.expander("📖 Diretório de Clientes (Referência para Cópia)"):
                st.write("Selecione um perfil para ver exemplos de IDs reais:")
                persona_dir = st.selectbox(
                    "Filtrar por Perfil Estratégico:", 
                    options=[p for p in cores_map_senior.keys() if "Regulares" not in p],
                    index=0,
                    key="persona_filter_final"
                )
                
                # Filtrar e mostrar os top 100 mais recentes desse perfil para facilitar a cópia
                amostra = rfm[rfm["Persona"] == persona_dir].sort_values("Recency").head(100)
                st.dataframe(
                    amostra.reset_index()[["customer_unique_id", "Persona"]],
                    use_container_width=True,
                    hide_index=True,
                    height=250
                )
                st.markdown(f"<p style='font-size: 11px; color: #808080; margin-top: -10px;'><i>Exibindo os 100 clientes com compras mais recentes deste perfil para referência rápida.</i></p>", unsafe_allow_html=True)
            
            st.write("---")

            cliente_id = st.text_input(
                "ID do Cliente (customer_unique_id)",
                placeholder="Cole o ID que você copiou acima (ex: 8d50f5eadf50201ccdcedfb9e2ac8455)"
            )

            if cliente_id:
                cliente_id = cliente_id.strip()
                if cliente_id in rfm.index:
                    cliente = rfm.loc[cliente_id]
                    persona = cliente["Persona"]
                    recency = int(cliente["Recency"])
                    frequency = int(cliente["Frequency"])
                    monetary = float(cliente["Monetary"])

                    # Médias globais para comparação
                    avg_r = rfm["Recency"].mean()
                    avg_f = rfm["Frequency"].mean()
                    avg_m = rfm["Monetary"].mean()

                    st.divider()

                    # Resultado: Persona em destaque
                    icon_persona = icon_map_senior.get(persona, "ri-user-line")
                    st.markdown(f"""
                        <div class="kpi-card" style="justify-content: center; margin-bottom: 20px;">
                            <div class="kpi-icon" style="font-size: 36px; color: {cores_map_senior.get(persona, '#4A9BD9')}">
                                <i class="{icon_persona}"></i>
                            </div>
                            <div style="text-align: center;">
                                <p class="kpi-label">Segmento do Cliente</p>
                                <p class="kpi-value" style="font-size: 24px;">{persona}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    # KPIs individuais com comparação à média
                    c1, c2, c3 = st.columns(3)

                    with c1:
                        delta_r = recency - avg_r
                        icon_r = "ri-arrow-down-line" if delta_r < 0 else "ri-arrow-up-line"
                        cor_r = "#27ae60" if delta_r < 0 else "#e67e22"
                        st.markdown(f"""
                            <div class="kpi-card">
                                <div class="kpi-icon"><i class="ri-calendar-line"></i></div>
                                <div>
                                    <p class="kpi-label">Recência</p>
                                    <p class="kpi-value">{recency} dias</p>
                                    <p style="font-size: 11px; color: {cor_r}; margin: 0;">
                                        <i class="{icon_r}" style="font-size: 11px;"></i>
                                        {abs(delta_r):.0f} dias vs média ({avg_r:.0f}d)
                                    </p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                    with c2:
                        delta_f = frequency - avg_f
                        icon_f = "ri-arrow-up-line" if delta_f > 0 else "ri-arrow-down-line"
                        cor_f = "#27ae60" if delta_f > 0 else "#e67e22"
                        st.markdown(f"""
                            <div class="kpi-card">
                                <div class="kpi-icon"><i class="ri-repeat-line"></i></div>
                                <div>
                                    <p class="kpi-label">Frequência</p>
                                    <p class="kpi-value">{frequency} pedido(s)</p>
                                    <p style="font-size: 11px; color: {cor_f}; margin: 0;">
                                        <i class="{icon_f}" style="font-size: 11px;"></i>
                                        {abs(delta_f):.2f} vs média ({avg_f:.2f})
                                    </p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                    with c3:
                        delta_m = monetary - avg_m
                        icon_m = "ri-arrow-up-line" if delta_m > 0 else "ri-arrow-down-line"
                        cor_m = "#27ae60" if delta_m > 0 else "#e67e22"
                        st.markdown(f"""
                            <div class="kpi-card">
                                <div class="kpi-icon"><i class="ri-money-dollar-circle-line"></i></div>
                                <div>
                                    <p class="kpi-label">Valor Monetário</p>
                                    <p class="kpi-value">R$ {monetary:,.2f}</p>
                                    <p style="font-size: 11px; color: {cor_m}; margin: 0;">
                                        <i class="{icon_m}" style="font-size: 11px;"></i>
                                        R$ {abs(delta_m):,.2f} vs média (R$ {avg_m:,.2f})
                                    </p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                else:
                    st.warning(f"Cliente '{cliente_id}' não encontrado na base de receita. Verifique o ID e tente novamente.")

        _busca_cliente_fragment()
