import plotly.express as px
import pandas as pd

def render_comportamento_compra(df):
    """
    Renderiza heatmap de picos de conversão por hora do dia e dia da semana.
    """
    # 1. Preparação dos Dados
    # O df original no painel não tem a sequencia garantida, vamos apenas usar o dataframe base
    # (assumindo que df é iterfável para conversão e df_completo já possui timestamps)
    df_temp = df.copy()

    # Verifica se a coluna 'order_purchase_timestamp' existe no formato datetime
    if 'order_purchase_timestamp' in df_temp.columns:
        if not pd.api.types.is_datetime64_any_dtype(df_temp['order_purchase_timestamp']):
            df_temp['order_purchase_timestamp'] = pd.to_datetime(df_temp['order_purchase_timestamp'])
        
        df_temp['hora'] = df_temp['order_purchase_timestamp'].dt.hour
        df_temp['dia_semana'] = df_temp['order_purchase_timestamp'].dt.day_name()
    else:
        # Se falhar (ex: dataframe pré-agrupado), retorna None
        return None

    dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    traducao_dias = {
        'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
        'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }

    # Só conta 1 por pedido para não duplicar se houver itens
    heatmap_data = df_temp.drop_duplicates(subset=['order_id']).groupby(['dia_semana', 'hora']).size().reset_index(name='pedidos')
    
    # Categorização para manter a ordem correta
    heatmap_data['dia_semana'] = pd.Categorical(heatmap_data['dia_semana'], categories=dias_ordem, ordered=True)
    heatmap_data['dia_pt'] = heatmap_data['dia_semana'].map(traducao_dias)

    # Criação do pivot
    pivot_heatmap = heatmap_data.pivot(index='dia_pt', columns='hora', values='pedidos').reindex(list(traducao_dias.values()))

    # 2. Construção do Heatmap (Design Sênior / Dark Mode)
    custom_colorscale = [
        [0, '#1a1a1a'],
        [0.5, '#124569'],
        [1, '#1f77b4']
    ]

    fig = px.imshow(
        pivot_heatmap,
        labels=dict(color="Pedidos"),
        x=list(range(24)),
        y=list(traducao_dias.values()),
        color_continuous_scale=custom_colorscale,
        aspect="auto"
    )

    # 3. Refinamento Estético
    fig.update_traces(
        xgap=2,
        ygap=2,
        hovertemplate="hora: %{x}<br>dia: %{y}<br>Pedidos: %{z}<extra></extra>"
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        title=dict(
            text="<b>Pico de Conversão: Dias Úteis à Tarde Concentram Maior Volume</b><br><span style='font-size:14px; color:rgba(255,255,255,0.6);'>Densidade de pedidos evidencia janelas de oportunidade para campanhas (10h às 16h)</span>",
            x=0.01, y=0.95
        ),
        xaxis=dict(
            tickmode='linear',
            dtick=2,
            title=None,
            showgrid=False,
            zeroline=False,
            ticks='',
            tickfont=dict(size=12, color='white')
        ),
        yaxis=dict(
            title=None,
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=12, color='white')
        ),
        coloraxis_showscale=False,
        height=480,
        margin=dict(t=100, b=50, l=10, r=10) # Margens otimizadas para app widescreen
    )

    # MARCA D'ÁGUA ("Fonte: ...") REMOVIDA PARA DATA-INK RATIO

    return fig
