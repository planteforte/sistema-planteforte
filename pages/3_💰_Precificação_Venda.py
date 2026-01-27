import streamlit as st
import pandas as pd
from database import DatabaseManager

# ============================================================
# CONFIGURAÇÃO
# ============================================================
st.set_page_config(page_title="Precificação de Venda", layout="wide", page_icon="💰")
db = DatabaseManager()
db.inicializar_banco()

st.title("💰 Precificação Comercial & Margens")
st.markdown("Definição de preço de venda (SKU) para todos os canais.")

# ============================================================
# 1. CARREGAR DADOS (MOTOR)
# ============================================================
df_insumos = db.listar_insumos()
df_lotes = db.listar_lotes_disponiveis()
df_padrao = db.listar_produtos_padrao()

# ============================================================
# 2. SELETOR DE ORIGEM (FÁBRICA VS TABELA)
# ============================================================
st.sidebar.header("1. Origem do Produto")
origem_custo = st.sidebar.radio("Base de Custo:", ["Tabela Projetada (Padrão)", "Lote Produzido (Fábrica)"])

custo_final_saco = 0.0
nome_produto_final = ""

# --- CENÁRIO A: TABELA PROJETADA (LISTA PRONTA) ---
if origem_custo == "Tabela Projetada (Padrão)":
    if df_padrao is not None and not df_padrao.empty:
        opcoes_padrao = df_padrao.apply(lambda x: f"{x['sku']} - {x['nome']} ({x['descricao']})", axis=1)
        item_selecionado = st.sidebar.selectbox("Selecione o Produto:", options=opcoes_padrao)
        
        idx = opcoes_padrao[opcoes_padrao == item_selecionado].index[0]
        dados_prod = df_padrao.iloc[idx]
        
        custo_final_saco = dados_prod['custo_padrao']
        nome_produto_final = f"{dados_prod['nome']} - {dados_prod['descricao']}"
        
        st.sidebar.info(f"📦 Custo fixo da tabela: **R$ {custo_final_saco:.2f}**")
    else:
        st.warning("Tabela de produtos padrão vazia.")
        st.stop()

# --- CENÁRIO B: LOTE DE FÁBRICA (MONTADORA) ---
else:
    if df_lotes is not None and not df_lotes.empty:
        opcoes_lotes = df_lotes.apply(lambda x: f"{x['codigo_lote']} - {x['produto_nome']} (R$ {x['custo_kg_final']:.2f}/kg)", axis=1)
        lote_selecionado_str = st.sidebar.selectbox("Selecione o Lote:", options=opcoes_lotes)

        idx_lote = opcoes_lotes[opcoes_lotes == lote_selecionado_str].index[0]
        dados_lote = df_lotes.iloc[idx_lote]
        custo_kg_semente = dados_lote['custo_kg_final']

        st.sidebar.markdown("---")
        tamanho_saco = st.sidebar.radio("Embalagem:", [5, 10, 20], horizontal=True, format_func=lambda x: f"{x} kg")
        
        custo_saco_estimado = 0.0
        if df_insumos is not None:
            try:
                row_saco = df_insumos[df_insumos['nome'].str.contains(f"Saco {tamanho_saco}kg", case=False)]
                if not row_saco.empty: custo_saco_estimado = float(row_saco.iloc[0]['custo_unitario'])
            except: pass

        c_emb = st.sidebar.number_input(f"Custo Saco (R$)", value=custo_saco_estimado, step=0.10)
        c_ext = st.sidebar.number_input("Outros (R$)", value=0.20, step=0.05)

        custo_final_saco = (custo_kg_semente * tamanho_saco) + c_emb + c_ext
        nome_produto_final = f"{dados_lote['produto_nome']} (Lote {dados_lote['codigo_lote']}) - {tamanho_saco}kg"
    else:
        st.warning("Nenhum lote produzido encontrado.")
        st.stop()

