import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import joblib
import json
import os
from utils.ui import mostrar_insight_card

# ── Cache do pipeline ML (carrega 1x, reutiliza em todo rerun) ──
@st.cache_resource(show_spinner=False)
def _load_pipeline(path):
    return joblib.load(path)

@st.cache_data(show_spinner=False)
def _load_metrics(path):
    with open(path, "r") as f:
        return json.load(f)

def render_ai_diagnostics():
    # Cabeçalho Padronizado — Estilo Translúcido (Igual aos KPIs)
    st.markdown("""
        <div class="dash-header" style="padding: 0; margin-bottom: 30px;">
            <div style="color: #4A9BD9; font-size: 28px; padding-right: 12px; display: flex; align-items: center;">
                <i class="ri-line-chart-line"></i>
            </div>
            <div>
                <h1 class="dash-title" style="font-size: 20px !important;">Hub de Análise Preditiva</h1>
                <p class="dash-subtitle">Simulações e Diagnósticos de Machine Learning</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Caminhos dos arquivos
    path_model = "ml/models/satisfaction_pipeline.pkl"
    path_metrics = "ml/reports/ml_metrics.json"

    # Verificação de existência do modelo
    if not os.path.exists(path_model) or not os.path.exists(path_metrics):
        st.info("💡 A camada de Análise Preditiva ainda está sendo configurada ou o modelo está em treinamento.")
        return

    # Carregamento com cache (evita recarregar a cada interação de widget)
    try:
        metrics = _load_metrics(path_metrics)
        pipeline = _load_pipeline(path_model)
    except Exception as e:
        st.error(f"Erro ao carregar os artefatos: {e}")
        return

    # --- Layout das Abas ---
    menu_ia = st.tabs(["Saúde do Modelo", "Simulador de Satisfação"])

    # Dicionário de Tradução
    labels_traduzidos = {
        'price': 'Preço do Produto',
        'freight_value': 'Valor do Frete',
        'tempo_entrega_dias': 'Tempo de Entrega (Total)',
        'atraso_entrega_dias': 'Atraso na Entrega (SLA)',
        'pct_frete': '% do Frete no Valor',
        'product_weight_g': 'Peso do Produto (g)',
        'hora_compra': 'Hora do Pedido',
        'customer_state': 'Estado do Cliente',
        'product_category': 'Categoria do Produto',
        'payment_type': 'Forma de Pagamento',
        'dia_semana': 'Dia da Semana'
    }

    with menu_ia[0]:
        st.markdown("#### Performance do Modelo (XGBoost)")
        
        # KPIs ESTILIZADOS IGUAL AO TOPO (ÍCONE AZUL)
        kpi1, kpi2, kpi3 = st.columns(3)
        
        with kpi1:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-icon"><i class="ri-focus-3-line"></i></div>
                    <div>
                        <p class="kpi-label">Recall (Detecção)</p>
                        <p class="kpi-value">{metrics['detrator_recall']:.1%}</p>
                        <p style="font-size: 11px; color: #808080; margin: 0;">Capacidade de achar clientes insatisfeitos</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with kpi2:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-icon"><i class="ri-checkbox-circle-line"></i></div>
                    <div>
                        <p class="kpi-label">Precisão (Acerto)</p>
                        <p class="kpi-value">{metrics['detrator_precision']:.1%}</p>
                        <p style="font-size: 11px; color: #808080; margin: 0;">Confiança quando o modelo dá o alerta</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with kpi3:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-icon"><i class="ri-scales-3-line"></i></div>
                    <div>
                        <p class="kpi-label">F1-Score (Equilíbrio)</p>
                        <p class="kpi-value">{metrics['f1_score']:.1%}</p>
                        <p style="font-size: 11px; color: #808080; margin: 0;">Média ponderada entre acerto e detecção</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.divider()

        col_graph1, col_graph2 = st.columns(2)
        
        with col_graph1:
            # Gráfico de Importância de Variáveis Traduzido — PADRÃO DATA-INK RATIO
            importances_raw = metrics.get('feature_importance', {})
            importances = pd.DataFrame({
                'Variável': [labels_traduzidos.get(k, k) for k in importances_raw.keys()],
                'Importância': list(importances_raw.values())
            }).sort_values('Importância', ascending=True)

            # Destaque para o maior ofensor (Atraso)
            importances['cor'] = ['#808080'] * (len(importances) - 1) + ['#e67e22']
            
            # Formatação de labels para o fim das barras
            text_labels = [f"{v:.1%}".replace('.', ',') for v in importances['Importância']]

            fig_imp = px.bar(
                importances, x='Importância', y='Variável',
                orientation='h', 
                title='<b>O que mais irrita o cliente? (Visão Preditiva)</b><br><span style="font-size:13px; color:rgba(255,255,255,0.7);">Importância relativa das variáveis no cálculo do risco de insatisfação (Modelo XGBoost)</span>',
                text=text_labels
            )
            
            fig_imp.update_traces(
                marker_color=importances['cor'],
                textposition='outside',
                textfont=dict(size=11, color='white'),
                cliponaxis=False,
                width=0.8
            )

            fig_imp.update_layout(
                height=450, 
                margin=dict(l=0, r=80, t=100, b=40), 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font=dict(color='white'),
                showlegend=False,
                bargap=0.1
            )

            # Remoção total do Eixo X (Data-Ink Ratio)
            fig_imp.update_xaxes(showgrid=False, showline=False, zeroline=False, showticklabels=False, title=None)
            
            # Limpeza do Eixo Y
            fig_imp.update_yaxes(
                showgrid=False, showline=False, zeroline=False, 
                title=None, automargin=True,
                tickfont=dict(size=12, color='white')
            )

            st.plotly_chart(fig_imp, use_container_width=True)
            mostrar_insight_card("ri-lightbulb-line", "O Principal Motivo da Insatisfação: O Atraso na Entrega", "Nossa análise preditiva processou milhares de pedidos e confirmou: o que mais irrita o cliente não é o preço, mas o descumprimento do prazo prometido. O impacto do atraso é 2,5x maior que qualquer outro fator. Dica: Cumprir a data combinada é o caminho mais curto para evitar avaliações negativas.")

        with col_graph2:
            # Matriz de Confusão (Heatmap) — PADRÃO DATA-INK RATIO
            cm = metrics['confusion_matrix']
            x_labels = ['Satisfeito (Prev)', 'Detrator (Prev)']
            y_labels = ['Satisfeito (Real)', 'Detrator (Real)']
            
            # Formatação de texto para as células (Padrão Sênior)
            z_text = [[f"{val:,}".replace(',', '.') for val in row] for row in cm]

            # Paleta Sênior: Laranja Ofensor (#e67e22) para erros e Azul Olist (#1f77b4) para acertos
            colorscale_custom = [[0, '#e67e22'], [1, '#1f77b4']]

            # Lógica Binária para Cores: Garante que os acertos sejam azuis independente do volume
            # 1 = Acerto (Azul), 0 = Erro (Cinza)
            z_colors = [[1, 0], [0, 1]]

            fig_cm = go.Figure(data=go.Heatmap(
                z=z_colors, 
                x=x_labels, y=y_labels,
                colorscale=colorscale_custom,
                showscale=False,
                text=z_text,
                texttemplate="%{text}",
                customdata=cm, # Guarda os valores originais para hover se necessário
                textfont=dict(color='white', size=13),
                hoverinfo="none"
            ))

            fig_cm.update_layout(
                title='<b>Matriz de Confusão: Acertos e Erros</b><br><span style="font-size:13px; color:rgba(255,255,255,0.7);">Cruzamento entre predições do modelo e classificações reais do dataset de teste</span>',
                height=450,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                margin=dict(l=20, r=20, t=100, b=40)
            )

            fig_cm.update_xaxes(side="bottom", showgrid=False, showline=False, zeroline=False, ticks="", tickfont=dict(size=12))
            fig_cm.update_yaxes(autorange="reversed", showgrid=False, showline=False, zeroline=False, ticks="", tickfont=dict(size=12))

            st.plotly_chart(fig_cm, use_container_width=True)
            mostrar_insight_card("ri-shield-check-line", "Como o Modelo Preditivo ajuda a Antecipar Problemas?", f"O sistema consegue 'adivinhar' corretamente {metrics['detrator_recall']:.1%} dos clientes que teriam uma experiência ruim antes mesmo de eles reclamarem. Isso nos permite agir de forma preventiva para tentar reverter a situação e não deixar nenhuma insatisfação passar despercebida.")

    with menu_ia[1]:
        # O @st.fragment isola este bloco: mudanças nos widgets
        # re-executam APENAS o simulador, sem escurecer a página toda.
        @st.fragment
        def _simulador_fragment():
            st.markdown("#### Simulador de Risco Preventivo")
            st.write("Ajuste os parâmetros do pedido abaixo para que o modelo calcule a probabilidade de o cliente ficar insatisfeito.")
            
            c1, c2 = st.columns(2)
            with c1:
                price = st.number_input("Preço do Produto (R$)", min_value=1.0, value=150.0, step=10.0)
                freight = st.number_input("Valor do Frete (R$)", min_value=0.0, value=25.0, step=5.0)
                weight = st.number_input("Peso do Produto (em gramas)", min_value=0, value=1000, step=100)
                hora = st.slider("Horário da Compra (H)", 0, 23, 14)
            
            with c2:
                delay = st.slider("Status do Atraso (Dias em relação ao SLA)", -10, 30, 0)
                tempo_entrega = st.slider("Tempo Total de Transporte (Dias)", 1, 60, 15)
                
                # Mapas de Tradução para Categorias e Pagamentos
                cat_map = {
                    "Cama, Mesa e Banho": "bed_bath_table",
                    "Beleza e Saúde": "health_beauty",
                    "Esporte e Lazer": "sports_leisure",
                    "Móveis e Decoração": "furniture_decor",
                    "Informática e Acessórios": "computers_accessories",
                    "Utilidades Domésticas": "housewares",
                    "Automotivo": "auto"
                }
                
                pay_map = {
                    "Cartão de Crédito": "credit_card",
                    "Boleto": "boleto",
                    "Vale": "voucher",
                    "Cartão de Débito": "debit_card"
                }

                categoria_pt = st.selectbox("Categoria do Produto", list(cat_map.keys()))
                estado = st.selectbox("Estado de Destino", 
                    ["SP", "RJ", "MG", "RS", "BA", "PR", "SC", "PE", "CE", "AM"])
                pagamento_pt = st.selectbox("Forma de Pagamento", list(pay_map.keys()))

            # Cálculo de features derivadas (Exatas como o modelo espera)
            pct_frete = (freight / price) * 100 if price > 0 else 0
            dia_semana = "Monday" # Valor base para simulação
            
            st.markdown("<br>", unsafe_allow_html=True)
            # Botão de Predição
            if st.button("🔮 Calcular Probabilidade de Detrator", use_container_width=True):
                # Converter de volta para os nomes originais que o modelo conhece
                categoria_orig = cat_map[categoria_pt]
                pagamento_orig = pay_map[pagamento_pt]

                # Criar DF de entrada para o pipeline
                input_data = pd.DataFrame([{
                    'price': price,
                    'freight_value': freight,
                    'tempo_entrega_dias': tempo_entrega,
                    'atraso_entrega_dias': delay,
                    'pct_frete': pct_frete,
                    'product_weight_g': weight,
                    'hora_compra': hora,
                    'customer_state': estado,
                    'product_category': categoria_orig,
                    'payment_type': pagamento_orig,
                    'dia_semana': dia_semana
                }])
                
                # Fazer predição
                prob = pipeline.predict_proba(input_data)[0][1]
                
                st.divider()
                
                if prob > 0.7:
                    st.error(f"⚠️ **RISCO CRÍTICO**: Este pedido tem **{prob:.1%}** de chance de gerar um detrator!")
                    mostrar_insight_card("ri-error-warning-line", "Ação Recomendada: Salvar a Experiência do Cliente", "Este pedido tem características de alto risco. Para evitar uma nota baixa, envie um cupom de desconto ou uma mensagem proativa pedindo desculpas pelo transtorno agora mesmo.", alerta=True)
                elif prob > 0.4:
                    st.warning(f"🟡 **RISCO MÉDIO**: Probabilidade de **{prob:.1%}** de insatisfação.")
                    mostrar_insight_card("ri-information-line", "Fique de Olho", "O risco é moderado. Acompanhe se o produto sairá para entrega no prazo para evitar que a situação piore.")
                else:
                    st.success(f"✅ **BAIXO RISCO**: O cliente tem apenas **{prob:.1%}** de chance de ficar insatisfeito.")

        _simulador_fragment()




