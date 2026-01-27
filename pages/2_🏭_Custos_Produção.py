import streamlit as st
import pandas as pd
from database import DatabaseManager
from datetime import datetime
from fpdf import FPDF
import tempfile

# ============================================================
# CONFIGURAÇÃO E BANCO
# ============================================================
st.set_page_config(page_title="Custos de Produção", layout="wide", page_icon="🏭")
db = DatabaseManager()
db.inicializar_banco()

st.title("🏭 Custos de Produção Industrial")
st.markdown("Cálculo de custo da batida e registro de lotes para precificação de venda.")

# Carregar Dados
df_insumos = db.listar_insumos()
df_especies = db.listar_especies()

def get_custo_insumo(nome):
    try:
        if df_insumos is not None and not df_insumos.empty:
            linha = df_insumos[df_insumos['nome'] == nome]
            if not linha.empty: return float(linha.iloc[0]['custo_unitario'])
    except: pass
    return 0.0

# ============================================================
# FUNÇÃO GERADORA DE PDF
# ============================================================
def gerar_pdf_custo(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="FICHA TÉCNICA DE PRODUÇÃO - PLANTE FORTE", ln=True, align='C')
    pdf.ln(10)
    
    # Dados Gerais
    pdf.set_font("Arial", size=12)
    pdf.cell(190, 8, txt=f"Produto: {dados['produto']}", ln=True)
    pdf.cell(190, 8, txt=f"Processo: {dados['processo']}", ln=True)
    pdf.cell(190, 8, txt=f"Lote: {dados['lote']} | Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(190, 8, txt=f"Volume Total Obtido: {dados['peso_total']:.2f} kg", ln=True)
    pdf.ln(5)
    
    # Tabela Batida
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="1. COMPOSIÇÃO DA MISTURA (BATIDA)", ln=True)
    pdf.set_font("Arial", size=10)
    
    # Cabeçalho Tabela
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(140, 8, "Componente (Peso Aplicado)", 1, 0, 'L', True)
    pdf.cell(50, 8, "Custo Total (R$)", 1, 1, 'C', True)
    
    # Itens
    pdf.set_font("Arial", size=10)
    for item in dados['itens_batida']:
        texto_item = item['nome']
        if item['peso'] > 0:
            texto_item += f" ({item['peso']:.2f} kg)"
            
        pdf.cell(140, 8, texto_item, 1)
        pdf.cell(50, 8, f"R$ {item['valor']:.2f}", 1, 1, 'R')
        
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(140, 8, "CUSTO MÉDIO POR KG BENEFICIADO:", 1, 0, 'R')
    pdf.cell(50, 8, f"R$ {dados['custo_kg']:.2f}", 1, 1, 'R')
    pdf.ln(10)
    
    # Embalagem
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt=f"2. PRODUTO ACABADO (SACO {dados['tamanho']} KG)", ln=True)
    pdf.set_font("Arial", size=10)
    
    pdf.cell(140, 8, f"Custo Semente ({dados['tamanho']}kg): R$ {dados['custo_base_saco']:.2f}", ln=True)
    pdf.cell(140, 8, f"Custo Embalagem/Extras: R$ {dados['custo_extras']:.2f}", ln=True)
    
    if dados['lista_extras']:
        pdf.ln(2)
        pdf.set_font("Arial", 'I', 9)
        pdf.multi_cell(190, 5, txt="Insumos adicionados: " + ", ".join(dados['lista_extras']))
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(34, 139, 34) # Verde
    pdf.cell(190, 10, txt=f"CUSTO FINAL DO PRODUTO: R$ {dados['custo_final']:.2f}", ln=True)
    
    # Salva em memória
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name

# ============================================================
# INTERFACE
# ============================================================
tab_fabrica, tab_config = st.tabs(["🧮 Calculadora e Embalagem", "⚙️ Tabela de Preços"])

