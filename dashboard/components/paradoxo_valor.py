import plotly.express as px
import pandas as pd

def render_paradoxo_valor(df):
    # 1. Preparação dos Dados (Seguindo a risca a lógica do Olist.ipynb)
    # Filtro de avaliados (primeiro item do pedido comReview)
    df_avaliados = df[(df['pedido_item_seq'] == 1) & (df['tem_avaliacao'] == True)].copy()
    
    if df_avaliados.empty:
        return None

    # Primeiro descobrimos o valor TOTAL de cada pedido na base informada
    # (Agrupamos na base de entrada 'df' para garantir consistência)
    pedidos_totais = df.groupby('order_id')['price'].sum().reset_index()

    # Resgatamos a nota única do pedido
    notas = df_avaliados[['order_id', 'review_score']]

    # Cruzamos a informação para calcular a média de ticket por score
    ticket_por_score = pedidos_totais.merge(notas, on='order_id').groupby('review_score').agg(
        ticket_medio=('price', 'mean')
    ).reset_index()

    # 2. Estratégia de Cores (Destaque Laranja #e67e22 no Score 1 vs Cinza Uniforme)
    cores_paradoxo = ['#e67e22', '#808080', '#808080', '#808080', '#808080']

    # Formatação de Rótulos (Padrão Brasileiro R$ XX,XX)
    labels_custom = [f"<b>R$ {v:,.2f}</b>".replace(',', 'v').replace('.', ',').replace('v', '.') for v in ticket_por_score['ticket_medio']]

    # 3. Construção do Gráfico
    fig = px.bar(
        ticket_por_score,
        x='review_score',
        y='ticket_medio',
        title='<b>Paradoxo do Valor: Itens de Maior Ticket Médio Lideram a Insatisfação</b><br><span style="font-size:13px; color:rgba(255,255,255,0.7);">Consumidores que investem mais (R$ 165) são os que atribuem as menores notas.</span>',
        text=labels_custom
    )

    # 4. Refinamento de Traços
    fig.update_traces(
        marker_color=cores_paradoxo,
        textposition='outside',
        textfont=dict(size=13, color='rgba(255,255,255,0.9)'),
        cliponaxis=False,
        width=0.75
    )

    # Layout transparente padrão
    layout_transparente = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    # 5. Layout Executivo
    fig.update_layout(
        **layout_transparente,
        title_x=0.01,
        height=480,
        showlegend=False,
        margin=dict(t=120, b=80, l=60, r=60),
        bargap=0.25
    )

    # Eixos Clean
    fig.update_xaxes(
        tickmode='linear',
        showgrid=False,
        showline=True,
        linecolor='rgba(255,255,255,0.1)',
        title_text=None,
        tickfont=dict(size=14, color='rgba(255,255,255,0.9)'),
        zeroline=False
    )

    fig.update_yaxes(
        showgrid=False,
        showline=False,
        zeroline=False,
        showticklabels=False,
        title=None
    )

    # Nota de Rodapé Removida

    return fig
