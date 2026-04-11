import plotly.express as px
import pandas as pd

def render_diagnostico_culpabilidade(df_completo):
    """
    Renderiza um Gráfico de Dispersão (Scatter) diagnosticando se a culpa 
    pelos atrasos é do vendedor (postagem) ou da transportadora (viagem).
    """
    # 1. Preparação dos Dados
    mask_log = (df_completo['pedido_item_seq'] == 1) & \
               (df_completo['order_status'] == 'delivered') & \
               (df_completo['dias_para_postar'].notna())

    df_culp = df_completo[mask_log].copy()
    
    # É preciso garantir que dt está acessível, convertendo se necessário
    if not pd.api.types.is_datetime64_any_dtype(df_culp['order_delivered_customer_date']):
        df_culp['order_delivered_customer_date'] = pd.to_datetime(df_culp['order_delivered_customer_date'])
    if not pd.api.types.is_datetime64_any_dtype(df_culp['order_delivered_carrier_date']):
        df_culp['order_delivered_carrier_date'] = pd.to_datetime(df_culp['order_delivered_carrier_date'])
        
    df_culp['dias_transporte'] = (df_culp['order_delivered_customer_date'] - df_culp['order_delivered_carrier_date']).dt.days
    df_culp['status_prazo'] = df_culp['atraso_entrega_dias'].apply(lambda x: 'Atrasado' if x > 0 else 'No Prazo')

    # Para performance e evitar excesso no navegador, usamos uma amostra representativa
    df_plot = df_culp.sample(min(12000, len(df_culp)), random_state=42)

    # 2. Construção do Gráfico
    fig = px.scatter(
        df_plot,
        x='dias_para_postar',
        y='dias_transporte',
        color='status_prazo',
        color_discrete_map={'Atrasado': '#e67e22', 'No Prazo': '#1f77b4'},
        opacity=0.3,
        labels={'dias_para_postar': 'Dias p/ Postagem (Vendedor)', 'dias_transporte': 'Dias de Viagem (Logística)'}
    )

    fig.update_traces(marker=dict(size=4, line=dict(width=0)))

    # 3. Destaque Visual (Retângulo Laranja)
    max_y = df_plot['dias_transporte'].max()
    fig.add_shape(
        type="rect", x0=0, y0=15, x1=3, y1=max_y,
        fillcolor="#e67e22", opacity=0.07, layer="below", line_width=0,
    )

    # 4. Linhas de SLA
    fig.add_vline(x=3, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig.add_hline(y=15, line_dash="dash", line_color="rgba(255,255,255,0.3)")

    # 5. Anotações Estratégicas
    estilo_base = dict(showarrow=False, bgcolor="rgba(17,17,17,0.8)", borderpad=5)

    # 6. Layout
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        title=dict(
            text="<b>Logística vs. Operação: Onde Moram os Atrasos?</b><br><span style='font-size:13px; color:rgba(255,255,255,0.5);'>A Jornada da Entrega: Mapeando atritos que quebram a promessa de prazo.</span>",
            x=0.01, y=0.94
        ),
        height=600,
        showlegend=False,
        margin=dict(t=120, b=60, l=70, r=50),
        annotations=[
            dict(x=0.05, y=0.90, xref="paper", yref="paper", text="<b>FALHA LOGÍSTICA</b>", font=dict(color="#e67e22", size=11), **estilo_base),
            dict(x=0.05, y=0.05, xref="paper", yref="paper", text="<b>EFICIÊNCIA</b>", font=dict(color="#1f77b4", size=11), **estilo_base),
            dict(x=0.95, y=0.05, xref="paper", yref="paper", text="<b>FALHA VENDEDOR</b>", font=dict(color="rgba(255,255,255,0.4)", size=11), **estilo_base),
        ]
    )

    # Limpeza de eixos
    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.03)', ticks="", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.03)', ticks="", zeroline=False)

    return fig
