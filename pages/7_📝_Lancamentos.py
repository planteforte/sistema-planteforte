import streamlit as st
import pandas as pd
from datetime import date
from database import DatabaseManager

# Configuração
st.set_page_config(page_title="Lançamentos Financeiros", layout="wide", page_icon="📝")
st.title("📝 Central de Lançamentos")

# Conexão
db = DatabaseManager()
db.inicializar_banco()

# Abas
tab_lancamento, tab_cadastro, tab_extrato = st.tabs([
    "💸 Novo Lançamento", 
    "👥 Cadastro de Parceiros", 
    "📋 Extrato & Gestão"
])

# ------------------------------------------------------------------------------
# ABA 1: NOVO LANÇAMENTO
# ------------------------------------------------------------------------------
with tab_lancamento:
    st.subheader("Registrar Movimentação")
    
    # Carregar listas
    conn = db._get_connection()
    df_cats = pd.read_sql_query("SELECT codigo, descricao, tipo FROM categorias ORDER BY descricao", conn)
    conn.close()
    
    lista_categorias = df_cats.apply(lambda x: f"{x['codigo']} - {x['descricao']} ({x['tipo']})", axis=1).tolist()
    
    df_clis = db.listar_clientes()
    lista_clientes = {}
    if df_clis is not None and not df_clis.empty:
        lista_clientes = dict(zip(df_clis['nome'], df_clis['id']))
        opcoes_clientes = list(lista_clientes.keys())
    else:
        opcoes_clientes = ["Sem cadastro"]

    # Formulário
    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            data_mov = st.date_input("Data", date.today())
            tipo_mov = st.selectbox("Tipo", ["Saída (Pagamento)", "Entrada (Recebimento)"])
        with col2:
            valor = st.number_input("Valor (R$)", min_value=0.01, step=10.00, format="%.2f")
            status = st.selectbox("Status", ["Pago", "Pendente"])
        with col3:
            categoria_sel = st.selectbox("Categoria", lista_categorias)
            cliente_sel = st.selectbox("Interessado", opcoes_clientes)
        
        descricao = st.text_input("Descrição", placeholder="Ex: Conta de Luz ref. Janeiro")
        
        if st.form_submit_button("💾 Salvar Lançamento", type="primary"):
            cat_codigo = categoria_sel.split(" - ")[0]
            cli_id = lista_clientes.get(cliente_sel, None)
            status_db = "Pago" if "Pago" in status else "Pendente"
            tipo_db = "Saída" if "Saída" in tipo_mov else "Entrada"
            
            if db.adicionar_lancamento(data_mov, valor, descricao, cat_codigo, cli_id, tipo_db, status_db):
                st.success("✅ Lançamento registrado!")
                st.rerun()
            else:
                st.error("Erro ao salvar.")

# ------------------------------------------------------------------------------
# ABA 2: CADASTRO DE PARCEIROS
# ------------------------------------------------------------------------------
with tab_cadastro:
    st.subheader("Novo Parceiro")
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        with st.form("form_cliente", clear_on_submit=True):
            nome = st.text_input("Nome *")
            doc = st.text_input("CPF/CNPJ")
            fone = st.text_input("Telefone")
            cidade_uf = st.text_input("Cidade-UF", placeholder="Ex: Auriflama-SP")
            tipo_parceiro = st.radio("Tipo:", ["Cliente", "Fornecedor"], horizontal=True)
            
            if st.form_submit_button("💾 Cadastrar"):
                if nome:
                    # Separa Cidade e UF
                    cidade_real = cidade_uf
                    uf_real = ""
                    if "-" in cidade_uf:
                        partes = cidade_uf.split("-")
                        if len(partes) >= 2:
                            cidade_real = partes[0].strip()
                            uf_real = partes[1].strip().upper()
                            
                    if db.adicionar_cliente(nome, doc, fone, cidade_real, uf_real, tipo_parceiro):
                        st.success(f"**{nome}** cadastrado!")
                        st.rerun()
                    else:
                        st.error("Erro no banco.")
                else:
                    st.warning("Nome obrigatório.")

    with col_b:
        if df_clis is not None and not df_clis.empty:
            st.dataframe(df_clis[['nome', 'telefone', 'cidade', 'tipo']], use_container_width=True, hide_index=True)

# ------------------------------------------------------------------------------
# ABA 3: EXTRATO COM EXCLUSÃO (A Mágica Acontece Aqui)
# ------------------------------------------------------------------------------
with tab_extrato:
    st.subheader("Gerenciar Lançamentos")
    
    df = db.buscar_lancamentos()
    
    if df is not None and not df.empty:
        # Cabeçalho da Tabela Manual
        cols = st.columns([1, 2, 2, 3, 2, 1])
        cols[0].markdown("**Data**")
        cols[1].markdown("**Tipo**")
        cols[2].markdown("**Valor**")
        cols[3].markdown("**Descrição**")
        cols[4].markdown("**Status**")
        cols[5].markdown("**Ação**")
        
        st.divider()
        
        # Loop para criar linhas com botão
        for index, row in df.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([1, 2, 2, 3, 2, 1])
            
            c1.text(pd.to_datetime(row['data']).strftime('%d/%m'))
            
            # Corzinha no tipo
            if row['tipo_movimento'] == 'Entrada':
                c2.markdown("🟢 Entrada")
            else:
                c2.markdown("🔴 Saída")
                
            c3.text(f"R$ {row['valor']:,.2f}")
            c4.text(row['descricao'])
            c5.text(row['status'])
            
            # Botão de Excluir com Chave Única (Key)
            if c6.button("🗑️", key=f"btn_del_{row['id']}", help="Excluir este lançamento"):
                if db.excluir_lancamento(row['id']):
                    st.success("Item excluído!")
                    st.rerun()
                else:
                    st.error("Erro ao excluir.")
            
            st.markdown("<hr style='margin: 5px 0'>", unsafe_allow_html=True)
            
    else:
        st.info("Nenhum lançamento para exibir.")