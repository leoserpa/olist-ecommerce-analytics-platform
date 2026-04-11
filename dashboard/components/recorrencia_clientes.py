import pandas as pd
import plotly.express as px

def render_recorrencia_clientes(df):
    """
    Renderiza o gráfico de barras sobre Fidelização (Recorrência) de Clientes.
    Padrão visual executivo/Tufte-style com foco na retenção.
    """
    # 1. Preparação (Lógica CRM)
    # Filtro de compra consolidada (já que usamos o df_receita)
    df_pedidos = df[df['pedido_item_seq'] == 1].copy()

    compras_por_cliente = df_pedidos.groupby('customer_unique_id')['order_id'].nunique().reset_index()
    compras_por_cliente.columns = ['customer_unique_id', 'total_compras']

    # Classificação Simples Sênior (Única vs Retido)
    def classificar_fidelidade(qtd):
        return "Recorrente (2+ compras)" if qtd > 1 else "Compra Única (1 compra)"

    compras_por_cliente['Perfil_Fidelidade'] = compras_por_cliente['total_compras'].apply(classificar_fidelidade)
    
    resumo_fidelidade = compras_por_cliente['Perfil_Fidelidade'].value_counts().reset_index()
    resumo_fidelidade.columns = ['Perfil', 'Qtd_Clientes']

    taxa_retencao = (len(compras_por_cliente[compras_por_cliente['total_compras'] > 1]) / len(compras_por_cliente)) * 100

    # 2. Gerar o Gráfico de Barras Estilo Sênior
    fig = px.bar(
        resumo_fidelidade,
        x='Perfil',
        y='Qtd_Clientes',
        color='Perfil',
        color_discrete_map={
            "Compra Única (1 compra)": "#808080",
            "Recorrente (2+ compras)": "#e67e22"
        },
        text_auto='.2s',
        title="<b>Análise de Retenção: O Desafio da Recompra na Olist</b><br><span style='font-size:13px; color:rgba(255,255,255,0.6);'>Dependência de Novos Clientes: Apenas 3 em cada 100 compradores retornam à plataforma.</span>"
    )

    # 3. Estilo Executivo Transparente
    fig.update_traces(
        textposition='outside',
        textfont=dict(size=13, color='white'),
        cliponaxis=False,
        width=0.6
    )

    # 4. Placa de Destaque (Big Number) - Reposicionamento do conjunto completo
    fig.add_annotation(
        x="Recorrente (2+ compras)",
        y=0.18, 
        xref="x", yref="paper",
        text=f"Taxa de Retenção:<br><b style='font-size:22px'>{taxa_retencao:.2f}%</b>",
        showarrow=True,
        arrowhead=2,
        arrowcolor="white",
        standoff=5, 
        ax=0, ay=-50, 
        font=dict(size=14, color="#E67E22"),
        bgcolor="rgba(17,17,17,0.95)",
        bordercolor="rgba(255,255,255,0.15)",
        borderwidth=1,
        borderpad=12
    )

    layout_transparente = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    fig.update_layout(
        **layout_transparente,
        title_x=0.0,
        title_y=0.95,
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        height=480,
        margin=dict(t=100, b=50, l=0, r=10),
        bargap=0.1
    )

    # Limpeza de Eixos
    fig.update_xaxes(showgrid=False, showline=True, linecolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(showgrid=False, showline=False, zeroline=False, showticklabels=False)

    # Nota de Rodapé Removida para manter padrão do app
    
    return fig
