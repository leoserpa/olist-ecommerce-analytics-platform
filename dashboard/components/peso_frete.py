import pandas as pd
import plotly.express as px

def render_peso_frete(df):
    """
    Renderiza o gráfico de dispersão (scatter plot) correlacionando Peso do Produto x Frete.
    Padrão visual executivo/Tufte-style com linha de tendência OLS.
    """
    # 1. Preparação dos Dados
    # Vamos usar o df_completo repassado pelo dashboard
    df_fisica = df.dropna(subset=['product_weight_g', 'freight_value']).copy()
    df_fisica = df_fisica[df_fisica['freight_value'] > 0]

    # Conversão de Gramas para Quilos (kg) para um dashboard mais sênior
    df_fisica['product_weight_kg'] = df_fisica['product_weight_g'] / 1000

    # Sample estratégico para fluidez no front-end do Streamlit (não travar o navegador)
    df_sample = df_fisica.sample(min(10000, len(df_fisica)), random_state=42)

    # 2. Construção do Gráfico com Storytelling
    fig = px.scatter(
        df_sample,
        x='product_weight_kg',
        y='freight_value',
        opacity=0.25,
        color_discrete_sequence=['#e67e22'], # Laranja para representar custo/alerta
        trendline="ols",
        trendline_color_override="white",
        title="<b>Logística Física: O Peso como Driver de Custo de Frete</b><br><span style='font-size:13px; color:rgba(255,255,255,0.6);'>Análise de correlação: A inclinação da reta confirma que o peso é o principal fator de variação no frete.</span>",
        labels={'product_weight_kg': 'Peso (kg)', 'freight_value': 'Frete (R$)'}
    )

    # 3. Refinamento de Traços
    fig.update_traces(marker=dict(size=4))

    layout_transparente = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    # 4. Layout Executivo Transparente
    fig.update_layout(
        **layout_transparente,
        height=550,
        margin=dict(t=120, b=80, l=60, r=60),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor='rgba(255,255,255,0.1)',
            zeroline=False,
            title_font=dict(size=12, color='rgba(255,255,255,0.7)'),
            ticksuffix=' kg' # Adiciona a unidade diretamente no eixo
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            zeroline=False,
            title_font=dict(size=12, color='rgba(255,255,255,0.7)')
        )
    )

    return fig
