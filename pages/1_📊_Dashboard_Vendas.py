"""
Dashboard Comercial Tiny ERP - Versão Final v3
+ Ajuste fino no tamanho do mapa (Bolinhas médias)
+ Correção do erro de DuplicateWidgetID (Chave duplicada)
+ Busca textual na área de exclusão
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import time
import logging
import base64  
from datetime import datetime, timedelta

# Importar módulos customizados
from config import Config
from logger_config import logger
from api_client import TinyAPIClient, TinyAPIError
from ibge_client import IBGEClient
from data_processor import DataProcessor
from utils import ValidationUtils
from database import DatabaseManager

# ============================================================
# CONFIGURAÇÃO INICIAL
# ============================================================

st.set_page_config(
    page_title=Config.PAGE_TITLE,
    layout=Config.PAGE_LAYOUT,
    initial_sidebar_state=Config.SIDEBAR_STATE
)

# Inicializa Banco de Dados
db = DatabaseManager()
db.inicializar_banco()

# Inicializa Variáveis de Memória
if "dados_carregados" not in st.session_state:
    st.session_state["dados_carregados"] = None
if "mapa_carregado" not in st.session_state:
    st.session_state["mapa_carregado"] = None

st.markdown("""
<style>
    .metric-card { background-color: #f0f2f6; border-radius: 10px; padding: 15px; }
    .stPlotlyChart { height: auto; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CABEÇALHO
# ============================================================

col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    try:
        with open("logo.png", "rb") as f:
            encoded_image = base64.b64encode(f.read()).decode()
        st.markdown(f"""<div style="display: flex; justify-content: center; align-items: center; background-color: #FFFFFF; padding: 10px; border-radius: 15px; width: 140px; height: 140px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);"><img src="data:image/png;base64,{encoded_image}" style="max-width: 90%; max-height: 90%;"></div>""", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Sem Logo")

with col_titulo:
    st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
    st.title("Dashboard Comercial")
    st.markdown("Análise Geoespacial e Temporal de Vendas")

# ============================================================
# FUNÇÕES
# ============================================================

@st.cache_data(ttl=Config.CACHE_TTL, show_spinner=False)
def carregar_coordenadas_ibge():
    try:
        return IBGEClient.carregar_municipios()
    except Exception as e:
        return pd.DataFrame()

def gerar_id_unico(row):
    """Cria uma assinatura única para a venda: Data-Cliente-Valor"""
    try:
        d = row['Data_Obj'].strftime('%Y%m%d')
        c = str(row['Cliente']).strip().replace(" ", "")
        v = str(int(row['Valor'] * 100)) # Valor em centavos
        return f"{d}-{c}-{v}"
    except:
        return "erro"

def buscar_vendas_tiny_paginado(token: str, data_ini: datetime, data_fim: datetime):
    try:
        client = TinyAPIClient(token)
        texto_status = st.empty()
        barra = st.progress(0)
        
        texto_status.text("Buscando vendas...")
        vendas_raw = client.buscar_vendas(data_ini, data_fim)
        texto_status.text("Processando...")
        barra.progress(50)
        
        df_vendas = DataProcessor.processar_vendas_raw(vendas_raw)
        
        barra.progress(100)
        time.sleep(0.5)
        barra.empty()
        texto_status.empty()
        return df_vendas
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return pd.DataFrame()

# ============================================================
# BARRA LATERAL
# ============================================================

st.sidebar.header("⚙️ Filtros")

try:
    token = st.secrets["tiny_api_token"]
except KeyError:
    token = st.sidebar.text_input("Token API Tiny", type="password")

d_ini = st.sidebar.date_input("Data Inicial", Config.DATA_INICIO_PADRAO, format="DD/MM/YYYY")
d_fim = st.sidebar.date_input("Data Final", Config.DATA_FIM_PADRAO, format="DD/MM/YYYY")

if st.sidebar.button("🔄 Atualizar Dashboard", type="primary", use_container_width=True):
    if not token:
        st.error("Token não configurado.")
    else:
        with st.spinner("⏳ Carregando..."):
            if st.session_state["mapa_carregado"] is None:
                st.session_state["mapa_carregado"] = carregar_coordenadas_ibge()
            
            df_vendas = buscar_vendas_tiny_paginado(token, d_ini, d_fim)
            
            if not df_vendas.empty and not st.session_state["mapa_carregado"].empty:
                df_final = DataProcessor.enriquecer_com_coordenadas(df_vendas, st.session_state["mapa_carregado"])
                
                # Gera ID único para controle de exclusão
                df_final['id_unico'] = df_final.apply(gerar_id_unico, axis=1)
                
                st.session_state["dados_carregados"] = df_final
            else:
                st.warning("Sem dados para exibir.")
                st.session_state["dados_carregados"] = pd.DataFrame()

# ============================================================
# DASHBOARD
# ============================================================

if st.session_state["dados_carregados"] is not None and not st.session_state["dados_carregados"].empty:
    
    # 1. Aplica o Blacklist
    blacklist = db.obter_blacklist()
    df_visualizacao = st.session_state["dados_carregados"].copy()
    
    if blacklist:
        df_visualizacao = df_visualizacao[~df_visualizacao['id_unico'].isin(blacklist)]

    if df_visualizacao.empty:
        st.warning("Todos os dados foram excluídos ou filtrados.")
    else:
        # KPIs
        kpis = DataProcessor.calcular_kpis(df_visualizacao)
        
        st.markdown("---")
        st.subheader("📊 Indicadores Principais")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Faturamento", f"R$ {kpis['total_vendas']:,.2f}")
        c2.metric("🎫 Ticket Médio", f"R$ {kpis['ticket_medio']:,.2f}")
        c3.metric("📄 Notas", f"{kpis['notas_emitidas']:,}")
        c4.metric("🏙️ Cidades", f"{kpis['cidades_atendidas']}")
        
        # MAPA
        st.markdown("---")
        col_titulo_mapa, col_botao = st.columns([3, 1])
        with col_titulo_mapa:
            st.subheader("🗺️ Mapa de Vendas")
        with col_botao:
            modo_tela_cheia = st.toggle("🔭 Ampliar Mapa", value=False)
        
        altura_mapa = 900 if modo_tela_cheia else 600
        zoom_inicial = 3.5
        
        df_agrupado = df_visualizacao.groupby(
            ['chave_cidade', 'Cidade_Original', 'Estado', 'latitude', 'longitude', 'Canal']
        ).agg(Valor=('Valor', 'sum'), Qtd_Vendas=('Valor', 'count')).reset_index()
        
        cores_canais = {"Mercado Livre": "#FFE600", "Shopee": "#FF5722", "Site": "#2E7D32", "Venda Direta": "#111111"}

        # --- AJUSTE MAPA: Tamanho Médio (30) ---
        fig_mapa = px.scatter_mapbox(
            df_agrupado, lat="latitude", lon="longitude", size="Valor", color="Canal",
            color_discrete_map=cores_canais,
            hover_name="Cidade_Original",
            hover_data={"Estado": True, "Valor": ":.2f", "Qtd_Vendas": True, "latitude": False, "longitude": False, "Canal": True},
            size_max=30, # Reduzido para ficar elegante
            zoom=zoom_inicial, center={"lat": -14.2, "lon": -51.9},
            mapbox_style="carto-positron",
        )
        fig_mapa.update_traces(marker=dict(opacity=0.8, sizemin=4))
        fig_mapa.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=altura_mapa)
        
        st.plotly_chart(fig_mapa, use_container_width=True)
        
        if modo_tela_cheia:
            st.info("👆 Desative 'Ampliar Mapa' para ver os gráficos.")

        if not modo_tela_cheia:
            st.markdown("---")
            # Gráficos
            df_tempo = DataProcessor.agrupar_por_data(df_visualizacao)
            fig_tempo = px.line(df_tempo, x='Data_Obj', y='Valor', markers=True, title="Tendência Diária")
            fig_tempo.update_traces(line_color='#17a2b8', line_width=3)
            st.plotly_chart(fig_tempo, use_container_width=True)
            
            c_uf, c_cid = st.columns(2)
            with c_uf:
                df_uf = DataProcessor.agrupar_por_estado(df_visualizacao, top_n=10)
                st.plotly_chart(px.bar(df_uf, x='Estado', y='Valor', color='Valor', text_auto='.2s', title="Top Estados"), use_container_width=True)
            with c_cid:
                df_city = DataProcessor.agrupar_por_cidade(df_visualizacao, top_n=10)
                fig_city = px.bar(df_city, x='Valor', y='Cidade_Original', orientation='h', text_auto='.2s', title="Top Cidades")
                fig_city.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_city, use_container_width=True)
            
            # --- ÁREA DE GERENCIAMENTO (COM BUSCA e FIX DE CHAVE) ---
            st.markdown("---")
            st.subheader("🗑️ Gerenciar / Excluir Vendas")
            
            with st.expander("Ver Lista de Vendas para Exclusão", expanded=True):
                # Campo de Busca
                texto_busca = st.text_input("🔍 Buscar venda por Cliente ou Cidade:", placeholder="Digite para filtrar...")

                # Cabeçalho da Tabela
                c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 2, 1])
                c1.markdown("**Data**")
                c2.markdown("**Cliente**")
                c3.markdown("**Cidade**")
                c4.markdown("**Valor**")
                c5.markdown("**Ação**")
                st.divider()

                # Prepara a lista
                df_lista = df_visualizacao.sort_values(by='Data_Obj', ascending=False)
                
                # Aplica o Filtro de Texto
                if texto_busca:
                    termo = texto_busca.lower()
                    df_lista = df_lista[
                        df_lista['Cliente'].str.lower().str.contains(termo, na=False) | 
                        df_lista['Cidade_Original'].str.lower().str.contains(termo, na=False)
                    ]

                # Limita a 50 APÓS filtrar
                total_encontrado = len(df_lista)
                if total_encontrado > 50:
                    st.caption(f"Mostrando as últimas 50 de {total_encontrado} vendas encontradas.")
                    df_lista = df_lista.head(50)
                elif total_encontrado == 0:
                    st.info("Nenhuma venda encontrada com esse termo.")

                # Loop de exibição COM INDICE para garantir chave única
                for i, (idx, row) in enumerate(df_lista.iterrows()):
                    c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 2, 1])
                    
                    c1.text(row['Data_Obj'].strftime('%d/%m'))
                    c2.text(row['Cliente'])
                    c3.text(f"{row['Cidade_Original']}-{row['Estado']}")
                    c4.text(f"R$ {row['Valor']:,.2f}")
                    
                    # Botão com chave única combinando ID da venda + índice da lista
                    # Isso resolve o erro StreamlitDuplicateElementKey
                    if c5.button("🗑️", key=f"del_{row['id_unico']}_{i}"):
                        if db.adicionar_blacklist(row['id_unico']):
                            st.success("Removido!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Erro.")
                    
                    st.markdown("<hr style='margin: 5px 0'>", unsafe_allow_html=True)

elif st.session_state["dados_carregados"] is None:
    st.info("👈 Clique em **'Atualizar Dashboard'** para carregar os dados.")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")
st.markdown("""<div style="text-align: center; color: #999; font-size: 12px;">Dashboard Comercial Tiny ERP</div>""", unsafe_allow_html=True)    
