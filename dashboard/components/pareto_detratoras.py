import pandas as pd
import plotly.express as px

def render_pareto_detratoras(df):
    """
    Pareto de Categorias Detratoras (Quem "mata" a nota?)
    Identifica as categorias com maior volume de avaliações 1 e 2 estrelas.
    """
    # 1. Preparação dos Dados
    # Filtramos seq=1 para contar o sentimento por pedido único
    df_detratores = df[(df['pedido_item_seq'] == 1) & (df['review_score'].isin([1, 2]))].copy()

    pareto_categoria = df_detratores.groupby('product_category')['order_id'].count().reset_index()
    pareto_categoria.columns = ['Categoria', 'Volume_Detracao']

    # 2. Tradução das Categorias (Padrão do Projeto)
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
        'cool_stuff': 'Brinquedos e Games',
        'baby': 'Bebês',
        'telephony': 'Telefonia',
        'toys': 'Brinquedos'
    }

    pareto_categoria['Categoria'] = pareto_categoria['Categoria'].map(traducao_categorias).fillna(pareto_categoria['Categoria'])

    # Ordenar e pegar as Top 12 para visualização completa conforme solicitado
    pareto_categoria = pareto_categoria.sort_values('Volume_Detracao', ascending=True).tail(12)

    # 3. Inversão Semântica de Cores (Storytelling Executivo)
    # Laranja Vibrante (#e67e22) para o maior ofensor, Cinza (#808080) para as outras 11
    cores_detracao = ['#808080'] * (len(pareto_categoria) - 1) + ['#e67e22']

    # 4. Gerar o Gráfico de Barras Horizontais
    fig = px.bar(
        pareto_categoria,
        x='Volume_Detracao',
        y='Categoria',
        orientation='h',
        title='<b>Foco na Qualidade: Onde Residem as Maiores Críticas?</b><br><span style="font-size:13px; color:rgba(255,255,255,0.7);">Ranking de Detratores: Cama, Mesa e Banho lidera o volume de avaliações 1 e 2 estrelas, sinalizando a necessidade de auditoria de produto.</span>',
        text='Volume_Detracao'
    )

    # 5. Estilização de Traços e Rótulos
    fig.update_traces(
        marker_color=cores_detracao,
        textposition='outside',
        textfont=dict(size=12, color='white'),
        cliponaxis=False,
        width=0.85
    )

    layout_transparente = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    # 6. Layout Executivo Transparente
    fig.update_layout(
        **layout_transparente,
        title_x=0.01,
        title_y=0.98,
        height=600,
        showlegend=False,
        margin=dict(l=10, r=100, t=100, b=60),
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
