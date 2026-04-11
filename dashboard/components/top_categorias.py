import pandas as pd
import plotly.express as px

def render_top_categorias(df):
    # Agrupamento e tradução
    categorias = df.groupby('product_category').agg(
        receita=('price', 'sum'),
        pedidos=('order_id', 'nunique'),
        ticket_medio=('price', 'mean')
    ).reset_index().sort_values('receita', ascending=False)
    
    traducao_categorias = {
        'health_beauty': 'Beleza e Saúde',
        'watches_gifts': 'Relógios e Presentes',
        'bed_bath_table': 'Cama, Mesa e Banho',
        'sports_leisure': 'Esporte e Lazer',
        'computers_accessories': 'Informática e Acessórios',
        'furniture_decor': 'Móveis e Decoração',
        'housewares': 'Utilidades Domésticas',
        'auto': 'Automotivo',
        'garden_tools': 'Ferramentas de Jardim',
        'cool_stuff': 'Brinquedos e Games'
    }
    categorias['product_category'] = categorias['product_category'].map(traducao_categorias).fillna(categorias['product_category'])
    
    top10_receita = categorias.head(10).copy()
    
    # --- Cálculos de Storytelling Executivo ---
    total_top10 = top10_receita['receita'].sum()
    top10_receita['pct_top10'] = (top10_receita['receita'] / total_top10 * 100).round(1)
    pct_top3 = (top10_receita.head(3)['receita'].sum() / total_top10 * 100).round(0)
    
    # Preparação do gráfico
    top10_plot = top10_receita.sort_values('receita')
    cores_destaque = ['#808080'] * (len(top10_plot) - 1) + ['#1f77b4']
    
    # Formatação robusta dos rótulos (Padrão Sênior BR)
    labels_custom = []
    for v, p in zip(top10_plot['receita'], top10_plot['pct_top10']):
        p_str = f"{p:.1f}%".replace('.', ',')
        if v >= 1_000_000:
            valor_str = f"{v/1_000_000:.1f}M".replace('.', ',')
        else:
            valor_str = f"{v/1_000:.0f}K".replace('.', ',')
        labels_custom.append(f"R$ {valor_str} (~{p_str})")
    
    fig = px.bar(
        top10_plot,
        x='receita',
        y='product_category',
        orientation='h',
        title=f'<b>Saúde & Beleza Lidera Faturamento Acumulado (R$ 1,3M)</b><br><span style="font-size:13px; color:rgba(255,255,255,0.6);">Top 3 categorias concentram ~{pct_top3:.0f}% das vendas líderes no período</span>',
        text=labels_custom
    )
    
    fig.update_traces(
        marker_color=cores_destaque,
        textposition='outside',
        textfont=dict(size=12, color='white'),
        cliponaxis=False,
        width=0.90 # Barras mais largas para compactação
    )
    
    layout_transparente = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    fig.update_layout(
        **layout_transparente,
        title_x=0,
        height=500,
        showlegend=False,
        margin=dict(l=0, r=180, t=100, b=60), # l=0 para aproximar eixo Y
        bargap=0.02 # Gap mínimo para visual sólido
    )
    
    # Remoção total do Eixo X
    fig.update_xaxes(
        showgrid=False,
        showline=False,
        zeroline=False,
        showticklabels=False,
        title=None
    )
    
    fig.update_yaxes(
        ticks='outside',
        ticklen=2,
        tickcolor='rgba(0,0,0,0)',
        showgrid=False,
        showline=False,
        zeroline=False,
        title=None,
        automargin=True,
        tickfont=dict(size=12, color='white')
    )
    
    # Nota de Rodapé Removida
    
    return fig
