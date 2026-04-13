import streamlit as st

def mostrar_insight_card(icone: str, titulo: str, texto: str, alerta: bool = False):
    """
    Renderiza um card de insight formatado (Tufte-style) logo abaixo de um gráfico Streamlit.
    Usa ícones vetoriais do Remix Icons (CDN CSS) para visual Enterprise.
    
    :param icone: Classe do ícone Remix Icons (ex: 'ri-bar-chart-2-line', 'ri-truck-line')
    :param titulo: Título forte em bold
    :param texto: Texto explicativo e executivo
    :param alerta: Se True, a borda vira laranja Olist (#e67e22), caso contrário azul padrão (#1f77b4)
    """
    cor_borda = "#e67e22" if alerta else "#1f77b4"
    
    html_card = f"""
    <div class='insight-card' style='
        background-color: #161717; 
        border-left: 4px solid {cor_borda}; 
        padding: 12px 18px; 
        margin-top: -15px; 
        margin-bottom: 20px; 
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15);
    '>
        <h4 style='color: #E0E0E0; margin: 0 0 4px 0; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px;'>
            <i class="{icone}" style="font-size: 16px; color: {cor_borda}; flex-shrink: 0;"></i>
            {titulo}
        </h4>
        <p style='color: rgba(255,255,255,0.65); margin: 0; font-size: 13px; line-height: 1.45;'>{texto}</p>
    </div>
    """
    
    st.markdown(html_card, unsafe_allow_html=True)
