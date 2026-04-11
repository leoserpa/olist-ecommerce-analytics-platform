import plotly.graph_objects as go
import pandas as pd

def render_distribuicao_status(df):
    """
    Renderiza o gráfico de Distribuição de status dos pedidos de forma idêntica ao Olist.ipynb
    """
    # 1. Preparação dos dados com cálculos de precisão
    status_counts = df[df['pedido_item_seq'] == 1]['order_status'].value_counts().reset_index()
    status_counts.columns = ['status', 'quantidade']

    traducao_status = {
        'delivered': 'Entregue',
        'shipped': 'Enviado',
        'canceled': 'Cancelado',
        'unavailable': 'Indisponível',
        'invoiced': 'Faturado',
        'processing': 'Em processamento',
        'created': 'Criado',
        'approved': 'Aprovado'
    }

    status_counts['status_pt'] = status_counts['status'].map(traducao_status).fillna(status_counts['status'])
    total_pedidos = status_counts['quantidade'].sum()
    status_counts['pct'] = (status_counts['quantidade'] / total_pedidos * 100)

    # Formatação da Legenda de Precisão (Tabela de Consulta)
    def format_legend(row):
        pct_str = f"{row['pct']:.1f}%" if row['pct'] >= 0.1 else "<0,1%"
        return f"{row['status_pt']} ({pct_str})"

    status_counts['legend_label'] = status_counts.apply(format_legend, axis=1)

    # 2. Design de Cores Estratégicas (Nível Sênior)
    cores_map = {
        'Entregue': '#1f77b4',         # Vibrant Blue
        'Enviado': '#808080',          # Grey
        'Faturado': '#4F4F4F',         # Graphite
        'Em processamento': '#FF8C00', # Vibrant Orange
        'Cancelado': '#363636',
        'Indisponível': '#2F2F2F',
        'Aprovado': '#F5F5F5'          # Off-White
    }

    cores_sequencia = [cores_map.get(s, '#808080') for s in status_counts['status_pt']]

    # 3. Construção do Donut Chart High-Performance
    fig = go.Figure(data=[go.Pie(
        labels=status_counts['legend_label'],
        values=status_counts['quantidade'],
        hole=0.72,
        marker=dict(colors=cores_sequencia, line=dict(color='rgba(0,0,0,0)', width=2)),
        textinfo='none',
        hoverinfo='label+value',
        sort=False,                # Mantém a ordem lógica da legenda
        showlegend=True
    )])

    # 4. KPI Central (Sincronizado Ativamente)
    pct_entregue = status_counts[status_counts['status_pt'] == 'Entregue']['pct'].sum()
    pct_formatado = f"{pct_entregue:.1f}%".replace('.', ',')

    fig.add_annotation(
        text=f"<span style='font-size:42px; font-weight:bold; color:#1f77b4;'>{pct_formatado}</span><br><span style='font-size:16px; font-weight:300; color:rgba(255,255,255,0.8);'>Entregues</span>",
        x=0.5, y=0.5, showarrow=False
    )

    # 5. Nota de Rodapé (Removido)

    # Variável global usada no notebook original
    layout_transparente = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    # 6. Layout de Consultoria (Padding e Alinhamento)
    fig.update_layout(
        **layout_transparente,
        title=dict(
            text="<b>Eficiência Logística: Pedidos Concluídos</b><br><span style='font-size:14px; color:rgba(255,255,255,0.6);'>Visão consolidada de status operacional</span>",
            x=0.01, y=0.95
        ),
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.1,
            font=dict(size=13, color='white'),
            bgcolor='rgba(0,0,0,0)'
        ),
        height=550,
        margin=dict(t=130, b=80, l=50, r=220) # Margem direita ampla para a legenda detalhada
    )

    return fig
