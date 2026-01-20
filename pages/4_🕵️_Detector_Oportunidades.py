import streamlit as st
import pandas as pd
import time
from datetime import datetime, date
from config import Config
from api_client import TinyAPIClient
from data_processor import DataProcessor

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(page_title="Detector de Oportunidades", layout="wide", page_icon="🕵️")

st.title("🕵️ Detector de Oportunidades (Churn & Retenção)")
st.markdown("Identifique quem parou de comprar, quem é novo e a performance por canal.")

# ============================================================
# FILTROS LATERAIS
# ============================================================
st.sidebar.header("⚙️ Configuração da Análise")

try:
    token = st.secrets["tiny_api_token"]
except KeyError:
    st.error("❌ Token não configurado!")
    st.stop()

# Filtro de Canal
canais_disponiveis = ["Todos", "Venda Direta", "Mercado Livre", "Shopee", "Site"]
filtro_canal = st.sidebar.multiselect(
    "Filtrar por Canal de Origem", 
    options=canais_disponiveis[1:], 
    default=canais_disponiveis[1:], 
    help="Selecione quais canais deseja analisar."
)

st.sidebar.markdown("---")

st.sidebar.subheader("📅 Período 1 (Referência/Passado)")
data_ini_1 = st.sidebar.date_input("Início P1", date(2023, 1, 1))
data_fim_1 = st.sidebar.date_input("Fim P1", date(2023, 12, 31))

st.sidebar.markdown("---")

st.sidebar.subheader("📅 Período 2 (Atual/Comparação)")
data_ini_2 = st.sidebar.date_input("Início P2", date(2024, 1, 1))
data_fim_2 = st.sidebar.date_input("Fim P2", date(2024, 12, 31))

btn_comparar = st.sidebar.button("⚔️ Cruzar Dados", type="primary")

# ============================================================
# LÓGICA DE PROCESSAMENTO
# ============================================================
if btn_comparar:
    client = TinyAPIClient(token)
    
    # 1. Buscar Vendas
    with st.spinner("Buscando vendas e identificando canais..."):
        vendas_p1 = client.buscar_vendas(data_ini_1, data_fim_1)
        vendas_p2 = client.buscar_vendas(data_ini_2, data_fim_2)
        
    if not vendas_p1 and not vendas_p2:
        st.warning("Nenhum dado encontrado nos períodos selecionados.")
    else:
        
        # Função Auxiliar
        def processar_clientes(lista_vendas):
            clientes = {} 
            for v in lista_vendas:
                nota = v.get('nota_fiscal', v)
                cliente_node = nota.get('cliente', {})
                
                nome = nota.get('nome') or cliente_node.get('nome')
                valor = float(nota.get('valor_nota', 0))
                
                canal_identificado = DataProcessor.identificar_canal(nota)
                
                if nome:
                    nome = nome.strip().upper() 
                    
                    if nome not in clientes:
                        clientes[nome] = {
                            'total': 0.0, 
                            'pedidos': 0,
                            'canais': set()
                        }
                    
                    clientes[nome]['total'] += valor
                    clientes[nome]['pedidos'] += 1
                    clientes[nome]['canais'].add(canal_identificado)
            return clientes

        # Processa os dois períodos
        dict_p1 = processar_clientes(vendas_p1)
        dict_p2 = processar_clientes(vendas_p2)
        
        # Conjuntos de Nomes
        nomes_p1 = set(dict_p1.keys())
        nomes_p2 = set(dict_p2.keys())
        
        # Matemática de Conjuntos
        nomes_perdidos = nomes_p1 - nomes_p2
        nomes_novos = nomes_p2 - nomes_p1
        nomes_recorrentes = nomes_p1 & nomes_p2
        
        # --- FUNÇÃO DE TABELA (AJUSTADA: SEM VALORES PARA RECORRENTES) ---
        def criar_tabela(lista_nomes, dict_dados_principal, mostrar_valor=True):
            linhas = []
            
            for nome in lista_nomes:
                dados = dict_dados_principal[nome]
                
                # Filtro de Canal
                if not dados['canais'].intersection(set(filtro_canal)):
                    continue

                canais_str = ", ".join(list(dados['canais']))

                item = {
                    'Cliente': nome,
                    'Canal': canais_str,
                    'Pedidos (Frequência)': dados['pedidos']
                }
                
                if mostrar_valor:
                    item['Total Acumulado'] = dados['total']

                linhas.append(item)
            
            df = pd.DataFrame(linhas)
            if not df.empty and mostrar_valor:
                df = df.sort_values('Total Acumulado', ascending=False)
            elif not df.empty:
                df = df.sort_values('Pedidos (Frequência)', ascending=False)
                
            return df

        # Gera as tabelas
        # Para perdidos e novos, mantemos o valor (para saber quem priorizar)
        df_perdidos = criar_tabela(nomes_perdidos, dict_p1, mostrar_valor=True)
        df_novos = criar_tabela(nomes_novos, dict_p2, mostrar_valor=True)
        
        # Para recorrentes, REMOVEMOS o valor por enquanto, focando na fidelidade
        df_recorrentes = criar_tabela(nomes_recorrentes, dict_p2, mostrar_valor=False)

        # ============================================================
        # VISUALIZAÇÃO DOS RESULTADOS
        # ============================================================
        
        st.divider()
        
        # Cálculo da Taxa de Retenção
        total_base_p1 = len(nomes_p1)
        total_retidos = len(nomes_recorrentes)
        taxa_retencao = (total_retidos / total_base_p1 * 100) if total_base_p1 > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📊 Taxa de Retenção", f"{taxa_retencao:.1f}%", help="Clientes de P1 que compraram em P2")
        col2.metric("🔴 Clientes Perdidos", len(df_perdidos) if not df_perdidos.empty else 0)
        col3.metric("🟢 Novos Clientes", len(df_novos) if not df_novos.empty else 0)
        col4.metric("🔵 Clientes Fiéis", len(df_recorrentes) if not df_recorrentes.empty else 0)
        
        st.divider()
        
        tab_lost, tab_new, tab_loyal = st.tabs([
            "🔴 Clientes Perdidos (Recuperar)", 
            "🟢 Novos Clientes (Boas-vindas)",
            "🔵 Base Fiel (Manutenção)"
        ])
        
        with tab_lost:
            st.markdown(f"**Estes clientes compraram no Passado, mas sumiram no Presente.**")
            st.caption("Ordenado pelo maior valor de compra anterior (Prioridade de contato).")
            if not df_perdidos.empty:
                st.dataframe(
                    df_perdidos.style.format({'Total Acumulado': 'R$ {:,.2f}'}),
                    use_container_width=True,
                    height=500
                )
            else:
                st.success("Nenhum cliente perdido nos canais selecionados!")

        with tab_new:
            st.markdown("**Clientes que entraram agora na carteira.**")
            if not df_novos.empty:
                st.dataframe(
                    df_novos.style.format({'Total Acumulado': 'R$ {:,.2f}'}),
                    use_container_width=True,
                    height=500
                )
            else:
                st.info("Nenhum cliente novo nos canais selecionados.")

        with tab_loyal:
            st.markdown("**Clientes que compraram nos dois períodos (Retidos).**")
            st.caption("Ordenado pela frequência de compras.")
            if not df_recorrentes.empty:
                st.dataframe(
                    df_recorrentes, # Sem formatação de valor, pois removemos a coluna
                    use_container_width=True,
                    height=500
                )
            else:
                st.info("Nenhum cliente recorrente encontrado.")

elif not btn_comparar:
    st.info("👈 Configure as datas e os canais na barra lateral e clique em 'Cruzar Dados'.")