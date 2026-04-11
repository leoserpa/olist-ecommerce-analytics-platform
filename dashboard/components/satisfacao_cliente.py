import plotly.express as px
import pandas as pd

def render_satisfacao_cliente(df):
    # 1. Preparação dos dados
    df_avaliados = df[(df['pedido_item_seq'] == 1) & (df['tem_avaliacao'] == True)].copy()
    
    if df_avaliados.empty:
        return None
        
    score_counts = df_avaliados['review_score'].value_counts().sort_index().reset_index()
    score_counts.columns = ['score', 'quantidade']
    
    total_avaliacoes = score_counts['quantidade'].sum()
    score_counts['percentual'] = (score_counts['quantidade'] / total_avaliacoes * 100).round(1)
    
    # Formatação de vírgula para o padrão BR
    labels_br = [f"{p:.1f}%".replace('.', ',') for p in score_counts['percentual']]
    
    # 2. Cores Estratégicas
    cores_score = ['#808080', '#808080', '#808080', '#808080', '#1f77b4']
    
    # 3. Construção do Gráfico
    fig = px.bar(
        score_counts,
        x='score',
        y='quantidade',
        title='<b>Foco na Excelência: Notas Máximas Dominam Satisfação do Cliente</b><br><span style="font-size:13px; color:rgba(255,255,255,0.6);">Distribuição de satisfação consolidada (Out 2016 a Ago 2018)</span>',
        text=labels_br
    )
    
    # 4. Refinamento de Traços - Rótulos nítidos (font 13px)
    fig.update_traces(
        marker_color=cores_score,
        textposition='outside',
        textfont=dict(size=13, color='rgba(255,255,255,0.9)', family='Arial'),
        cliponaxis=False,
        marker_line_width=0,
        width=0.75 # Igualado ao paradoxo_valor
    )
    
    layout_transparente = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    # 5. Layout Executivo - Alinhamento à Esquerda e Margens de Respiro Lateral
    fig.update_layout(
        **layout_transparente,
        title_x=0.01, # Igualado ao paradoxo
        height=480, # Igualado ao paradoxo do valor (480)
        showlegend=False,
        margin=dict(t=120, b=80, l=60, r=60), # Igualado ao paradoxo do valor
        bargap=0.25 # Igualado ao paradoxo do valor
    )
    
    # 6. Eixos Clean
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
