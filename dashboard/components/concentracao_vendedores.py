import plotly.graph_objects as go
import pandas as pd

def render_concentracao_vendedores(df):
    """
    Renderiza o gráfico de curva de Pareto da concentração de receita por vendedor.
    (80% da receita gerada por um percentual X de vendedores)
    """
    # 1. Preparação dos Dados
    seller_rank = df.groupby('seller_id')['price'].sum().sort_values(ascending=False).reset_index()
    seller_rank['cum_receita'] = (seller_rank['price'].cumsum() / seller_rank['price'].sum()) * 100
    seller_rank['cum_vendedores'] = ((seller_rank.index + 1) / len(seller_rank)) * 100

    # Ponto de 80% da receita
    # Filtramos até chegar no primeiro que ultrapassa ou bate em 80%
    ponto_80_df = seller_rank[seller_rank['cum_receita'] >= 80]
    
    if len(ponto_80_df) > 0:
        ponto_80 = ponto_80_df.iloc[0]
        pct_vendedores_80 = ponto_80['cum_vendedores']
    else:
        # Fallback de segurança se falhar
        pct_vendedores_80 = 20.0

    pct_formatada = f"{pct_vendedores_80:.1f}".replace('.', ',')

    # 2. Construção do Gráfico (Design Perfeccionista / Tufte)
    fig = go.Figure()

    # Curva de Pareto - Interatividade na linha
    fig.add_trace(go.Scatter(
        x=seller_rank['cum_vendedores'],
        y=seller_rank['cum_receita'],
        mode='lines',
        name='Curva',
        line=dict(color='#1f77b4', width=4),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.1)',
        hovertemplate="<b>%{x:.1f}%</b> dos vendedores → <b>%{y:.1f}%</b> da receita<extra></extra>",
        hoverlabel=dict(bgcolor='rgba(30, 30, 30, 0.9)', font_size=13, font_family='Arial')
    ))

    # Ponto Crítico 80/20
    fig.add_trace(go.Scatter(
        x=[pct_vendedores_80],
        y=[80],
        mode='markers+text',
        marker=dict(color='white', size=12, line=dict(color='#1f77b4', width=2)),
        text=[f"Top {pct_formatada}% Vendedores"],
        textposition="middle right",
        textfont=dict(color="white", size=14),
        cliponaxis=False,
        hoverinfo='skip'
    ))

    # Linhas de Referência
    fig.add_shape(type="line", x0=0, x1=pct_vendedores_80, y0=80, y1=80, line=dict(color="rgba(255,255,255,0.2)", dash="dot", width=1))
    fig.add_shape(type="line", x0=pct_vendedores_80, x1=pct_vendedores_80, y0=0, y1=80, line=dict(color="rgba(255,255,255,0.2)", dash="dot", width=1))

    # 3. Layout: Proteção de Títulos e Interatividade
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        title=dict(
            text=f"<b>Risco de Concentração: {pct_formatada}% dos Vendedores Geram 80% da Receita</b><br><span style='font-size:14px; color:rgba(255,255,255,0.6);'>Curva de Pareto indica alta dependência de um pequeno grupo de Top Sellers.</span>",
            x=0.01, y=0.95
        ),
        xaxis=dict(
            showgrid=False,
            range=[0, 100],
            zeroline=False,
            tickvals=[0, 20, 40, 60, 80, 100],
            ticksuffix='%',
            tickfont=dict(size=12, color='white')
        ),
        yaxis=dict(
            showgrid=False,
            range=[0, 105],
            zeroline=False,
            tickvals=[20, 40, 60, 80, 100], # Evita sobreposição na origem
            ticksuffix='%',
            tickfont=dict(size=12, color='white')
        ),
        hovermode='x',
        showlegend=False,
        height=550,
        margin=dict(t=100, b=50, l=40, r=150) # Margem ajustada para melhor uso de espaço no app
    )

    # REMOVIDA A MARCA D'ÁGUA ("Fonte: ...") PARA MANTER METÁFORA DATA-INK RATIO

    return fig
