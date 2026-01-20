import streamlit as st
import base64

# Configuração da Página
st.set_page_config(
    page_title="Portal PlanteForte",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CABEÇALHO COM LOGO (Mesmo estilo do Dashboard) ---
col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    try:
        with open("logo.png", "rb") as f:
            data = f.read()
            encoded_image = base64.b64encode(data).decode()
        st.markdown(
            f"""
            <div style="
                display: flex; justify-content: center; align-items: center;
                background-color: #FFFFFF; padding: 10px; border-radius: 15px; 
                width: 140px; height: 140px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            ">
                <img src="data:image/png;base64,{encoded_image}" style="max-width: 90%; max-height: 90%;">
            </div>
            """, unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.warning("Sem Logo")

with col_titulo:
    st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
    st.title("Portal Integrado PlanteForte")
    st.markdown("Sistema de Gestão e Inteligência de Dados.")

st.markdown("---")

# --- CONTEÚDO DA HOME ---

st.markdown("""
### 👋 Bem-vindo ao Sistema!

Utilize o **menu lateral à esquerda** para navegar entre as aplicações disponíveis.

#### 📂 Módulos Disponíveis:

* **📊 Dashboard de Vendas:**
    * Conexão com Tiny ERP
    * Mapa de calor e vendas por cidade
    * Indicadores de faturamento
    
* **🚀 Precificação:**
    * Gere o custo de produção e de o preço final do produto.
""")

# Dica visual
st.info("💡 Dica: Você pode esconder o menu lateral clicando no 'X' ou na seta no topo esquerdo para ter mais espaço de tela.")