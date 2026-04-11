import pandas as pd
import plotly.express as px

def render_mapa_churn(df):
    """
    Diagnóstico Geográfico: Taxa de Cancelamento por Estado.
    Identifica se o frete/logística de certas regiões está 'matando' o pedido.
    """
    # 1. Preparação (Lógica de Churn)
    # A base de Diagnóstico usa todos os pedidos (completos, cancelados, etc).
    # Como st.cache_data passa o df_completo já carregado, basta contar o order_status
    df_pedidos = df[df['pedido_item_seq'] == 1].copy()
    total_estado = df_pedidos.groupby('customer_state')['order_id'].count()
    cancelados_estado = df_pedidos[df_pedidos['order_status'] == 'canceled'].groupby('customer_state')['order_id'].count()

    df_churn_geo = pd.DataFrame({
        'Total': total_estado,
        'Cancelados': cancelados_estado
    }).fillna(0)

    df_churn_geo['Taxa_Churn'] = (df_churn_geo['Cancelados'] / df_churn_geo['Total'] * 100)
    df_churn_geo = df_churn_geo.reset_index().sort_values('Taxa_Churn', ascending=True)

    # Cálculo da Média Nacional para o Benchmark
    media_nacional_churn = df_churn_geo['Taxa_Churn'].mean()

    # 2. Lógica Semântica de Cores ORIGINAL
    def colorir_senior(x):
        if x == 0: return '#1f77b4'
        if x > 1.0: return '#e67e22'
        return '#808080'

    cores_churn = [colorir_senior(x) for x in df_churn_geo['Taxa_Churn']]

    # Formatação de Rótulos PT-BR
    labels_churn = [f"{p:.1f}%".replace('.', ',') for p in df_churn_geo['Taxa_Churn']]

    # 3. Gerar o Gráfico de Barras Horizontais
    fig = px.bar(
        df_churn_geo,
        x='Taxa_Churn',
        y='customer_state',
        orientation='h',
        title="<b>Geografia dos Cancelamentos: Onde o Churn Operacional é Crítico?</b><br><span style='font-size:13px; color:rgba(255,255,255,0.6);'>Estados do Norte têm churn superior ao dobro da média nacional, chegando a quase 5x no caso de Roraima.</span>",
        text=labels_churn
    )

    # 4. Linha de Benchmark Sutil (Dotted e Low Opacity)
    fig.add_vline(
        x=media_nacional_churn,
        line_dash="dot",
        line_color="rgba(255,255,255,0.2)",
        line_width=1
    )

    # 5. Anotação na Base do Gráfico (Eixo X)
    fig.add_annotation(
        x=media_nacional_churn,
        y=-0.02, 
        xref="x",
        yref="paper",
        text=f"Média Nacional: {media_nacional_churn:.2f}%".replace('.', ','),
        showarrow=False,
        font=dict(size=10, color="rgba(255,255,255,0.4)"),
        xanchor="left",
        xshift=4
    )

    # 6. Estilização de Traços
    fig.update_traces(
        marker_color=cores_churn,
        textposition='outside',
        textfont=dict(size=11, color='white'),
        cliponaxis=False,
        width=0.85
    )

    layout_transparente = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    # 7. Layout Executivo Transparente
    fig.update_layout(
        **layout_transparente,
        title_x=0.01,
        title_y=0.98,
        height=650, # Altura ajustada para caber os 27 estados na tela
        showlegend=False,
        margin=dict(l=10, r=160, t=100, b=80),
        bargap=0.1
    )

    # Limpeza Total de Eixos
    fig.update_xaxes(
        showgrid=False, showline=False, zeroline=False, showticklabels=False, title=None
    )

    fig.update_yaxes(
        ticks='outside', ticklen=5, tickcolor='rgba(0,0,0,0)',
        showgrid=False, showline=False, zeroline=False,
        title=None, automargin=True,
        tickfont=dict(size=12, color='white')
    )

    return fig
