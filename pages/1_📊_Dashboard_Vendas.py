"""
Dashboard Comercial Tiny ERP - Versão Melhorada
Aplicação Streamlit com todas as melhorias técnicas implementadas
+ Funcionalidade de Mapa em Tela Cheia para Mobile
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

# ============================================================
# CONFIGURAÇÃO INICIAL
# ============================================================

st.set_page_config(
    page_title=Config.PAGE_TITLE,
    layout=Config.PAGE_LAYOUT,
    initial_sidebar_state=Config.SIDEBAR_STATE
)

# Aplicar CSS customizado
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
    }
    .stPlotlyChart {
        /* Remove altura fixa para permitir redimensionamento dinâmico */
        height: auto; 
    }
    .error-box {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 15px;
        border-radius: 4px;
    }
    .success-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 15px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CABEÇALHO COM LOGO (QUADRADO ARREDONDADO)
# ============================================================

col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    try:
        # Lê a imagem e transforma em texto (Base64)
        with open("logo.png", "rb") as f:
            data = f.read()
            encoded_image = base64.b64encode(data).decode()
        
        # Cria o HTML com fundo Branco e Cantos Arredondados
        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                background-color: #FFFFFF;
                padding: 10px;
                border-radius: 15px; 
                width: 140px;
                height: 140px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            ">
                <img src="data:image/png;base64,{encoded_image}" style="max-width: 90%; max-height: 90%;">
            </div>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.warning("Sem Logo")

with col_titulo:
    # Ajuste de margem para alinhar o texto com a caixa da logo
    st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
    st.title("Dashboard Comercial")
    st.markdown("Análise Geoespacial e Temporal de Vendas")

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

@st.cache_data(ttl=Config.CACHE_TTL, show_spinner=False)
def carregar_coordenadas_ibge():
    """
    Carrega coordenadas dos municípios brasileiros com cache.
    """
    try:
        logger.info("Carregando coordenadas do IBGE")
        df_mapa = IBGEClient.carregar_municipios()
        logger.info(f"Coordenadas carregadas: {len(df_mapa)} municípios")
        return df_mapa
    except Exception as e:
        logger.error(f"Erro ao carregar coordenadas: {e}")
        st.error(f"❌ Erro ao carregar dados do IBGE: {str(e)}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def buscar_vendas_tiny_paginado(token: str, data_ini: datetime, data_fim: datetime):
    """
    Busca vendas do Tiny ERP com tratamento robusto de erros.
    """
    try:
        # Validar período
        if not ValidationUtils.validar_periodo_datas(data_ini, data_fim):
            st.error("❌ Data inicial não pode ser maior que data final")
            return pd.DataFrame()
        
        # Criar cliente API
        client = TinyAPIClient(token)
        
        # Placeholders para progresso
        texto_status = st.empty()
        barra = st.progress(0)
        
        # Buscar vendas
        vendas_raw = client.buscar_vendas(data_ini, data_fim)
        
        # Processar vendas
        texto_status.text("Processando dados...")
        barra.progress(50)
        
        df_vendas = DataProcessor.processar_vendas_raw(vendas_raw)
        
        barra.progress(100)
        texto_status.text("✅ Dados carregados com sucesso!")
        time.sleep(1)
        
        barra.empty()
        texto_status.empty()
        
        logger.info(f"Vendas processadas: {len(df_vendas)} registros")
        return df_vendas
        
    except TinyAPIError as e:
        logger.error(f"Erro da API Tiny: {e}")
        st.error(f"❌ Erro na API Tiny: {str(e)}")
        return pd.DataFrame()
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        st.error(f"❌ Erro de validação: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar vendas")
        st.error(f"❌ Erro inesperado: {str(e)}")
        return pd.DataFrame()


# ============================================================
# INTERFACE - BARRA LATERAL
# ============================================================

st.sidebar.header("⚙️ Filtros")

# Obter token de forma segura
try:
    token = st.secrets["tiny_api_token"]
    st.sidebar.success("✅ Token carregado de secrets")
except KeyError:
    # Fallback caso não esteja no secrets.toml (ou para primeira execução)
    st.sidebar.warning("⚠️ Token não configurado em secrets")
    token = st.sidebar.text_input(
        "Token API Tiny",
        type="password",
        help="Cole seu token da API Tiny ERP aqui"
    )

# Filtros de data
d_ini = st.sidebar.date_input(
    "Data Inicial",
    Config.DATA_INICIO_PADRAO,
    format="DD/MM/YYYY"
)

d_fim = st.sidebar.date_input(
    "Data Final",
    Config.DATA_FIM_PADRAO,
    format="DD/MM/YYYY"
)

# Botão de atualização
btn_carregar = st.sidebar.button(
    "🔄 Atualizar Dashboard",
    type="primary",
    use_container_width=True
)

# ============================================================
# LÓGICA PRINCIPAL
# ============================================================

if btn_carregar:
    # Validar entrada
    if not token:
        st.error("❌ Por favor, insira o Token da API Tiny")
        logger.warning("Tentativa de carregamento sem token")
    else:
        with st.spinner("⏳ Processando dados..."):
            # Carregar dados
            df_mapa = carregar_coordenadas_ibge()
            df_vendas = buscar_vendas_tiny_paginado(token, d_ini, d_fim)
            
            # Verificar resultados
            if df_vendas.empty:
                st.warning("⚠️ Nenhuma venda encontrada para o período especificado")
                logger.info(f"Nenhuma venda encontrada: {d_ini} a {d_fim}")
            elif df_mapa.empty:
                st.error("❌ Erro ao carregar dados geográficos")
            else:
                try:
                    # Enriquecer dados com coordenadas
                    df_final = DataProcessor.enriquecer_com_coordenadas(df_vendas, df_mapa)
                    
                    if df_final.empty:
                        st.warning("⚠️ Nenhuma venda encontrada com coordenadas válidas")
                    else:
                        # Calcular KPIs
                        kpis = DataProcessor.calcular_kpis(df_final)
                        
                        # ============================================================
                        # EXIBIÇÃO - KPIs
                        # ============================================================
                        
                        st.markdown("---")
                        st.subheader("📊 Indicadores Principais")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        col1.metric(
                            "💰 Faturamento Total",
                            f"R$ {kpis['total_vendas']:,.2f}"
                        )
                        col2.metric(
                            "🎫 Ticket Médio",
                            f"R$ {kpis['ticket_medio']:,.2f}"
                        )
                        col3.metric(
                            "📄 Notas Emitidas",
                            f"{kpis['notas_emitidas']:,}"
                        )
                        col4.metric(
                            "🏙️ Cidades Atendidas",
                            f"{kpis['cidades_atendidas']}"
                        )
                        
                        # ============================================================
                        # EXIBIÇÃO - GRÁFICOS
                        # ============================================================
                        
                        # -------------------------------------------------------------
                        # MAPA DE BOLHAS COM BOTÃO DE TELA CHEIA (MODIFICAÇÃO AQUI)
                        # -------------------------------------------------------------
                        st.markdown("---")
                        
                        # Título e Botão na mesma linha
                        col_titulo_mapa, col_botao = st.columns([3, 1])
                        with col_titulo_mapa:
                            st.subheader("🗺️ Onde estamos vendendo? (Por Canal)")
                        with col_botao:
                            # Botão Toggle para Modo Tela Cheia
                            modo_tela_cheia = st.toggle("🔭 Ampliar Mapa", value=False)
                        
                        # Define altura dinâmica baseada no botão
                        # 900px cobre bem a tela de um celular moderno na vertical
                        altura_mapa = 900 if modo_tela_cheia else 600
                        zoom_inicial = 3.5 if modo_tela_cheia else 3.5
                        
                        # Agrupamento para o mapa INCLUINDO O CANAL
                        df_agrupado = df_final.groupby(
                            ['chave_cidade', 'Cidade_Original', 'Estado', 'latitude', 'longitude', 'Canal']
                        ).agg(
                            Valor=('Valor', 'sum'),
                            Qtd_Vendas=('Valor', 'count')
                        ).reset_index()
                        
                        # Definição das Cores Personalizadas
                        cores_canais = {
                            "Mercado Livre": "#FFE600",  # Amarelo ML
                            "Shopee": "#FF5722",         # Laranja Shopee
                            "Site": "#2E7D32",           # Verde (PlanteForte)
                            "Venda Direta": "#111111",   # Preto
                            "Outros": "#888888"          # Cinza
                        }

                        fig_mapa = px.scatter_mapbox(
                            df_agrupado,
                            lat="latitude",
                            lon="longitude",
                            size="Valor",
                            color="Canal",
                            color_discrete_map=cores_canais,
                            hover_name="Cidade_Original",
                            hover_data={
                                "Estado": True,
                                "Valor": ":.2f",
                                "Qtd_Vendas": True,
                                "latitude": False,
                                "longitude": False,
                                "Canal": True
                            },
                            size_max=40,
                            zoom=zoom_inicial,
                            center={"lat": -14.2, "lon": -51.9},
                            mapbox_style="carto-positron",
                        )
                        fig_mapa.update_traces(marker=dict(opacity=0.9, sizemin=5))
                        
                        # Aplica a altura dinâmica aqui
                        fig_mapa.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=altura_mapa)
                        
                        st.plotly_chart(fig_mapa, use_container_width=True)
                        
                        # Mensagem de ajuda se estiver ampliado
                        if modo_tela_cheia:
                            st.info("👆 Desative o botão 'Ampliar Mapa' para ver os outros gráficos abaixo.")

                        # -------------------------------------------------------------
                        # OUTROS GRÁFICOS (Só aparecem se não estiver ampliado)
                        # -------------------------------------------------------------
                        if not modo_tela_cheia:
                            st.markdown("---")
                            st.subheader("📈 Evolução das Vendas (Dia a Dia)")
                            
                            df_tempo = DataProcessor.agrupar_por_data(df_final)
                            
                            fig_tempo = px.line(
                                df_tempo,
                                x='Data_Obj',
                                y='Valor',
                                markers=True,
                                title="Tendência de Faturamento",
                                labels={'Data_Obj': 'Data', 'Valor': 'Faturamento (R$)'}
                            )
                            fig_tempo.update_traces(line_color='#17a2b8', line_width=3)
                            st.plotly_chart(fig_tempo, use_container_width=True)
                            
                            # Rankings
                            st.markdown("---")
                            col_rank_uf, col_rank_cidade = st.columns(2)
                            
                            with col_rank_uf:
                                st.subheader("🏆 Top 10 Estados")
                                df_uf = DataProcessor.agrupar_por_estado(df_final, top_n=10)
                                fig_uf = px.bar(
                                    df_uf,
                                    x='Estado',
                                    y='Valor',
                                    color='Valor',
                                    text_auto='.2s'
                                )
                                st.plotly_chart(fig_uf, use_container_width=True)
                            
                            with col_rank_cidade:
                                st.subheader("🏙️ Top 10 Cidades")
                                df_city = DataProcessor.agrupar_por_cidade(df_final, top_n=10)
                                fig_city = px.bar(
                                    df_city,
                                    x='Valor',
                                    y='Cidade_Original',
                                    orientation='h',
                                    text_auto='.2s'
                                )
                                fig_city.update_layout(yaxis={'categoryorder': 'total ascending'})
                                st.plotly_chart(fig_city, use_container_width=True)
                            
                            # Download de dados
                            st.markdown("---")
                            st.subheader("📂 Dados Detalhados")
                            
                            csv = df_final.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Baixar Dados em CSV",
                                data=csv,
                                file_name=f'vendas_tiny_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                                mime='text/csv',
                            )
                            
                            with st.expander("Ver Tabela Completa"):
                                st.dataframe(
                                    df_final,
                                    use_container_width=True,
                                    height=400
                                )
                        
                        logger.info("Dashboard exibido com sucesso")
                        
                except Exception as e:
                    logger.exception("Erro ao processar e exibir dados")
                    st.error(f"❌ Erro ao processar dados: {str(e)}")

# ============================================================
# RODAPÉ
# ============================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 12px;">
    Dashboard Comercial Tiny ERP
    <br>
    Desenvolvido com Streamlit, Pandas e Plotly
</div>
""", unsafe_allow_html=True)
