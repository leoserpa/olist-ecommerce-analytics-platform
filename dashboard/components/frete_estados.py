import pandas as pd
import plotly.express as px

def render_frete_estados(df):
    # 1. Preparação dos Dados
    frete_geog = df.groupby('customer_state')['pct_frete'].mean().sort_values(ascending=False).reset_index()

    # 2. Design de Cores (Laranja de Alerta #e67e22 para os 5 estados críticos, Cinza para os demais)
    frete_geog_plot = frete_geog.sort_values('pct_frete')
    cores_frete = ['#808080'] * (len(frete_geog_plot) - 5) + ['#e67e22'] * 5

    # Rótulos Customizados com Formatação Brasileira (Vírgula)
    labels_frete = [f"{p:.1f}%".replace('.', ',') for p in frete_geog_plot['pct_frete']]

    fig = px.bar(
        frete_geog_plot,
        x='pct_frete',
        y='customer_state',
        orientation='h',
        title=f'<b>Peso do Frete por Estado: O Desafio Logístico</b><br><span style="font-size:13px; color:rgba(255,255,255,0.6);">Regiões Norte e Nordeste pagam mais frete, reduzindo a margem de lucro.</span>',
        text=labels_frete
    )

    # Estilização das Barras e Rótulos
    fig.update_traces(
        marker_color=cores_frete,
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
        height=550,
        showlegend=False,
        margin=dict(l=10, r=160, t=100, b=80),
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

    # Rodapé removido

    return fig
