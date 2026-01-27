import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from datetime import datetime, date, timedelta
from api_client import TinyAPIClient
from database import DatabaseManager
from utils import DataUtils

# ============================================================
# CONFIGURAÇÃO GERAL
# ============================================================
st.set_page_config(
    page_title="PlanteForte ERP",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa Banco Local
db = DatabaseManager()
db.inicializar_banco()

# ============================================================
# FUNÇÕES DE APOIO (INTEGRIDADE DOS DADOS)
# ============================================================

def gerar_assinatura_venda(venda, valor_float):
    """
    Gera o mesmo 'RG' único usado no Dashboard de Vendas.
    Formato: YYYYMMDD-NomeClienteSemEspaco-ValorCentavos
    """
    try:
        # 1. Data (Tiny envia geralmente como dd/mm/yyyy)
        data_str = venda.get('data_emissao', '')
        try:
            dt = datetime.strptime(data_str, '%d/%m/%Y')
        except ValueError:
            # Tenta fallback para formato ISO se mudar
            try:
                dt = datetime.strptime(data_str, '%Y-%m-%d')
            except:
                dt = date.today() # Fallback extremo (raro)
        
        d = dt.strftime('%Y%m%d')
        
        # 2. Cliente (Remove espaços para evitar erros de digitação)
        c = str(venda.get('nome', '')).strip().replace(" ", "")
        
        # 3. Valor (Em centavos para evitar flutuação de float)
        v = str(int(valor_float * 100))
        
        return f"{d}-{c}-{v}"
    except Exception:
        return "erro-geracao-id"

def identificar_canal(nota):
    """
    Identifica o canal de venda baseado no PADRÃO DO PEDIDO (xPed).
    """
    xPed = str(nota.get('numero_ecommerce', '')).strip()
    if not xPed:
        xPed = str(nota.get('numero_ordem_compra', '')).strip()
    
    xPed_upper = xPed.upper()
    
    # REGRA 1: xPed Vazio -> Tenta achar palavras chave
    if not xPed or xPed_upper in ['NONE', 'NULL', 'N/A']:
        texto_fallback = (str(nota.get('obs', '')) + str(nota.get('nome', ''))).lower()
        if 'shopee' in texto_fallback: return "Shopee"
        if 'mercado' in texto_fallback or 'ebazar' in texto_fallback: return "Mercado Livre"
        return "Venda Direta"

    # REGRA 2: Shopee (Letras + Números)
    tem_letra = any(c.isalpha() for c in xPed)
    tem_numero = any(c.isdigit() for c in xPed)
    if tem_letra and tem_numero:
        return "Shopee"

    # REGRA 3: Numéricos
    if xPed.isdigit():
        if len(xPed) > 10:
            return "Mercado Livre"
        else:
            return "Site"
            
    return "Shopee" if tem_letra else "Venda Direta"

# ============================================================
# FUNÇÕES DE CACHE E LÓGICA (BACKEND)
# ============================================================

@st.cache_data(ttl=60) # Cache reduzido para 60s para refletir exclusões rápido
def buscar_dados_tiny_filtrados(token, data_ini, data_fim):
    """
    Busca vendas no Tiny e aplica o filtro da BLACKLIST (Lixeira).
    Só soma o que não foi excluído no Dashboard.
    """
    # 1. Busca a Lista Negra atualizada do Banco
    blacklist_ids = db.obter_blacklist()
    
    client = TinyAPIClient(token)
    vendas = client.buscar_vendas(data_ini, data_fim)
    
    total_vendas = 0.0
    qtd_pedidos = 0
    por_canal = {"Shopee": 0.0, "Mercado Livre": 0.0, "Site": 0.0, "Venda Direta": 0.0}
    
    if vendas:
        for v_wrap in vendas:
            v = v_wrap.get('nota_fiscal', v_wrap)
            
            # Valor
            raw_valor = v.get('valor_nota') or v.get('valor') or v.get('valor_total')
            valor = DataUtils.converter_valor(raw_valor)
            
            # --- O FILTRO MÁGICO ---
            # Gera a assinatura dessa venda
            assinatura = gerar_assinatura_venda(v, valor)
            
            # Se a assinatura estiver na blacklist, IGNORE esta venda
            if assinatura in blacklist_ids:
                continue 
            # -----------------------
            
            total_vendas += valor
            qtd_pedidos += 1
            
            canal = identificar_canal(v)
            if canal in por_canal:
                por_canal[canal] += valor
            else:
                por_canal["Venda Direta"] += valor 
                
    return total_vendas, qtd_pedidos, por_canal

def buscar_dados_financeiros_locais(data_ini, data_fim):
    """Busca Contas a Pagar e Saldo Total"""
    df = db.buscar_lancamentos()
    
    contas_pagar_periodo = 0.0
    saldo_caixa_total = 0.0
    
    if df is not None and not df.empty:
        df['data'] = pd.to_datetime(df['data']).dt.date
        
        # 1. Contas a Pagar (Saída + Pendente + No Período)
        mask_pagar = (
            (df['tipo_movimento'] == 'Saída') & 
            (df['status'] == 'Pendente') &
            (df['data'] >= data_ini) & 
            (df['data'] <= data_fim)
        )
        contas_pagar_periodo = df.loc[mask_pagar, 'valor'].sum()
        
        # 2. Saldo Total (Entradas Pagas - Saídas Pagas)
        entradas = df.loc[(df['tipo_movimento'] == 'Entrada') & (df['status'] == 'Pago'), 'valor'].sum()
        saidas = df.loc[(df['tipo_movimento'] == 'Saída') & (df['status'] == 'Pago'), 'valor'].sum()
        saldo_caixa_total = entradas - saidas
        
    return contas_pagar_periodo, saldo_caixa_total

# ============================================================
# INTERFACE (FRONTEND)
# ============================================================

col_logo, col_header, col_user = st.columns([1, 4, 2])
with col_logo:
    try:
        with open("logo.png", "rb") as f:
            encoded_image = base64.b64encode(f.read()).decode()
        st.markdown(f'<img src="data:image/png;base64,{encoded_image}" style="width: 100px; border-radius: 10px;">', unsafe_allow_html=True)
    except:
        st.header("🌱")

with col_header:
    st.title("Cockpit Gerencial")
    st.markdown(f"**{datetime.now().strftime('%d/%m/%Y')}** | Visão Integrada")

with col_user:
    st.info("🏢 Matriz: **AURIFLAMA-SP**")

st.divider()

col_filtro, col_vazio = st.columns([2, 4])
with col_filtro:
    periodo = st.selectbox(
        "📅 Analisar Período:",
        ["Hoje", "Este Mês", "Este Ano"],
        index=0
    )

hoje = date.today()
if periodo == "Hoje":
    d_ini, d_fim = hoje, hoje
    texto_periodo = "Hoje"
elif periodo == "Este Mês":
    d_ini = hoje.replace(day=1)
    d_fim = hoje
    texto_periodo = "Neste Mês"
else:
    d_ini = hoje.replace(month=1, day=1)
    d_fim = hoje
    texto_periodo = "Neste Ano"

try:
    token = st.secrets["tiny_api_token"]
except:
    st.error("Token do Tiny não configurado!")
    st.stop()

with st.spinner(f"Consolidando dados ({texto_periodo})..."):
    # Chama a função nova COM FILTRO
    vendas_tiny, qtd_pedidos, canais_dict = buscar_dados_tiny_filtrados(token, d_ini, d_fim)
    a_pagar_local, saldo_caixa = buscar_dados_financeiros_locais(d_ini, d_fim)

st.subheader(f"📊 Resultados: {texto_periodo}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Vendas Faturadas", f"R$ {vendas_tiny:,.2f}", "Notas Emitidas (Líquido)")
c2.metric("🧾 Contas a Pagar", f"R$ {a_pagar_local:,.2f}", f"Vencendo: {periodo}", delta_color="inverse")
c3.metric("🏦 Saldo em Caixa", f"R$ {saldo_caixa:,.2f}", "Disponível (Acumulado)")
c4.metric("📦 Pedidos/Notas", f"{qtd_pedidos}", "Volume de Vendas")

st.divider()

st.subheader("🛒 Origem das Vendas")
col_graf, col_detalhe = st.columns([2, 1])

with col_graf:
    if vendas_tiny > 0:
        df_canais = pd.DataFrame(list(canais_dict.items()), columns=['Canal', 'Valor'])
        df_canais = df_canais[df_canais['Valor'] > 0]
        
        if not df_canais.empty:
            fig = px.pie(
                df_canais, values='Valor', names='Canal', hole=0.5, color='Canal',
                color_discrete_map={
                    "Mercado Livre": "#FFE600", "Shopee": "#FF5722", 
                    "Site": "#2E7D32", "Venda Direta": "#111111"
                }
            )
            fig.update_layout(
                annotations=[dict(text=f'R$ {vendas_tiny:,.0f}', x=0.5, y=0.5, font_size=16, showarrow=False)],
                margin=dict(l=20, r=20, t=0, b=0), height=300, showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Vendas encontradas, mas canal não identificado.")
    else:
        st.info(f"Sem vendas válidas em: {periodo}")

with col_detalhe:
    st.markdown("##### Detalhamento")
    for canal, valor in canais_dict.items():
        if valor > 0:
            perc = (valor / vendas_tiny) if vendas_tiny > 0 else 0
            st.write(f"**{canal}**")
            st.progress(perc)
            st.caption(f"R$ {valor:,.2f} ({perc:.1%})")

st.divider()
st.subheader("🚀 Ações Rápidas")
col_a, col_b, col_c = st.columns(3)

with col_a:
    if st.button("🗺️ Mapa de Vendas", use_container_width=True):
        st.switch_page("pages/1_📊_Dashboard_Vendas.py")
with col_b:
    st.button("📦 Estoque (Em Breve)", use_container_width=True, disabled=True)
with col_c:
    st.button("⚙️ Configurações", use_container_width=True, disabled=True)
