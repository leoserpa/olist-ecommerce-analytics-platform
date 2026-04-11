import plotly.graph_objects as go
import pandas as pd

def render_churn_receita(df_completo):
    """
    Renderiza um Waterfall Chart mostrando o fluxo de churn de receita 
    (cancelamentos e falta de estoque). Usa a base completa para pegar atritos.
    """
    # 1. Agrupamento e Cálculos
    status_fin = df_completo.groupby('order_status')['price'].sum().reset_index()

    # Tratamentos seguros de extração (evita KeyError)
    cancelado = 0
    if 'canceled' in status_fin['order_status'].values:
        cancelado = status_fin.loc[status_fin['order_status'] == 'canceled', 'price'].values[0]
        
    indisponivel = 0
    if 'unavailable' in status_fin['order_status'].values:
        indisponivel = status_fin.loc[status_fin['order_status'] == 'unavailable', 'price'].values[0]

    valido_status = ['delivered', 'shipped', 'invoiced', 'processing', 'approved']
    receita_real = status_fin[status_fin['order_status'].isin(valido_status)]['price'].sum()
    
    total_potencial = receita_real + cancelado + indisponivel

    # 2. Formatação PT-BR
    def fmt_br_final(val, is_m=True):
        if is_m:
            return f"R$ {val/1e6:.2f}".replace('.', ',') + " M"
        return f"-R$ {val/1000:.1f}".replace('.', ',') + " k"

    labels_waterfall = [
        fmt_br_final(total_potencial),
        fmt_br_final(cancelado, False),
        fmt_br_final(indisponivel, False),
        fmt_br_final(receita_real)
    ]

    # 3. Construção do Waterfall
    fig = go.Figure(go.Waterfall(
        name = "Fluxo",
        orientation = "v",
        measure = ["absolute", "relative", "relative", "total"],
        x = ["Receita Bruta<br>Potencial", "Cancelados", "Falta de<br>Estoque", "Receita<br>Efetivada"],
        textposition = "outside",
        text = labels_waterfall,
        textfont = dict(size=14, color='white', family='Arial'),
        y = [total_potencial, -cancelado, -indisponivel, receita_real],
        connector = {"line":{"color":"rgba(128, 128, 128, 0.4)", "width": 1, "dash": "solid"}},
        decreasing = {"marker":{"color":"#e67e22", "line":{"width":0}}},
        increasing = {"marker":{"color":"#1f77b4", "line":{"width":0}}},
        totals = {"marker":{"color":"#1f77b4", "line":{"width":0}}}
    ))

    # 4. Layout
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        title=dict(
            text="<b>Diagnóstico Financeiro: O Vazamento de Receita</b><br><span style='font-size:14px; color:rgba(255,255,255,0.6);'>Análise de evasão por atritos operacionais (Cancelamentos e Estoque)</span>",
            x=0.01, y=0.95
        ),
        xaxis=dict(
            showgrid=False,
            showline=False,
            zeroline=False,
            ticks="",
            tickfont=dict(size=12, color='rgba(255,255,255,0.8)')
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            zeroline=False,
            showticklabels=False,
            title=None,
            range=[0, total_potencial * 1.12]
        ),
        height=600,
        margin=dict(t=120, b=60, l=40, r=40),
        showlegend=False
    )

    return fig
