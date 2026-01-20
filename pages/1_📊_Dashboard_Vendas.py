import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from config import Config
from api_client import TinyAPIClient
from ibge_client import IBGEClient
from utils import TextUtils, DataUtils

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(page_title="Dashboard de Vendas", layout="wide", page_icon="📊")

st.title("📊 Mapa de Vendas")
st.markdown("Visão geográfica e indicadores de desempenho.")

# ============================================================
# FILTROS LATERAIS
# ============================================================
st.sidebar.header("Filtros")

try:
    token = st.secrets["tiny_api_token"]
except KeyError:
    st.error("Token não configurado! Configure no painel do Streamlit Cloud.")
    st.stop()

# Filtro de Data
data_ini = st.sidebar.date_input("Data Inicial", datetime(2026, 1, 1))
data_fim = st.sidebar.date_input("Data Final", datetime.now())

btn_atualizar = st.sidebar.button("🔄 Atualizar Dados", type="primary")

# ============================================================
# LÓGICA PRINCIPAL
# ============================================================

# Se não clicou, mostra mensagem de espera
if not btn_atualizar:
    st.info("👈 Ajuste as datas na barra lateral e clique em 'Atualizar Dados'.")
    st.stop()

# Se clicou, processa:
client = TinyAPIClient(token)

# 1. Carregar Coordenadas (Cacheado)
with st.spinner("Carregando base geográfica..."):
    df_ibge = IBGEClient.carregar_municipios()

# 2. Buscar Vendas no Tiny
with st.spinner("Buscando vendas no Tiny..."):
    vendas = client.buscar_vendas(data_ini, data_fim)

if not vendas:
    st.warning("Nenhuma venda encontrada neste período.")
    st.stop()

# 3. Processamento dos Dados
with st.spinner("Cruzando dados geográficos..."):
    dados_processados = []
    
    for venda_wrapper in vendas:
        venda = venda_wrapper.get('nota_fiscal', venda_wrapper)
        
        # Extração segura de dados
        cidade = venda.get('nome_municipio', '')
        uf = venda.get('uf', '')
        valor = DataUtils.converter_valor(venda.get('valor_nota'))
        cliente = venda.get('nome', 'Consumidor Final')
        
        # Identificação de Canal (Regra de Negócio Simplificada)
        obs = str(venda.get('obs', '')).lower()
        num_ordem = str(venda.get('numero_ordem_compra', '')).lower()
        
        canal = "Venda Direta"
        if "shopee" in obs or "shopee" in num_ordem:
            canal = "Shopee"
        elif "mercado livre" in obs or "mercadolivre" in obs or "ml" in num_ordem:
            canal = "Mercado Livre"
        elif "site" in obs or "loja integrada" in obs:
            canal = "Site"
            
        if cidade and uf:
            chave = TextUtils.gerar_chave_cidade(cidade, uf)
            
            dados_processados.append({
                'chave_cidade': chave,
                'Cidade_Original': cidade,
                'Estado': uf,
                'Valor': valor,
                'Canal': canal,
                'Cliente': cliente
            })
    
    df_vendas = pd.DataFrame(dados_processados)

    if df_vendas.empty:
        st.warning("Vendas encontradas, mas sem dados de endereço para o mapa.")
        st.stop()

    # Cruzamento com IBGE (Merge)
    df_final = pd.merge(
        df_vendas,
        df_ibge,
        on='chave_cidade',
        how='inner'
    )
    
    # Agrupamento por Cidade e Canal (para as bolinhas do mapa)
    df_agrupado = df_final.groupby(
        ['chave_cidade', 'Cidade_Original', 'Estado', 'latitude', 'longitude', 'Canal']
    ).agg({
        'Valor': 'sum',
        'Cliente': 'count' # Contagem de pedidos
    }).reset_index()

    # ============================================================
    # VISUALIZAÇÃO (DASHBOARD)
    # ============================================================
    
    # KPIs (Indicadores no Topo)
    total_fat = df_final['Valor'].sum()
    ticket_medio = df_final['Valor'].mean() if not df_final.empty else 0
    top_canal = df_final['Canal'].mode()[0] if not df_final.empty else "N/A"
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Faturamento Total", f"R$ {total_fat:,.2f}")
    col2.metric("🎫 Ticket Médio", f"R$ {ticket_medio:,.2f}")
    col3.metric("🏆 Canal Principal", top_canal)
    
    st.divider()
    
    # --- ÁREA DO MAPA (Melhorada para Mobile) ---
    
    col_titulo_mapa, col_toggle = st.columns([3, 1])
    with col_titulo_mapa:
        st.subheader("🗺️ Distribuição Geográfica")
    with col_toggle:
        # Botão para expandir
        modo_tela_cheia = st.toggle("🔭 Ampliar Mapa", value=False)
    
    # Define a altura baseada no botão
    altura_dinamica = 850 if modo_tela_cheia else 450
    zoom_inicial = 3.5 if modo_tela_cheia else 3
    
    # Criando o Mapa
    fig = px.scatter_mapbox(
        df_agrupado,
        lat="latitude",
        lon="longitude",
        size="Valor",
        color="Canal",
        hover_name="Cidade_Original",
        hover_data={"Valor": ":.2f", "Cliente": True, "latitude": False, "longitude": False},
        zoom=zoom_inicial,
        size_max=35, # Bolinhas um pouco maiores para facilitar toque
        center={"lat": -15.7, "lon": -47.8}, # Centro do Brasil
        title=None
    )
    
    # Estilo do Mapa (Clean para facilitar visualização)
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0,"t":0,"l":0,"b":0},
        height=altura_dinamica,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.8)" # Fundo branco na legenda para ler melhor
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    if modo_tela_cheia:
        st.info("👆 Desative o botão 'Ampliar Mapa' para ver as tabelas e gráficos abaixo.")
    
    # --- OUTROS GRÁFICOS (Só aparecem se não estiver em tela cheia para não poluir) ---
    if not modo_tela_cheia:
        st.divider()
        
        col_bar, col_pie = st.columns([2, 1])
        
        with col_bar:
            st.subheader("Estados (Top 10)")
            df_estado = df_final.groupby('Estado')['Valor'].sum().sort_values(ascending=False).head(10).reset_index()
            fig_bar = px.bar(df_estado, x='Estado', y='Valor', text_auto='.2s', color='Valor')
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_pie:
            st.subheader("Canais de Venda")
            fig_pie = px.pie(df_final, values='Valor', names='Canal', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
