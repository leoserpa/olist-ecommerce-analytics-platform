import plotly.graph_objects as go

def render_atraso_vendedor(df_diag):
    """
    Renderiza o histograma de agilidade logística com linha de média e destaque de SLA.
    Gráfico 2.5 — Atraso do Vendedor (Diagnóstico Executivo).
    """
    
    # 1. Preparação e Limpeza
    df_post = df_diag[df_diag['pedido_item_seq'] == 1].copy()
    df_post = df_post.dropna(subset=['dias_para_postar'])
    df_post = df_post[df_post['dias_para_postar'] >= 0]
    df_post['dias'] = df_post['dias_para_postar'].astype(int)

    # Cálculo da Média Real
    media_val = df_post['dias'].mean()

    # Agrupamento para o gráfico (0 a 10 dias)
    df_count = df_post['dias'].value_counts().sort_index().reset_index()
    df_count.columns = ['dias', 'quantidade']
    df_count = df_count[(df_count['dias'] >= 0) & (df_count['dias'] <= 10)]

    # Cores SLA (Azul para <= 2, Cinza para o resto)
    cores = ['#1f77b4' if d <= 2 else '#848484' for d in df_count['dias']]

    # 2. Construção do Gráfico
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_count['dias'],
        y=df_count['quantidade'],
        marker_color=cores,
        marker_line_width=0,
        text=df_count['quantidade'],
        texttemplate='%{text:.2s}',
        textposition='outside',
        textfont=dict(size=11, color='white'),
        hovertemplate="<b>%{x} Dias</b><br>Volume: %{y:,}<extra></extra>"
    ))

    # 3. Linha da Média
    fig.add_vline(
        x=media_val,
        line_dash="dash",
        line_color="#FF8C00",
        annotation_text=f"Média: {media_val:.1f} dias",
        annotation_position="top right",
        annotation_font=dict(size=12, color="#FF8C00")
    )

    # 4. Layout
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        title=dict(
            text="<b>Agilidade Logística: Cumprimento do SLA de Postagem</b><br><span style='font-size:13px; color:rgba(255,255,255,0.6);'>Desempenho dos vendedores no despacho inicial | Destaque para eficiência em até 48h</span>",
            x=0.01, y=0.95
        ),
        height=600,
        margin=dict(t=120, b=80, l=50, r=50),
        xaxis=dict(
            dtick=1,
            showgrid=False,
            range=[-0.5, 10.5],
            title_font=dict(size=11, color='gray')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            title='',
            showticklabels=False
        ),
        showlegend=False
    )

    return fig
