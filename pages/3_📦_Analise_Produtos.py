import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
from config import Config
from api_client import TinyAPIClient

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(page_title="Análise de Produtos", layout="wide", page_icon="📦")

st.title("📦 Análise de Produtos Vendidos")
st.markdown("Visão detalhada de volume (Sacos) e faturamento (Curva ABC).")

# ============================================================
# GERENCIAMENTO DE ESTADO (MEMÓRIA)
# ============================================================
# Aqui verificamos se já existe algo salvo na "mochila" do usuário
if 'analise_produtos_df' not in st.session_state:
    st.session_state['analise_produtos_df'] = None
if 'analise_produtos_meta' not in st.session_state:
    st.session_state['analise_produtos_meta'] = None

# ============================================================
# FILTROS LATERAIS
# ============================================================
st.sidebar.header("Filtros")

try:
    token = st.secrets["tiny_api_token"]
except KeyError:
    st.error("❌ Token não configurado no secrets.toml")
    st.stop()

# Recupera datas anteriores se existirem, senão usa padrão
data_ini = st.sidebar.date_input("Data Inicial", datetime(2024, 1, 1))
data_fim = st.sidebar.date_input("Data Final", datetime.now())

limite_notas = st.sidebar.slider(
    "Amostra de Notas", 
    min_value=10, 
    max_value=300, 
    value=50,
    help="Define quantas vendas recentes serão abertas para ler os itens."
)

col_btn1, col_btn2 = st.sidebar.columns(2)
btn_analisar = col_btn1.button("🔎 Analisar", type="primary")

# Botão para limpar a memória se o usuário quiser
if col_btn2.button("🗑️ Limpar"):
    st.session_state['analise_produtos_df'] = None
    st.rerun()

# ============================================================
# LÓGICA DE PROCESSAMENTO (SÓ RODA SE CLICAR NO BOTÃO)
# ============================================================
if btn_analisar:
    client = TinyAPIClient(token)
    
    # 1. Busca Cabeçalhos
    with st.spinner("Buscando lista de vendas..."):
        todas_vendas = client.buscar_vendas(data_ini, data_fim)
    
    if not todas_vendas:
        st.warning("Nenhuma venda encontrada no período.")
    else:
        # Filtra as últimas X notas
        vendas_analise = todas_vendas[-limite_notas:]
        qtd_analise = len(vendas_analise)
        
        st.info(f"Analisando itens das últimas {qtd_analise} vendas (de um total de {len(todas_vendas)})...")
        
        # Barra de Progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        lista_produtos = []
        
        # 2. Busca Itens de cada Nota
        for i, venda_wrapper in enumerate(vendas_analise):
            # Desembrulha (Nota Fiscal vs Wrapper direto)
            venda = venda_wrapper.get('nota_fiscal', venda_wrapper)
            id_nota = venda.get('id')
            numero = venda.get('numero')
            
            # Atualiza visual
            progress_bar.progress((i + 1) / qtd_analise)
            status_text.caption(f"Lendo Nota {numero}...")
            
            if id_nota:
                detalhes = client.obter_detalhes_nota(id_nota)
                
                # Procura itens (compatibilidade com versões diferentes da API)
                itens = []
                if 'itens' in detalhes:
                    itens = detalhes['itens']
                elif 'nota_fiscal' in detalhes and 'itens' in detalhes['nota_fiscal']:
                    itens = detalhes['nota_fiscal']['itens']
                
                for item_wrapper in itens:
                    item = item_wrapper.get('item', {})
                    
                    # Tratamento de dados
                    sku = item.get('codigo', 'SEM-COD')
                    nome = item.get('descricao', 'Produto Sem Nome')
                    qtd = float(item.get('quantidade', 0))
                    valor = float(item.get('valor_total', 0))
                    
                    lista_produtos.append({
                        'SKU': sku,
                        'Nome_Completo': f"{sku} - {nome}",
                        'Nome_Limpo': nome, 
                        'Qtd': qtd,
                        'Valor_Total': valor
                    })
            
            # Pausa para não bloquear API
            time.sleep(0.3)
            
        progress_bar.empty()
        status_text.empty()
        
        # 3. Agregação e Cálculos
        if lista_produtos:
            df = pd.DataFrame(lista_produtos)
            
            # Agrupa por Produto
            df_agrupado = df.groupby(['SKU', 'Nome_Completo', 'Nome_Limpo']).agg({
                'Qtd': 'sum',
                'Valor_Total': 'sum'
            }).reset_index()
            
            # --- CÁLCULO DA CURVA ABC ---
            # 1. Ordena por Valor
            df_abc = df_agrupado.sort_values('Valor_Total', ascending=False).copy()
            
            # 2. Calcula % acumulada
            total_faturamento = df_abc['Valor_Total'].sum()
            df_abc['% Acumulada'] = (df_abc['Valor_Total'] / total_faturamento).cumsum() * 100
            
            # 3. Classifica
            def classificar(perc):
                if perc <= 80: return 'A (Vital)'
                elif perc <= 95: return 'B (Importante)'
                else: return 'C (Complementar)'
            
            df_abc['Curva ABC'] = df_abc['% Acumulada'].apply(classificar)
            
            # SALVA NA MEMÓRIA DO STREAMLIT (SESSION STATE)
            st.session_state['analise_produtos_df'] = df_abc
            st.session_state['analise_produtos_meta'] = f"Análise gerada em {datetime.now().strftime('%H:%M')} com {qtd_analise} notas."
            
            st.rerun() # Recarrega a página para exibir os dados salvos
            
        else:
            st.error("A leitura das notas não retornou itens.")