# === MOSTRADOR DE CUSTO BASE (C4) ===
st.markdown(f"""
<div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #2196f3; margin-bottom: 20px;">
    <h3 style="margin:0; color: #0d47a1;">{nome_produto_final}</h3>
    <span style="font-size: 1.2em;">Custo Base (B4/C4): <b>R$ {custo_final_saco:.2f}</b></span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 3. SIMULADOR DE CANAIS DE VENDA
# ============================================================
st.subheader("2. Simulador de Preços por Canal")

# Layout 2x2: Linha 1 (ML e Shopee), Linha 2 (Site e Venda Direta)
row1_col1, row1_col2 = st.columns(2)
st.markdown("---")
row2_col1, row2_col2 = st.columns(2)

# ============================================================
# CANAL 1: MERCADO LIVRE (Fórmula Validada)
# ============================================================
with row1_col1:
    st.markdown("### 🟡 Mercado Livre")
    with st.container(border=True):
        # Inputs O4, P4, Q4, R4, S4
        c1, c2 = st.columns(2)
        ml_margem = c1.number_input("Margem (O4) %", value=30.0, step=1.0, key="ml_m")
        ml_imposto = c2.number_input("Imposto (P4) %", value=5.2, step=0.1, key="ml_i")
        c3, c4 = st.columns(2)
        ml_comissao = c3.number_input("Comissão (Q4) %", value=16.5, step=0.5, key="ml_c")
        ml_antecipacao = c4.number_input("Antecipação (R4) %", value=3.5, step=0.1, key="ml_a")
        ml_frete = st.number_input("Custo Frete (S4) R$", value=22.45, step=0.50, key="ml_fr")

        # Lógica: (B4+6)/(1-...) ou (B4+S4)/(1-...) se >= 79
        divisor_ml = 1 - ((ml_comissao + ml_imposto + ml_margem + ml_antecipacao) / 100)
        
        if divisor_ml > 0:
            taxa_fixa_ml = 6.00
            preco_teste = (custo_final_saco + taxa_fixa_ml) / divisor_ml
            
            if preco_teste >= 79.00:
                pv_ml = (custo_final_saco + ml_frete) / divisor_ml
                msg_ml = "Preço >= 79 (Considera Frete S4)"
            else:
                pv_ml = preco_teste
                msg_ml = "Preço < 79 (Considera Taxa Fixa R$ 6)"
                
            st.divider()
            st.markdown(f"""<div style="text-align: center;"><h2 style="color: #fdd835; margin:0;">R$ {pv_ml:.2f}</h2><small>{msg_ml}</small></div>""", unsafe_allow_html=True)
        else:
            st.error("Taxas ML > 100%")

# ============================================================
# CANAL 2: SHOPEE (Fórmula Validada)
# ============================================================
with row1_col2:
    st.markdown("### 🟠 Shopee")
    with st.container(border=True):
        # Inputs V4, W4, X4, Y4, Z4
        c1, c2 = st.columns(2)
        sh_margem = c1.number_input("Margem (V4) %", value=21.0, step=1.0, key="sh_m")
        sh_aliquota = c2.number_input("Alíquota (W4) %", value=20.0, step=0.5, key="sh_a")
        c3, c4 = st.columns(2)
        sh_imposto = c3.number_input("Imp. Fiscal (Y4) %", value=6.0, step=0.5, key="sh_i")
        sh_antecipacao = c4.number_input("Antecipação (Z4) %", value=3.5, step=0.1, key="sh_ant")
        sh_fixa = st.number_input("Taxa Fixa (X4) R$", value=4.00, step=0.50, key="sh_f")

        # Lógica: (C4 + X4) / (1 - W4 - Y4 - V4 - Z4)
        divisor_sh = 1 - ((sh_aliquota + sh_imposto + sh_margem + sh_antecipacao) / 100)
        
        if divisor_sh > 0:
            pv_sh = (custo_final_saco + sh_fixa) / divisor_sh
            st.divider()
            st.markdown(f"""<div style="text-align: center;"><h2 style="color: #e65100; margin:0;">R$ {pv_sh:.2f}</h2><small>Markup Shopee</small></div>""", unsafe_allow_html=True)
        else:
            st.error("Taxas Shopee > 100%")

# ============================================================
# CANAL 3: SITE (Fórmula Validada)
# ============================================================
with row2_col1:
    st.markdown("### 🟢 Site Próprio")
    with st.container(border=True):
        # Inputs D4, E4, F4, I4, H4
        c1, c2 = st.columns(2)
        si_margem = c1.number_input("Margem (I4) %", value=20.0, step=1.0, key="si_m")
        si_imposto = c2.number_input("Imposto (D4) %", value=5.7, step=0.1, key="si_i")
        c3, c4 = st.columns(2)
        si_comissao = c3.number_input("Comissão (E4) %", value=2.0, step=0.1, key="si_c")
        si_outras = c4.number_input("Outros (F4) %", value=12.0, step=0.5, key="si_o")
        si_frete = st.number_input("Frete (H4) R$", value=80.00, step=1.0, key="si_f")

        # Lógica: (C4 + H4) / (1 - I4 - D4 - E4 - F4)
        divisor_si = 1 - ((si_margem + si_imposto + si_comissao + si_outras) / 100)
        
        if divisor_si > 0:
            pv_si = (custo_final_saco + si_frete) / divisor_si
            st.divider()
            st.markdown(f"""<div style="text-align: center;"><h2 style="color: #2e7d32; margin:0;">R$ {pv_si:.2f}</h2><small>Markup Site</small></div>""", unsafe_allow_html=True)
        else:
            st.error("Taxas Site > 100%")

# ============================================================
# CANAL 4: VENDA DIRETA (NOVO - Lógica Aplicada)
# ============================================================
with row2_col2:
    st.markdown("### ⚫ Venda Direta / Balcão")
    with st.container(border=True):
        # Inputs B4, D4, E4, F4, G4
        c1, c2 = st.columns(2)
        vd_margem = c1.number_input("Margem (B4) %", value=30.0, step=1.0, key="vd_m")
        vd_imposto = c2.number_input("Imposto (D4) %", value=5.7, step=0.1, key="vd_i")
        c3, c4 = st.columns(2)
        vd_comissao = c3.number_input("Comissão (E4) %", value=10.0, step=0.5, key="vd_c")
        vd_outras = c4.number_input("Taxas/Cartão (F4) %", value=5.0, step=0.5, key="vd_o")
        vd_frete = st.number_input("Frete (G4) R$", value=50.00, step=1.0, key="vd_f")

        # Lógica FOB (H4): C4 / (1 - B4 - D4 - E4 - F4)
        # Lógica CIF (I4): (C4 + G4) / (1 - B4 - D4 - E4 - F4)
        
        divisor_vd = 1 - ((vd_margem + vd_imposto + vd_comissao + vd_outras) / 100)
        
        if divisor_vd > 0:
            pv_fob = custo_final_saco / divisor_vd
            pv_cif = (custo_final_saco + vd_frete) / divisor_vd
            
            st.divider()
            col_fob, col_cif = st.columns(2)
            
            with col_fob:
                st.markdown(f"""
                <div style="text-align: center; border-right: 1px solid #ddd;">
                    <span style="color: #666; font-size: 0.9em;">Preço FOB (H4)</span>
                    <h2 style="color: #333; margin:0;">R$ {pv_fob:.2f}</h2>
                    <small>Cliente Retira</small>
                </div>
                """, unsafe_allow_html=True)
                
            with col_cif:
                st.markdown(f"""
                <div style="text-align: center;">
                    <span style="color: #666; font-size: 0.9em;">Preço CIF (I4)</span>
                    <h2 style="color: #333; margin:0;">R$ {pv_cif:.2f}</h2>
                    <small>Entrega Inclusa</small>
                </div>
                """, unsafe_allow_html=True)
                
        else:
            st.error("Taxas Venda Direta > 100%")