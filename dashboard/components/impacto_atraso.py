import plotly.graph_objects as go
import pandas as pd
import numpy as np

def render_impacto_atraso(df):
    # 1. Preparação dos Dados
    df_log = df[(df['pedido_item_seq'] == 1) & (df['atraso_entrega_dias'].notna())].copy()
    
    if df_log.empty:
        return None

    def categorizar_atraso(dias):
        if dias <= -5: return 'Muito Antecipado (>5d)'
        if dias < 0: return 'Antecipado (1-5d)'
        if dias == 0: return 'No Prazo'
        if dias <= 3: return 'Atraso Curto (1-3d)'
        if dias <= 7: return 'Atraso Médio (4-7d)'
        return 'Atraso Crítico (>7d)'

    df_log['faixa_atraso'] = df_log['atraso_entrega_dias'].apply(categorizar_atraso)

    ordem_faixas = ['Muito Antecipado (>5d)', 'Antecipado (1-5d)', 'No Prazo', 'Atraso Curto (1-3d)', 'Atraso Médio (4-7d)', 'Atraso Crítico (>7d)']
    satisfacao_atraso = df_log.groupby('faixa_atraso')['review_score'].mean().reindex(ordem_faixas).reset_index()

    # 2. Cores Estratégicas (Semáforo)
    cores_atraso = ['#1f77b4', '#808080', '#808080', '#e67e22', '#e67e22', '#e67e22']

    # Formatação PT-BR
    labels_barras = []
    for x in satisfacao_atraso['review_score']:
        val_fmt = f"{x:.2f}".replace('.', ',')
        if val_fmt == '4,00':
            labels_barras.append('4,0')
        else:
            labels_barras.append(val_fmt)

    # 3. Construção do Gráfico
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=satisfacao_atraso['faixa_atraso'],
        y=satisfacao_atraso['review_score'],
        text=labels_barras,
        textposition='outside',
        marker_color=cores_atraso,
        marker_line_color='rgba(255,255,255,0.4)', # Borda para separar as barras grudadas
        marker_line_width=1.5,
        textfont=dict(size=14, color='white'),
        cliponaxis=False
    ))

    # 4. Linha de Referência (Média Geral)
    media_geral = df_log['review_score'].mean()
    fig.add_shape(
        type="line", line=dict(color="rgba(255,255,255,0.3)", width=1, dash="dot"),
        x0=-0.5, x1=5.5, y0=media_geral, y1=media_geral,
        layer='below'
    )

    fig.add_annotation(
        x=5.2, y=media_geral + 0.15,
        text=f"Média Geral: {media_geral:.2f}".replace('.', ','),
        showarrow=False, font=dict(color="#E0E0E0", size=12)
    )

    # Layout transparente base
    layout_transparente = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    # 5. Adicionando Rodapé (Removido)

    # 6. Layout Executivo
    fig.update_layout(
        **layout_transparente,
        title=dict(
            text="<b>O Impacto do Atraso: A Queda Drástica na Satisfação após o 3º Dia</b><br><span style='font-size:14px; color:rgba(255,255,255,0.6);'>Notas médias de review por faixa de cumprimento de SLA (Dias entre entrega real e prometida)</span>",
            x=0.0, y=0.95
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            title=None,
            range=[0, 5.2]
        ),
        xaxis=dict(
            title=None,
            showgrid=False,
            showline=False,
            zeroline=False,
            ticks='',
            showticklabels=True,
            tickfont=dict(size=12, color='rgba(255,255,255,0.8)')
        ),
        height=550,
        margin=dict(t=100, b=100, l=60, r=60),
        bargap=0
    )

    return fig