# ============================================================
# EXIBIÇÃO DOS DADOS (SE HOUVER DADOS NA MEMÓRIA)
# ============================================================

if st.session_state['analise_produtos_df'] is not None:
    # Recupera os dados da memória
    df_abc = st.session_state['analise_produtos_df']
    msg_meta = st.session_state['analise_produtos_meta']
    
    st.success(f"✅ {msg_meta} (Dados salvos na memória)")
    
    total_faturamento = df_abc['Valor_Total'].sum()
    
    # Define cores fixas para o gráfico
    cores_abc = {
        'A (Vital)': '#2E7D32',      # Verde
        'B (Importante)': '#FBC02D', # Amarelo Ouro
        'C (Complementar)': '#C62828' # Vermelho
    }

    # Destaque do Campeão (Por Volume)
    campeao_qtd = df_abc.sort_values('Qtd', ascending=False).iloc[0]
    
    st.divider()
    
    # Card Nativo
    col_destaque, col_metricas = st.columns([2, 2])
    
    with col_destaque:
        st.subheader("🏆 Produto Campeão (Volume)")
        st.markdown(f"**{campeao_qtd['Nome_Limpo']}**")
        st.metric(
            label="Sacos Vendidos", 
            value=f"{campeao_qtd['Qtd']:,.0f}",
            delta="Líder de Vendas"
        )
    
    with col_metricas:
        st.metric("📦 Total de Sacos na Amostra", f"{df_abc['Qtd'].sum():,.0f}")
        st.metric("💰 Faturamento da Amostra", f"R$ {total_faturamento:,.2f}")

    st.divider()

    # ABAS
    tab_vol, tab_fin = st.tabs(["📦 Ranking por Volume (Sacos)", "💰 Curva ABC (Faturamento)"])
    
    with tab_vol:
        st.caption("Ordenado pela QUANTIDADE vendida. As cores indicam a importância financeira (ABC).")
        # Ordena por Quantidade
        df_vol = df_abc.sort_values('Qtd', ascending=False).head(15)
        
        fig_vol = px.bar(
            df_vol,
            x='Qtd',
            y='Nome_Limpo',
            orientation='h',
            color='Curva ABC',
            text_auto='.0f',
            color_discrete_map=cores_abc,
            title="Top 15 - Volume de Vendas",
            labels={'Qtd': 'Quantidade (Sacos)', 'Nome_Limpo': 'Produto'}
        )
        fig_vol.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
        st.plotly_chart(fig_vol, use_container_width=True)
        
    with tab_fin:
        st.caption("Ordenado pelo VALOR (R$). Curva ABC Clássica.")
        # Ordena por Valor
        df_fin = df_abc.sort_values('Valor_Total', ascending=False).head(15)
        
        fig_fin = px.bar(
            df_fin,
            x='Valor_Total',
            y='Nome_Limpo',
            orientation='h',
            color='Curva ABC',
            text_auto='.2s',
            color_discrete_map=cores_abc,
            title="Top 15 - Faturamento (Curva ABC)",
            labels={'Valor_Total': 'Faturamento (R$)', 'Nome_Limpo': 'Produto'}
        )
        fig_fin.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
        st.plotly_chart(fig_fin, use_container_width=True)

    # Tabela Detalhada
    with st.expander("📋 Ver Tabela Completa"):
        df_display = df_abc[['SKU', 'Nome_Limpo', 'Qtd', 'Valor_Total', 'Curva ABC']].copy()
        df_display.columns = ['SKU', 'Produto', 'Sacos', 'Faturamento', 'Classe']
        
        st.dataframe(
            df_display.style.format({
                'Sacos': '{:,.0f}',
                'Faturamento': 'R$ {:,.2f}'
            }),
            use_container_width=True
        )
elif not btn_analisar:
    st.info("👈 Ajuste os filtros na barra lateral e clique em 'Analisar' para carregar os dados.")