with tab_fabrica:
    # SELETOR DE PROCESSO
    st.markdown("### Selecione o Tipo de Produção")
    tipo_processo = st.radio("", ["SEMENTE CONVENCIONAL", "SEMENTE INCRUSTADA GRAFITADA"], horizontal=True, label_visibility="collapsed")
    st.divider()

    col_esq, col_dir = st.columns([1, 1])
    
    # --- LADO ESQUERDO: INPUTS ---
    with col_esq:
        st.subheader("1. Parâmetros da Batida")
        
        col_lote, col_esp = st.columns([1, 2])
        lote_input = col_lote.text_input("Nº Lote (Obrigatório para Registrar)", placeholder="Ex: 2405-A")
        
        if df_especies is not None and not df_especies.empty:
            lista_especies = df_especies['nome'].tolist()
            especie_sel = col_esp.selectbox("Selecione a Semente:", lista_especies)
            
            # Dados Técnicos
            dados_especie = df_especies[df_especies['nome'] == especie_sel].iloc[0]
            familia = dados_especie['familia']
            custo_ponto = dados_especie['custo_ponto']
            
            st.info(f"🧬 Família: **{familia}** | 💲 Custo Ponto: **R$ {custo_ponto:.2f}**")
            st.markdown("---")
            
            # =========================================================
            # LÓGICA 1: CONVENCIONAL
            # =========================================================
            if tipo_processo == "SEMENTE CONVENCIONAL":
                c1, c2, c3 = st.columns(3)
                qtd_batida = c1.number_input("Qtd Batida (kg)", value=1000.0, step=50.0)
                pureza_ini = c2.number_input("Pureza Inicial (%)", value=62.0)
                pureza_des = c3.number_input("Pureza Desejada (%)", value=27.0)
                
                st.markdown("---")
                st.subheader("2. Composição")
                col_slid, col_chk = st.columns([2, 2])
                
                # Palha
                perc_palha = col_slid.slider("% Palha R (Enchimento)", 0, 100, 20)
                
                # Análise (Agora com valor editável)
                custo_analise_ref = get_custo_insumo("Analise Laboratorio")
                with col_chk:
                    usar_analise = st.checkbox("Incluir Análise?", value=True)
                    if usar_analise:
                        custo_extra_analise = st.number_input("Custo Análise (R$)", value=custo_analise_ref, step=10.0)
                    else:
                        custo_extra_analise = 0.0
                
                # CÁLCULOS
                if pureza_ini > 0:
                    pontos_utilizados = qtd_batida * pureza_des
                    kg_semente_pura = pontos_utilizados / pureza_ini
                    volume_enchimento = qtd_batida - kg_semente_pura
                else:
                    kg_semente_pura = 0; volume_enchimento = 0; pontos_utilizados = 0
                
                kg_palha = volume_enchimento * (perc_palha / 100)
                kg_granulado = volume_enchimento - kg_palha
                
                custo_total_semente = pontos_utilizados * custo_ponto
                
                nome_palha = "Palha Panicum" if familia == "Panicum" else "Palha Brachiaria"
                preco_palha = get_custo_insumo(nome_palha)
                custo_total_palha = kg_palha * preco_palha
                
                preco_granulado = get_custo_insumo("Granulado")
                custo_total_granulado = kg_granulado * preco_granulado
                
                peso_final_total = qtd_batida
                
                itens_batida_lista = [
                    {"nome": "Semente Pura", "peso": kg_semente_pura, "valor": custo_total_semente},
                    {"nome": nome_palha, "peso": kg_palha, "valor": custo_total_palha},
                    {"nome": "Granulado", "peso": kg_granulado, "valor": custo_total_granulado},
                ]
                
                opcoes_tamanho = [5, 20]

            # =========================================================
            # LÓGICA 2: INCRUSTADA GRAFITADA
            # =========================================================
            else:
                c1, c2, c3 = st.columns(3)
                qtd_semente_kg = c1.number_input("Qtd Sementes Base (kg)", value=338.0, step=1.0)
                pureza_ini = c2.number_input("Pureza Inicial (%)", value=90.0, step=1.0) 
                pureza_final = c3.number_input("Pureza Final (%)", value=90.0, step=1.0)
                
                st.markdown("---")
                st.subheader("2. Composição da Incrustação")
                
                ci1, ci2 = st.columns(2)
                qtd_seedgel = ci1.number_input("Qtd Seedgel (kg)", value=900.0, step=1.0)
                qtd_grafite = ci2.number_input("Qtd Grafite (kg)", value=13.5, step=0.1)
                
                # Análise (Agora com valor editável)
                custo_analise_ref = get_custo_insumo("Analise Laboratorio")
                st.markdown("---")
                ca1, ca2 = st.columns([1, 2])
                usar_analise = ca1.checkbox("Incluir Análise?", value=True)
                if usar_analise:
                    custo_extra_analise = ca2.number_input("Custo Análise (R$)", value=custo_analise_ref, step=10.0)
                else:
                    custo_extra_analise = 0.0

                # CÁLCULOS
                pontos_utilizados = qtd_semente_kg * pureza_final
                custo_total_semente = pontos_utilizados * custo_ponto
                
                preco_seedgel = get_custo_insumo("Seedgel")
                custo_total_seedgel = qtd_seedgel * preco_seedgel
                
                preco_grafite = get_custo_insumo("Grafite")
                custo_total_grafite = qtd_grafite * preco_grafite
                
                peso_final_total = qtd_semente_kg + qtd_seedgel + qtd_grafite
                
                itens_batida_lista = [
                    {"nome": "Semente Base", "peso": qtd_semente_kg, "valor": custo_total_semente},
                    {"nome": "Seedgel", "peso": qtd_seedgel, "valor": custo_total_seedgel},
                    {"nome": "Grafite", "peso": qtd_grafite, "valor": custo_total_grafite},
                ]
                
                opcoes_tamanho = [2, 10]

            # --- CUSTOS FINAIS COMUNS ---
            if usar_analise:
                itens_batida_lista.append({"nome": "Analise Lab", "peso": 0, "valor": custo_extra_analise})
            
            custo_total_batida = sum(item['valor'] for item in itens_batida_lista)
            custo_kg_final = custo_total_batida / peso_final_total if peso_final_total > 0 else 0
            
        else:
            st.warning("Cadastre as espécies na aba Configurações.")
            st.stop()

    # --- LADO DIREITO: RESULTADOS ---
    with col_dir:
        st.subheader("3. Resultado Industrial")
        
        st.markdown(f"""
        <div style="background-color: #1b5e20; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;">
            <h2 style="margin:0; color: #fff;">R$ {custo_kg_final:.2f} / kg</h2>
            <small>Custo Beneficiado ({tipo_processo})</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabela Dinâmica
        df_display = pd.DataFrame(itens_batida_lista)
        df_show = df_display.copy()
        df_show['peso'] = df_show['peso'].apply(lambda x: f"{x:.2f}" if x > 0 else "-")
        df_show['valor'] = df_show['valor'].apply(lambda x: f"R$ {x:,.2f}")
        df_show.columns = ["Item", "Peso (kg)", "Custo Total"]
        
        st.dataframe(df_show, use_container_width=True, hide_index=True)
        
        st.info(f"**Peso Total do Lote:** {peso_final_total:,.2f} kg | **Custo Total:** R$ {custo_total_batida:,.2f}")
        
        # --- BOTÃO DE REGISTRO DE LOTE ---
        st.markdown("### 💾 Oficializar Produção")
        if st.button("Registrar Lote de Produção", type="secondary", use_container_width=True, help="Salva este custo e quantidade no histórico de lotes para precificação de venda."):
            if not lote_input:
                st.error("⚠️ Digite o Número do Lote para salvar.")
            else:
                if db.registrar_lote_producao(lote_input, especie_sel, tipo_processo, peso_final_total, custo_total_batida, custo_kg_final):
                    st.success(f"✅ Lote **{lote_input}** registrado com sucesso! Custo: R$ {custo_kg_final:.2f}/kg.")
                    # Opcional: st.rerun() para limpar, mas pode ser ruim se quiser gerar PDF logo em seguida
                else:
                    st.error("Erro ao registrar no banco de dados.")

        st.divider()

        # =================================================================
        # 4. EMBALAGEM E FINALIZAÇÃO
        # =================================================================
        st.subheader("4. Embalagem (Produto Final)")
        
        tamanho_sc = st.radio("Tamanho:", opcoes_tamanho, horizontal=True, format_func=lambda x: f"{x} KG")
        
        st.markdown("**Selecione os Agregados:**")
        if df_insumos is not None:
            df_agregados = df_insumos[df_insumos['categoria'].isin(['Embalagem', 'Outros'])].copy()
            df_agregados['Selecionar'] = False
            df_agregados['Qtd'] = 1.0
            
            df_agregados.loc[df_agregados['nome'].str.contains('Linha', case=False), 'Qtd'] = 1.5
            
            nome_saco_provavel = f"Saco {tamanho_sc}kg"
            idx_saco = df_agregados.index[df_agregados['nome'] == nome_saco_provavel].tolist()
            if idx_saco:
                df_agregados.at[idx_saco[0], 'Selecionar'] = True

            edited_df = st.data_editor(
                df_agregados[['Selecionar', 'nome', 'custo_unitario', 'Qtd', 'unidade']],
                column_config={
                    "Selecionar": st.column_config.CheckboxColumn("Usar", default=False, width="small"),
                    "nome": st.column_config.TextColumn("Item", width="medium"),
                    "custo_unitario": st.column_config.NumberColumn("R$", format="%.2f", disabled=True),
                    "Qtd": st.column_config.NumberColumn("Qtd", min_value=0.01, step=0.1, format="%.2f"),
                    "unidade": st.column_config.TextColumn("Un", disabled=True, width="small"),
                },
                hide_index=True,
                use_container_width=True,
                key="editor_embalagem"
            )
            
            selecionados = edited_df[edited_df['Selecionar'] == True]
            custo_agregados = (selecionados['custo_unitario'] * selecionados['Qtd']).sum()
            
            custo_produto_base = custo_kg_final * tamanho_sc
            custo_final_produto = custo_produto_base + custo_agregados
            
            st.markdown(f"""
            <div style="background-color: #2e7d32; color: white; padding: 15px; border-radius: 8px; text-align: center; margin-top: 10px;">
                <small>Custo Final Saco {tamanho_sc}kg</small>
                <h1 style="margin:0; color: #fff;">R$ {custo_final_produto:.2f}</h1>
            </div>
            """, unsafe_allow_html=True)
            
            # --- ÁREA DO PDF ---
            st.markdown("### 📄 Relatório")
            
            dados_pdf = {
                "produto": especie_sel,
                "processo": tipo_processo,
                "lote": lote_input if lote_input else "N/A",
                "peso_total": peso_final_total,
                "qtd_batida": peso_final_total,
                "custo_kg": custo_kg_final,
                "itens_batida": itens_batida_lista,
                "tamanho": tamanho_sc,
                "custo_base_saco": custo_produto_base,
                "custo_extras": custo_agregados,
                "lista_extras": selecionados['nome'].tolist(),
                "custo_final": custo_final_produto
            }
            
            if st.button("🖨️ Gerar Ficha Técnica (PDF)", type="primary", use_container_width=True):
                try:
                    pdf_path = gerar_pdf_custo(dados_pdf)
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Baixar PDF Agora",
                            data=f,
                            file_name=f"Ficha_{especie_sel}_{tipo_processo[:4]}_{tamanho_sc}kg.pdf",
                            mime="application/pdf",
                            key="dl_pdf"
                        )
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}. Verifique se instalou 'fpdf' (pip install fpdf).")

# ------------------------------------------------------------------------------
# ABA 2: CONFIGURAÇÕES (GERENCIAMENTO DE INSUMOS)
# ------------------------------------------------------------------------------
with tab_config:
    st.subheader("Gestão de Preços e Insumos")
    st.info("Aqui você pode editar preços, criar novos insumos e excluir itens obsoletos.")
    
    col_ins, col_esp = st.columns([2, 1])
    
    # 1. TABELA DE INSUMOS (EDITÁVEL)
    with col_ins:
        st.markdown("**Insumos & Embalagens**")
        if df_insumos is not None:
            
            # Cria tabela editável
            df_edit = df_insumos[['id', 'nome', 'custo_unitario', 'unidade', 'categoria']].copy()
            df_edit['Excluir'] = False # Checkbox de exclusão
            
            edited_insumos = st.data_editor(
                df_edit,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                    "nome": st.column_config.TextColumn("Nome do Insumo"),
                    "custo_unitario": st.column_config.NumberColumn("Custo (R$)", format="%.2f", min_value=0.0),
                    "unidade": st.column_config.TextColumn("Unid.", width="small"),
                    "categoria": st.column_config.SelectboxColumn("Categoria", options=["Materia Prima", "Embalagem", "Servico", "Outros"]),
                    "Excluir": st.column_config.CheckboxColumn("Apagar?", width="small")
                },
                hide_index=True,
                use_container_width=True,
                key="editor_insumos"
            )
            
            # LÓGICA DE ATUALIZAÇÃO (SALVAR EDIÇÕES)
            if st.button("💾 Salvar Alterações e Exclusões", type="primary"):
                changes_count = 0
                
                # 1. Detectar Exclusões
                excluir_ids = edited_insumos[edited_insumos['Excluir'] == True]['id'].tolist()
                for eid in excluir_ids:
                    db.excluir_insumo(eid)
                    changes_count += 1
                
                # 2. Detectar Edições (Preço/Nome)
                # Comparamos o DF editado com o original
                for index, row in edited_insumos.iterrows():
                    original = df_insumos[df_insumos['id'] == row['id']].iloc[0]
                    
                    if row['custo_unitario'] != original['custo_unitario']:
                        db.atualizar_insumo(row['id'], 'custo_unitario', row['custo_unitario'])
                        changes_count += 1
                    
                    if row['nome'] != original['nome']:
                        db.atualizar_insumo(row['id'], 'nome', row['nome'])
                        changes_count += 1

                if changes_count > 0:
                    st.success(f"{changes_count} alterações realizadas!")
                    st.rerun()
                else:
                    st.info("Nenhuma alteração detectada.")
            
            st.divider()
            
            # 2. FORMULÁRIO DE ADIÇÃO (NOVO INSUMO)
            with st.expander("➕ Cadastrar Novo Insumo"):
                with st.form("form_add_insumo"):
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 3])
                    novo_nome = c1.text_input("Nome", placeholder="Ex: Saco 2kg Promoção")
                    novo_custo = c2.number_input("Custo (R$)", min_value=0.0, step=0.01)
                    nova_und = c3.text_input("Unidade", placeholder="un, kg, m")
                    nova_cat = c4.selectbox("Categoria", ["Embalagem", "Materia Prima", "Outros", "Servico"])
                    
                    if st.form_submit_button("Adicionar"):
                        if novo_nome and nova_und:
                            db.adicionar_insumo(novo_nome, nova_und, novo_custo, nova_cat)
                            st.success(f"{novo_nome} adicionado!")
                            st.rerun()
                        else:
                            st.error("Preencha o nome e a unidade.")

    # 2. TABELA DE ESPÉCIES (AGORA EDITÁVEL)
    with col_esp:
        st.markdown("**Sementes (Custo Ponto)**")
        if df_especies is not None:
            
            df_esp_edit = df_especies[['id', 'nome', 'familia', 'custo_ponto', 'custo_kg_projetado']].copy()
            
            edited_especies = st.data_editor(
                df_esp_edit,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                    "nome": st.column_config.TextColumn("Espécie", disabled=True), 
                    "familia": st.column_config.TextColumn("Família", disabled=True),
                    "custo_ponto": st.column_config.NumberColumn("Custo Ponto (R$)", format="%.4f", min_value=0.0, step=0.01),
                    "custo_kg_projetado": st.column_config.NumberColumn("Último Custo Ind. (R$)", format="%.2f", disabled=True)
                },
                hide_index=True,
                use_container_width=True,
                key="editor_especies"
            )

            if st.button("💾 Salvar Custos de Ponto", type="primary"):
                changes_count = 0
                for index, row in edited_especies.iterrows():
                    original = df_especies[df_especies['id'] == row['id']].iloc[0]
                    if row['custo_ponto'] != original['custo_ponto']:
                        db.atualizar_especie_campo(row['id'], 'custo_ponto', row['custo_ponto'])
                        changes_count += 1
                
                if changes_count > 0:
                    st.success(f"{changes_count} custos de ponto atualizados!")
                    st.rerun()
                else:
                    st.info("Nenhuma alteração no custo do ponto.")