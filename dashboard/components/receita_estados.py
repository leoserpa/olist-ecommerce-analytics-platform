import pandas as pd
import plotly.express as px

def render_receita_estados(df):
    # Agrupamento Geográfico
    geo = df.groupby('customer_state').agg(
        receita=('price', 'sum'),
        pedidos=('order_id', 'nunique'),
        ticket_medio=('price', 'mean')
    ).reset_index().sort_values('receita', ascending=False)

    # Cálculos de Concentração Estratégica
    receita_nacional = geo['receita'].sum()
    geo['pct_total'] = (geo['receita'] / receita_nacional * 100).round(1)
    top3_receita = geo.head(3)['receita'].sum()
    pct_top3_nacional = (top3_receita / receita_nacional * 100).round(0)

    # Preparando dados e cores (Revertendo para o cinza #808080)
    geo_plot = geo.sort_values('receita')
    cores_geo = ['#808080'] * (len(geo_plot) - 1) + ['#1f77b4']

    # Rótulos Customizados com Formatação Brasileira (Vírgula)
    labels_geo = []
    for v, p in zip(geo_plot['receita'], geo_plot['pct_total']):
        p_str = f"{p:.1f}%".replace('.', ',')
        if v >= 1_000_000:
            valor_fmt = f"R$ {v/1_000_000:.1f}M".replace('.', ',')
        else:
            valor_fmt = f"R$ {v/1_000:.0f}K".replace('.', ',')
        labels_geo.append(f"{valor_fmt} ({p_str})")

    fig = px.bar(
        geo_plot,
        x='receita',
        y='customer_state',
        orientation='h',
        title=f'<b>São Paulo Lidera Faturamento Nacional (R$ 5,2M)</b><br><span style="font-size:13px; color:rgba(255,255,255,0.6);">Dados consolidados (Out 2016 a Ago 2018) | Top 3 Estados concentram ~{pct_top3_nacional:.0f}% da receita total</span>',
        text=labels_geo
    )

    # Estilização das Barras e Rótulos
    fig.update_traces(
        marker_color=cores_geo,
        textposition='outside',
        textfont=dict(size=11, color='rgba(255,255,255,0.8)'),
        cliponaxis=False,
        width=0.85
    )
    
    layout_transparente = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    fig.update_layout(
        **layout_transparente,
        title_x=0,
        height=750,  # Importante: altura maior mapeada no Olist.ipynb
        showlegend=False,
        margin=dict(l=10, r=160, t=100, b=60),
        bargap=0.1
    )

    # Remoção Total do Eixo X
    fig.update_xaxes(
        showgrid=False,
        showline=False,
        zeroline=False,
        showticklabels=False,
        title=None
    )

    fig.update_yaxes(
        ticks='outside',
        ticklen=5,
        tickcolor='rgba(0,0,0,0)',
        showgrid=False,
        showline=False,
        zeroline=False,
        title=None,
        automargin=True,
        tickfont=dict(size=12, color='white')
    )

    # Nota de rodapé removida

    return fig
