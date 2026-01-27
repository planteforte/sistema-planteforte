import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from config import Config
from api_client import TinyAPIClient

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(page_title="Inteligência Sazonal", layout="wide", page_icon="📅")

st.title("📅 Inteligência Sazonal (O Calendário do Agro)")
st.markdown("Analise o comportamento histórico das vendas para prever a próxima safra.")

# ============================================================
# FUNÇÃO DE CORREÇÃO (O Segredo para não dar erro)
# ============================================================
def converter_valor_robusto(dado):
    """
    Tenta converter qualquer coisa que o Tiny mande (string com vírgula, ponto, etc)
    para um número real (float).
    """
    if dado is None:
        return 0.0
    
    # Se já for número, retorna
    if isinstance(dado, (int, float)):
        return float(dado)
    
    # Se for texto, limpa
    texto = str(dado).strip()
    if not texto:
        return 0.0
        
    try:
        # Troca vírgula por ponto (Padrão BR -> US)
        texto = texto.replace(',', '.')
        return float(texto)
    except ValueError:
        return 0.0

# ============================================================
# FILTROS
# ============================================================
st.sidebar.header("Configuração")

try:
    token = st.secrets["tiny_api_token"]
except:
    st.error("Token não configurado.")
    st.stop()

st.sidebar.info("Analisando histórico desde 2023 para identificar padrões.")
data_ini = date(2023, 1, 1)
data_fim = datetime.now().date()

btn_analisar = st.sidebar.button("🔄 Gerar Gráficos Sazonais", type="primary")

# ============================================================
# PROCESSAMENTO
# ============================================================
if btn_analisar:
    client = TinyAPIClient(token)
    
    with st.spinner("Buscando histórico de vendas de vários anos..."):
        vendas = client.buscar_vendas(data_ini, data_fim)
        
    if not vendas:
        st.warning("Nenhum dado encontrado.")
    else:
        # 1. Transformar em DataFrame
        dados_processados = []
        for v_wrap in vendas:
            v = v_wrap.get('nota_fiscal', v_wrap)
            data_emissao = v.get('data_emissao')
            
            # --- CORREÇÃO AQUI ---
            # O Tiny pode mandar 'valor_nota', 'valor' ou 'valor_total'
            raw_valor = v.get('valor_nota') or v.get('valor') or v.get('valor_total')
            valor = converter_valor_robusto(raw_valor)
                
            if data_emissao:
                dados_processados.append({
                    'Data': data_emissao,
                    'Valor': valor
                })
        
        df = pd.DataFrame(dados_processados)
        
        # Converter coluna de data
        df['Data_Obj'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        
        # Remover datas inválidas ou sem valor
        df = df[df['Data_Obj'].notna()]
        df = df[df['Valor'] > 0] # Remove notas zeradas/canceladas
        
        if df.empty:
            st.error("Encontramos as notas, mas os valores não puderam ser lidos. Verifique o formato no Tiny.")
            st.stop()

        # Criar colunas de tempo
        df['Ano'] = df['Data_Obj'].dt.year.astype(str) # Ano como texto para o gráfico agrupar cores
        df['Mes_Num'] = df['Data_Obj'].dt.month
        
        meses_pt = {
            1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 
            7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
        }
        df['Mes_Nome'] = df['Mes_Num'].map(meses_pt)
        
        # Agrupar dados por Ano e Mês
        df_agrupado = df.groupby(['Ano', 'Mes_Num', 'Mes_Nome'])['Valor'].sum().reset_index()
        
        # Ordenação cronológica para o gráfico
        df_agrupado = df_agrupado.sort_values(['Ano', 'Mes_Num'])

        # ============================================================
        # ANÁLISE E VISUALIZAÇÃO
        # ============================================================
        
        st.divider()
        
        # 1. IDENTIFICAR O MELHOR MÊS
        sazonalidade_geral = df.groupby('Mes_Nome')['Valor'].sum().reset_index()
        if not sazonalidade_geral.empty:
            melhor_mes = sazonalidade_geral.sort_values('Valor', ascending=False).iloc[0]
            nome_melhor_mes = melhor_mes['Mes_Nome']
        else:
            nome_melhor_mes = "N/A"
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🏆 Mês de Ouro", nome_melhor_mes)
        col2.metric("📅 Vendas Analisadas", len(df))
        col3.metric("💰 Faturamento Analisado", f"R$ {df['Valor'].sum():,.2f}")
        
        st.divider()

        # 2. GRÁFICO COMPARATIVO ANO x ANO
        st.subheader("📈 Comparativo de Safra (Ano a Ano)")
        st.markdown("Cada linha colorida representa um ano.")
        
        fig_linhas = px.line(
            df_agrupado,
            x='Mes_Nome',
            y='Valor',
            color='Ano', # Agora o Ano é texto, então gera cores discretas
            markers=True,
            title="Evolução Mensal das Vendas",
            labels={'Valor': 'Faturamento (R$)', 'Mes_Nome': 'Mês', 'Ano': 'Ano'},
            category_orders={"Mes_Nome": list(meses_pt.values())} # Força ordem Jan->Dez
        )
        fig_linhas.update_traces(line=dict(width=3))
        st.plotly_chart(fig_linhas, use_container_width=True)
        
        # 3. MAPA DE CALOR (HEATMAP)
        st.subheader("🔥 Mapa de Calor (Sazonalidade)")
        st.markdown("Descubra visualmente quando o dinheiro entra na conta.")
        
        # Pivot table
        heatmap_data = df_agrupado.pivot(index='Ano', columns='Mes_Nome', values='Valor')
        # Reordenar colunas e preencher vazios com 0
        heatmap_data = heatmap_data.reindex(columns=list(meses_pt.values())).fillna(0)
        
        fig_heat = px.imshow(
            heatmap_data,
            labels=dict(x="Mês", y="Ano", color="Faturamento"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            color_continuous_scale='RdYlGn', # Vermelho (Baixo) -> Verde (Alto)
            text_auto='.2s',
            aspect="auto"
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # 4. TABELA
        with st.expander("Ver Números Detalhados"):
            st.dataframe(
                heatmap_data.style.format("R$ {:,.2f}"), 
                use_container_width=True
            )

elif not btn_analisar:
    st.info("Clique em 'Gerar Gráficos Sazonais' para processar.")