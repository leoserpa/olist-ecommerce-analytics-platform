import numpy as np
import plotly.graph_objects as go
import pandas as pd

def render_evolucao_vendas(df):
    # 0. Preparação de Dados Agregados (Como no Olist.ipynb)
    receita_mensal = df.groupby('ano_mes').agg(
        receita=('price', 'sum'),
        pedidos=('order_id', 'nunique'),
        ticket_medio=('price', 'mean')
    ).reset_index()
    
    # 1. Base com Tradução para PT-BR
    meses_pt = {
        '2016-10': 'Out 16', '2017-01': 'Jan 17', '2017-02': 'Fev 17', '2017-03': 'Mar 17',
        '2017-04': 'Abr 17', '2017-05': 'Mai 17', '2017-06': 'Jun 17', '2017-07': 'Jul 17',
        '2017-08': 'Ago 17', '2017-09': 'Set 17', '2017-10': 'Out 17', '2017-11': 'Nov 17',
        '2017-12': 'Dez 17', '2018-01': 'Jan 18', '2018-02': 'Fev 18', '2018-03': 'Mar 18',
        '2018-04': 'Abr 18', '2018-05': 'Mai 18', '2018-06': 'Jun 18', '2018-07': 'Jul 18', '2018-08': 'Ago 18'
    }
    eixo_x_pt = [meses_pt.get(m, m) for m in receita_mensal['ano_mes']]

    # 2. Cálculos Estatísticos (Bandas de Bollinger)
    window = 3
    rolling_mean = receita_mensal['receita'].rolling(window=window).mean()
    rolling_std = receita_mensal['receita'].rolling(window=window).std()
    upper_band = rolling_mean + (rolling_std * 2)
    lower_band = rolling_mean - (rolling_std * 2)

    fig = go.Figure()

    # Camada 1: Banda de Volatilidade (Sutil no gráfico)
    fig.add_trace(go.Scatter(
        x=eixo_x_pt, y=upper_band,
        line=dict(color='rgba(255,255,255,0)'),
        showlegend=False, hoverinfo='none'
    ))
    fig.add_trace(go.Scatter(
        x=eixo_x_pt, y=lower_band,
        fill='tonexty',
        fillcolor='rgba(128, 128, 128, 0.12)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Volatilidade',
        hoverinfo='none',
        marker=dict(color='rgba(128, 128, 128, 0.4)')
    ))

    # Camada 2: Média Móvel
    fig.add_trace(go.Scatter(x=eixo_x_pt, y=rolling_mean, name='Média Móvel (3m)', line=dict(color='rgba(200, 200, 200, 0.35)', width=1.5, dash='dot')))

    # Camada 3: Receita Real com Rótulo Final de Precisão
    ultimo_valor = receita_mensal['receita'].iloc[-1]
    ultimo_mes = eixo_x_pt[-1]
    valor_formatado = f"R$ {ultimo_valor/1000:,.1f}k".replace('.', 'v').replace(',', '.').replace('v', ',')

    fig.add_trace(go.Scatter(
        x=eixo_x_pt, y=receita_mensal['receita'],
        mode='lines+markers', name='Receita Real',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8, symbol='circle', line=dict(color='white', width=1))
    ))

    # Rótulo de dado no último ponto (Afastamento de 5px e Alinhamento Central)
    fig.add_annotation(
        x=ultimo_mes, y=ultimo_valor,
        text=f"<b>{valor_formatado}</b>",
        showarrow=False,
        xanchor='left', xshift=5, yshift=0,
        font=dict(color='white', size=12)
    )

    # 3. Anotação Black Friday (Fina e Elegante)
    # Proteção caso "Nov 17" não exista na base iterada
    matches = receita_mensal.loc[receita_mensal['ano_mes'] == '2017-11', 'receita']
    if not matches.empty:
        bf_val = matches.values[0]
        fig.add_annotation(
            x='Nov 17',
            y=bf_val,
            text='<b>Pico Black Friday</b><br>(~R$ 1,0M)',
            showarrow=True,
            arrowhead=2,
            arrowsize=1.0, # Seta discreta
            arrowwidth=1.0, # Fina e elegante
            arrowcolor='white',
            standoff=6, # Garante que a seta aponte sem tocar o marcador
            ax=0,
            ay=-65,
            bgcolor='rgba(35, 35, 35, 0.92)',
            bordercolor='rgba(255, 255, 255, 0.15)',
            borderwidth=1,
            borderpad=8,
            font=dict(color='white', size=12)
        )

    # 4. Ajuste de Margens

    # Layout transparente
    layout_transparente = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    fig.update_layout(
        **layout_transparente,
        title=dict(
            text='<b>Receita e Volatilidade: Impacto Decisivo da Black Friday e Crescimento Sustentado</b><br><span style="font-size:13px; color:rgba(255,255,255,0.6);">Análise mensal consolidada (Out 2016 a Ago 2018) | Média Móvel (3m) e faixa de volatilidade</span>',
            x=0.01, y=0.95
        ),
        height=550,
        margin=dict(t=120, b=130, l=80, r=95),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=12)),
        hovermode='closest'
    )

    # 5. Eixos - Eliminação de Ruído (Barra Branca OFF)
    fig.update_xaxes(
        showgrid=False,
        tickangle=-45,
        dtick=2,
        title=None,
        tickfont=dict(color='rgba(255,255,255,0.8)'),
        showline=False,
        zeroline=False
    )

    fig.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.1)',
        tickvals=[0, 200000, 400000, 600000, 800000, 1000000, 1200000],
        ticktext=['R$ 0', '200k', '400k', '600k', '800k', '1,0M', '1,2M'],
        title=None,
        tickfont=dict(color='rgba(255,255,255,0.8)'),
        showline=False,
        zeroline=False
    )

    return fig
