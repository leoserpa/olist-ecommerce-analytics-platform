import pandas as pd
import plotly.express as px

def render_top_ticket(df):
    # 0. Agrupamento Global (mesmo do outro gráfico)
    categorias = df.groupby('product_category').agg(
        receita=('price', 'sum'),
        pedidos=('order_id', 'nunique'),
        ticket_medio=('price', 'mean')
    ).reset_index().sort_values('receita', ascending=False)

    # 1. Preparação e Tradução de Dados
    categorias_relevantes = categorias[categorias['pedidos'] >= 100].copy()
    top10_ticket = categorias_relevantes.nlargest(10, 'ticket_medio').copy()

    traducao_refinada = {
        'computers': 'Computadores',
        'small_appliances': 'Eletroportáteis',
        'musical_instruments': 'Instrumentos Musicais',
        'agro_industry_and_commerce': 'Agro e Indústria',
        'home_appliances_2': 'Eletrodomésticos (Linha 2)',
        'air_conditioning': 'Ar Condicionado',
        'fixed_telephony': 'Telefonia Fixa',
        'construction_tools_safety': 'Ferramentas de Construção',
        'kitchen_dining_laundry_garden_furniture': 'Móveis de Jardim/Cozinha'
    }

    top10_ticket['product_category'] = top10_ticket['product_category'].map(traducao_refinada).fillna(top10_ticket['product_category'])
    top10_ticket_plot = top10_ticket.sort_values('ticket_medio')

    # 2. Lógica de Cores e Rótulos (Padrão Sênior - Master Polish)
    cores_ticket = ['#808080'] * (len(top10_ticket_plot) - 1) + ['#1f77b4']
    segundo_lugar_valor = top10_ticket_plot.iloc[-2]['ticket_medio']
    leader_valor = top10_ticket_plot.iloc[-1]['ticket_medio']
    multiplicador = leader_valor / segundo_lugar_valor

    labels_custom = []
    for i, row in top10_ticket_plot.iterrows():
        valor_br = f"R$ {row['ticket_medio']:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.')
        if row['product_category'] == 'Computadores':
            # Correção Master: 2,3x (vírgula para decimal)
            mult_str = f"{multiplicador:.1f}".replace('.', ',')
            labels_custom.append(f"<b>{valor_br}</b> ({mult_str}x o 2º lugar)")
        else:
            labels_custom.append(valor_br)

    fig = px.bar(
        top10_ticket_plot,
        x='ticket_medio',
        y='product_category',
        orientation='h',
        title='<b>Computadores Lidera Ticket Médio com o Dobro do 2º Lugar</b><br><span style="font-size:13px; color:rgba(255,255,255,0.6);">Dados consolidados (Out 2016 a Ago 2018) | Mínimo de 100 pedidos</span>',
        text=labels_custom
    )

    fig.update_traces(
        marker_color=cores_ticket,
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

    # 4. Layout Executivo (Aproximação e Compactação)
    fig.update_layout(
        **layout_transparente,
        title_x=0,
        height=500,
        showlegend=False,
        margin=dict(l=0, r=250, t=100, b=60), # l=0 para aproximar eixo Y da borda
        bargap=0.02 # Gap mínimo para visual sólido
    )

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
