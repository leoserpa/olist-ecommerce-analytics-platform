import pandas as pd
import plotly.express as px

def render_metodos_pagamento(df):
    """
    Renderiza o gráfico de barras horizontais dos Métodos de Pagamento.
    Usa o padrão Tufte-style executivo adotado no projeto.
    """
    
    # 1. Preparação dos Dados
    # Como df recebidp já é o df_receita, os clientes pagos já estão filtrados
    # Filtramos seq=1 para contar cada pedido apenas uma vez
    df_pagamentos = df[df['pedido_item_seq'] == 1]['payment_type'].value_counts().reset_index()
    df_pagamentos.columns = ['Metodo', 'Pedidos']

    traducao = {
        'credit_card': 'Cartão de Crédito',
        'boleto': 'Boleto',
        'voucher': 'Cupom/Voucher',
        'debit_card': 'Cartão de Débito'
    }
    df_pagamentos['Metodo'] = df_pagamentos['Metodo'].map(traducao)

    df_pag_plot = df_pagamentos.sort_values('Pedidos', ascending=True)
    total_pag = df_pag_plot['Pedidos'].sum()
    df_pag_plot['pct'] = (df_pag_plot['Pedidos'] / total_pag * 100).round(1)

    labels_custom = []
    for pedidos, pct in zip(df_pag_plot['Pedidos'], df_pag_plot['pct']):
        p_str = f"{pct:.1f}%".replace('.', ',')
        v_str = f"{pedidos/1000:.1f}k".replace('.', ',')
        labels_custom.append(f"{v_str} ({p_str})")

    cores_pag = ['#808080'] * (len(df_pag_plot) - 1) + ['#1f77b4']

    # 2. Construção do Gráfico
    fig = px.bar(
        df_pag_plot,
        x='Pedidos',
        y='Metodo',
        orientation='h',
        title='<b>Cartão de Crédito é o Método Preferencial de Compra</b><br><span style="font-size:13px; color:rgba(255,255,255,0.6);">Dominância Estratégica: O crédito processa 3 em cada 4 pedidos realizados na plataforma.</span>',
        text=labels_custom
    )

    # 3. Refinamento de Traços
    fig.update_traces(
        marker_color=cores_pag,
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

    # 4. Layout Executivo Transparente
    fig.update_layout(
        **layout_transparente,
        title_x=0.01,
        title_y=0.95,
        height=550, # Igual ao distribuicao_status.py
        showlegend=False,
        margin=dict(t=130, b=80, l=0, r=180), # Margens top e bottom iguais à esquerda
        bargap=0.1
    )

    # Limpeza Total de Eixos
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
    
    return fig
