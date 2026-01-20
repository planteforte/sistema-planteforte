import streamlit as st
import streamlit.components.v1 as components

# Configuração da página para ocupar a tela toda
st.set_page_config(page_title="Calculadora de Precificação", layout="wide", page_icon="💰")

# Aqui colocamos o seu código HTML original com as Novas Funcionalidades (PDF e Carregar)
html_codigo = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sementes Planteforte - Sistema</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    
    <style>
        /* --- ESTILO GERAL E TIPOGRAFIA --- */
        body {
            font-family: 'Segoe UI', 'Roboto', Helvetica, Arial, sans-serif;
            background-color: #ffffff;
            margin: 0;
            padding: 10px;
            color: #333;
        }

        .main-container {
            max-width: 100%;
            margin: 0 auto;
        }

        /* --- CABEÇALHO COM LOGO --- */
        .header {
            text-align: center;
            margin-bottom: 30px;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            border-bottom: 4px solid #2e7d32;
        }
        
        .logo-area {
            max-height: 80px;
            margin-bottom: 10px;
        }
        
        h1 { margin: 0; color: #1b5e20; font-size: 1.8em; text-transform: uppercase; letter-spacing: 1px;}
        p.subtitle { color: #7f8c8d; margin-top: 5px; font-weight: 500;}

        /* --- CARTÃO PRINCIPAL DA CALCULADORA --- */
        .card {
            background: white;
            padding: 35px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 30px;
            border-top: 6px solid #27ae60; /* Verde Agro */
        }

        h2 { color: #27ae60; margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }

        /* --- INPUTS E LABELS --- */
        label {
            display: block;
            margin-top: 15px;
            font-weight: 600;
            font-size: 0.95em;
            color: #444;
        }

        input {
            width: 100%;
            padding: 10px 12px;
            margin-top: 5px;
            border: 1px solid #ccc;
            border-radius: 6px;
            box-sizing: border-box;
            font-size: 1em;
            transition: border 0.3s;
        }

        input:focus { border-color: #27ae60; outline: none; background-color: #f9fff9; }

        /* --- BOTÕES --- */
        .btn {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: 0.3s;
            margin-top: 25px;
        }

        .btn-green { background-color: #27ae60; color: white; }
        .btn-green:hover { background-color: #219150; }

        .btn-blue { background-color: #2980b9; color: white; margin-top: 5px; padding: 10px; font-size: 0.9em; text-transform: none; width: auto; display: inline-block;}
        .btn-blue:hover { background-color: #21618c; }

        .btn-outline { background: transparent; border: 2px solid #27ae60; color: #27ae60; margin-top: 10px;}
        .btn-outline:hover { background: #eafaf1; }

        .btn-red { background-color: #c0392b; color: white; margin-top: 10px; }
        .btn-red:hover { background-color: #a93226; }
        
        .btn-gray { background-color: #7f8c8d; color: white; }
        .btn-gray:hover { background-color: #626d6e; }

        /* --- SEÇÃO DE CLIENTE --- */
        .client-section {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border: 1px dashed #bdc3c7;
            margin-bottom: 20px;
        }
        .row { display: flex; gap: 15px; flex-wrap: wrap; }
        .col { flex: 1; min-width: 150px; }

        /* --- RESULTADOS --- */
        .resultado-box {
            margin-top: 30px;
            padding: 20px;
            background-color: #e8f5e9;
            border: 1px solid #c8e6c9;
            border-radius: 8px;
            text-align: center;
        }
        .valor-destaque { font-size: 2em; color: #2e7d32; font-weight: bold; display: block; margin: 10px 0;}

        /* --- TABELA DE HISTÓRICO --- */
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9em; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; color: #333; }
        tr:hover { background-color: #f5f5f5; }
        
        .btn-action { 
            cursor: pointer; font-weight: bold; border: none; background: none; margin: 0 5px; font-size: 1.1em;
        }
        .btn-delete { color: #c0392b; }
        .btn-load { color: #2980b9; }

        /* --- MODAL (JANELA FLUTUANTE) --- */
        .modal-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(0,0,0,0.6); z-index: 1000;
            justify-content: center; align-items: center; overflow-y: auto;
        }
        .modal-content {
            background-color: white; padding: 30px; border-radius: 10px; width: 700px; max-width: 95%;
            border-top: 6px solid #2980b9; position: relative; margin: 20px auto;
        }
        .close-btn { position: absolute; top: 15px; right: 20px; font-size: 28px; cursor: pointer; color: #aaa; }
        
        .readonly { background-color: #eee; color: #555; pointer-events: none; border-color: #ddd; }
        
        .section-title {
            font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; color: #2980b9; 
            margin-top: 20px; margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 5px;
        }

    </style>
</head>
<body>

    <div class="main-container" id="conteudoParaPDF">

        <div class="header">
            <img src="https://sementesplanteforte.com.br/img/logo-1713454562.jpg" alt="Logo" class="logo-area" width="200">
            <h1>CALCULADORA PRECIFICAÇÃO</h1>
            <p class="subtitle">Cotação Comercial</p>
        </div>

        <div class="card">
            <h2>Dados da Cotação</h2>
            
            <div class="client-section">
                <div class="row">
                    <div class="col" style="flex: 2;">
                        <label>Nome do Cliente / Fazenda</label>
                        <input type="text" id="nomeCliente" placeholder="Ex: Fazenda Santa Clara">
                    </div>
                    <div class="col">
                        <label>Cidade / Estado</label>
                        <input type="text" id="cidadeCliente" placeholder="Ex: Sorriso - MT">
                    </div>
                </div>
                
                <div class="row">
                    <div class="col" style="flex: 2;">
                        <label>Produto / Cultivar</label>
                        <input type="text" id="nomeProduto" placeholder="Ex: Soja Intacta (Digite ou use a Ficha Técnica)">
                    </div>
                    <div class="col">
                        <label>Data</label>
                        <input type="text" id="dataCotacao" readonly>
                    </div>
                </div>
            </div>

            <div class="row" style="align-items: flex-end;">
                <div class="col">
                    <label>Custo do Produto (Saco 10kg)</label>
                    <input type="number" id="custoProduto" placeholder="0.00" class="input-destaque">
                </div>
                <div class="col" style="flex: 0 0 auto; padding-bottom: 5px;">
                    <button class="btn-blue hide-on-pdf" data-html2canvas-ignore="true" onclick="abrirModal()">🏭 Abrir Ficha Técnica (Produção)</button>
                </div>
            </div>

            <div class="row">
                <div class="col">
                    <label>Valor do Frete Total (R$)</label>
                    <input type="number" id="valorFrete" placeholder="0.00">
                </div>
                <div class="col">
                    <label>Margem de Lucro (%)</label>
                    <input type="number" id="margemLucro" placeholder="30">
                </div>
            </div>

            <div class="row">
                <div class="col">
                    <label>Impostos Totais (%)</label>
                    <input type="number" id="imposto" placeholder="18">
                </div>
                <div class="col">
                    <label>Comissão (%)</label>
                    <input type="number" id="comissao" placeholder="5">
                </div>
                <div class="col">
                    <label>Outras Taxas (%)</label>
                    <input type="number" id="outrasTaxas" placeholder="3.5">
                </div>
            </div>

            <button class="btn btn-green hide-on-pdf" data-html2canvas-ignore="true" onclick="calcularVenda()">Calcular Preço Final</button>

            <div class="resultado-box" id="areaResultado" style="display:none;">
                <div class="row">
                    <div class="col">
                        <span>Preço de Venda (FOB)</span>
                        <span class="valor-destaque" id="resFOB">R$ 0,00</span>
                    </div>
                    <div class="col">
                        <span>Preço de Venda (CIF)</span>
                        <span class="valor-destaque" id="resCIF">R$ 0,00</span>
                    </div>
                </div>
                
                <div class="hide-on-pdf" data-html2canvas-ignore="true">
                    <button class="btn btn-outline" onclick="salvarCotacao()">💾 Salvar no Histórico</button>
                    <button class="btn btn-red" onclick="gerarPDF()">📄 Baixar PDF da Cotação</button>
                </div>
            </div>
        </div>
    </div> <div class="main-container">
        <div class="card">
            <h2>Histórico de Cotações Salvas</h2>
            <div style="overflow-x: auto;">
                <table id="tabelaHistorico">
                    <thead>
                        <tr>
                            <th>Cliente</th>
                            <th>Produto</th> 
                            <th>Preço (CIF)</th>
                            <th style="text-align: center;">Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        </tbody>
                </table>
            </div>
            <div class="row" style="margin-top: 15px;">
                <div class="col">
                    <button class="btn-blue" onclick="limparHistorico()">Limpar Tudo</button>
                </div>
            </div>
        </div>
    </div>

    <div id="modalProducao" class="modal-overlay">
        <div class="modal-content">
            <span class="close-btn" onclick="fecharModal()">&times;</span>
            <h2 style="color: #2980b9; border:none; margin-bottom: 5px;">🏭 Ficha Técnica de Produção</h2>
            
            <label>Nome da Semente / Produto</label>
            <input type="text" id="nomeSemente" placeholder="Identificação do lote ou cultivar...">

            <div class="section-title">1. Dados da Semente Base</div>
            <div class="row">
                <div class="col"><label>Qtd Sementes (kg)</label><input type="number" id="qtdSemente" placeholder="0"></div>
                <div class="col"><label>Pureza Inicial (%)</label><input type="number" id="purezaInicial" placeholder="0"></div>
                <div class="col"><label>Pureza Desejada</label><input type="number" id="purezaDesejada" placeholder="Ex: 80"></div>
            </div>
            <div class="row">
                <div class="col"><label>Custo do Ponto (R$)</label><input type="number" id="custoPonto" placeholder="0.00"></div>
                <div class="col"><label>Pontos Utilizados</label><input type="text" id="pontosUtilizados" class="readonly" readonly></div>
            </div>

            <div class="section-title">2. Insumos (Seedgel & Grafite)</div>
            <div class="row">
                <div class="col"><label>Qtd Seedgel (kg)</label><input type="number" id="qtdSeedgel" placeholder="0"></div>
                <div class="col"><label>Custo Unit. Seedgel (R$)</label><input type="number" id="custoUnitSeedgel" placeholder="0.00"></div>
            </div>
            <div class="row">
                <div class="col"><label>Qtd Grafite (kg)</label><input type="number" id="qtdGrafite" placeholder="0"></div>
                <div class="col"><label>Custo Unit. Grafite (R$)</label><input type="number" id="custoUnitGrafite" placeholder="0.00"></div>
            </div>

            <div class="section-title">3. Acabamento</div>
            <div class="row">
                <div class="col"><label>Custo Emb. Unit. (R$)</label><input type="number" id="custoEmbalagem" placeholder="0.00"></div>
                <div class="col"><label>Custo Agregados (R$)</label><input type="number" id="custoAgregados" placeholder="0.00"></div>
            </div>

            <div style="background: #eafaf1; padding: 15px; margin-top: 20px; border-radius: 8px; border: 1px solid #c8e6c9;">
                <div class="row">
                    <div class="col"><p style="margin: 5px 0; font-size: 0.9em;">Custo Batida (+R$100):<br><strong id="resCustoBatida" style="font-size: 1.1em;">R$ 0,00</strong></p></div>
                    <div class="col"><p style="margin: 5px 0; font-size: 0.9em;">Peso Total Produzido:<br><strong id="resPesoTotal" style="font-size: 1.1em;">0 kg</strong></p></div>
                    <div class="col"><p style="margin: 5px 0; font-size: 0.9em;">Custo por Kg:<br><strong id="resCustoKg" style="font-size: 1.1em;">R$ 0,00</strong></p></div>
                </div>
                <hr style="border: 0; border-top: 1px dashed #ccc;">
                <p style="margin: 5px 0; text-align: center;">Custo Final Saco 10kg ( Produto + Emb.): <br><strong id="resSaco10kg" style="color:#2980b9; font-size: 1.4em;">R$ 0,00</strong></p>
            </div>

            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button class="btn btn-gray" style="margin-top:0;" onclick="fecharModal()">❌ Cancelar / Retornar</button>
                <button class="btn btn-green" style="background-color: #2980b9; margin-top:0;" onclick="calcularETransferir()">✅ Calcular e Usar este Custo</button>
            </div>
        </div>
    </div>

    <script>
        // --- INICIALIZAÇÃO ---
        window.onload = function() {
            carregarTabela();
            document.getElementById('dataCotacao').value = new Date().toLocaleDateString('pt-BR');
        }

        // --- FUNÇÃO PARA GERAR PDF (NOVA) ---
        function gerarPDF() {
            // Seleciona a área principal
            const element = document.getElementById('conteudoParaPDF');
            
            // Pega o nome do cliente para o arquivo
            const cliente = document.getElementById('nomeCliente').value || "Cliente";
            
            // Configurações do PDF
            const opt = {
                margin:       10,
                filename:     `Cotacao_${cliente}.pdf`,
                image:        { type: 'jpeg', quality: 0.98 },
                html2canvas:  { scale: 2 }, // Melhora a qualidade
                jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };

            // Gera e baixa
            html2pdf().set(opt).from(element).save();
        }

        // --- LÓGICA DE VENDA ---
        function calcularVenda() {
            let custo = parseFloat(document.getElementById('custoProduto').value) || 0;
            let frete = parseFloat(document.getElementById('valorFrete').value) || 0;
            let margem = parseFloat(document.getElementById('margemLucro').value) || 0;
            let imposto = parseFloat(document.getElementById('imposto').value) || 0;
            let comissao = parseFloat(document.getElementById('comissao').value) || 0;
            let taxas = parseFloat(document.getElementById('outrasTaxas').value) || 0;

            let somaPorcentagens = margem + imposto + comissao + taxas;

            if (somaPorcentagens >= 100) {
                alert("A soma das porcentagens não pode ser 100% ou mais.");
                return;
            }

            let divisor = 1 - (somaPorcentagens / 100);
            let precoFOB = custo / divisor;
            let precoCIF = (custo + frete) / divisor;

            document.getElementById('resFOB').innerText = precoFOB.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
            document.getElementById('resCIF').innerText = precoCIF.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
            
            document.getElementById('areaResultado').style.display = 'block';
        }

        // --- SALVAR COTAÇÃO (MELHORADO: SALVA TUDO) ---
        function salvarCotacao() {
            // Pega TODOS os campos
            let dados = {
                cliente: document.getElementById('nomeCliente').value,
                cidade: document.getElementById('cidadeCliente').value,
                produto: document.getElementById('nomeProduto').value,
                data: new Date().toLocaleDateString('pt-BR'),
                custo: document.getElementById('custoProduto').value,
                frete: document.getElementById('valorFrete').value,
                margem: document.getElementById('margemLucro').value,
                imposto: document.getElementById('imposto').value,
                comissao: document.getElementById('comissao').value,
                taxas: document.getElementById('outrasTaxas').value,
                precoFinal: document.getElementById('resCIF').innerText
            };

            let historico = JSON.parse(localStorage.getItem('historicoCotacoes')) || [];
            historico.push(dados);
            localStorage.setItem('historicoCotacoes', JSON.stringify(historico));

            carregarTabela();
            alert("Cotação salva no histórico!");
        }

        // --- CARREGAR ITEM DO HISTÓRICO (NOVO) ---
        function carregarItem(index) {
            let historico = JSON.parse(localStorage.getItem('historicoCotacoes')) || [];
            let item = historico[index];

            if(item) {
                // Preenche os campos de volta
                document.getElementById('nomeCliente').value = item.cliente || "";
                document.getElementById('cidadeCliente').value = item.cidade || "";
                document.getElementById('nomeProduto').value = item.produto || "";
                document.getElementById('custoProduto').value = item.custo || "";
                
                document.getElementById('valorFrete').value = item.frete || "";
                document.getElementById('margemLucro').value = item.margem || "";
                document.getElementById('imposto').value = item.imposto || "";
                document.getElementById('comissao').value = item.comissao || "";
                document.getElementById('outrasTaxas').value = item.taxas || "";

                // Recalcula para mostrar o resultado
                calcularVenda();
                
                // Rola a tela para o topo
                window.scrollTo(0, 0);
                alert("Dados carregados! Verifique os valores acima.");
            }
        }

        // --- TABELA DE HISTÓRICO (COM BOTÃO CARREGAR) ---
        function carregarTabela() {
            let historico = JSON.parse(localStorage.getItem('historicoCotacoes')) || [];
            let tbody = document.querySelector('#tabelaHistorico tbody');
            tbody.innerHTML = ""; 

            // Vamos mostrar do mais novo para o mais antigo (reverse)
            historico.forEach((item, index) => {
                let row = `<tr>
                    <td><strong>${item.cliente}</strong></td>
                    <td>${item.produto}</td>
                    <td>${item.precoFinal || item.preco}</td>
                    <td style="text-align: center;">
                        <button class="btn-action btn-load" onclick="carregarItem(${index})" title="Carregar Dados">📝</button>
                        <button class="btn-action btn-delete" onclick="deletarItem(${index})" title="Apagar">🗑️</button>
                    </td>
                </tr>`;
                tbody.innerHTML += row;
            });
        }

        function deletarItem(index) {
            if(confirm("Deseja apagar este item?")) {
                let historico = JSON.parse(localStorage.getItem('historicoCotacoes')) || [];
                historico.splice(index, 1);
                localStorage.setItem('historicoCotacoes', JSON.stringify(historico));
                carregarTabela();
            }
        }

        function limparHistorico() {
            if(confirm("Tem certeza que deseja apagar TODO o histórico?")) {
                localStorage.removeItem('historicoCotacoes');
                carregarTabela();
            }
        }

        // --- CONTROLE DA JANELA (ABRIR/FECHAR) ---
        function abrirModal() { document.getElementById('modalProducao').style.display = 'flex'; }
        function fecharModal() { document.getElementById('modalProducao').style.display = 'none'; }

        // --- LÓGICA DE PRODUÇÃO (BATIDA) ---
        function calcularETransferir() {
            // Mesma lógica anterior
            let nomeSemente = document.getElementById('nomeSemente').value;
            let qtdSemente = parseFloat(document.getElementById('qtdSemente').value) || 0;
            let purezaDesejada = parseFloat(document.getElementById('purezaDesejada').value) || 0;
            let custoPonto = parseFloat(document.getElementById('custoPonto').value) || 0;
            let qtdSeedgel = parseFloat(document.getElementById('qtdSeedgel').value) || 0;
            let custoUnitSeedgel = parseFloat(document.getElementById('custoUnitSeedgel').value) || 0;
            let qtdGrafite = parseFloat(document.getElementById('qtdGrafite').value) || 0;
            let custoUnitGrafite = parseFloat(document.getElementById('custoUnitGrafite').value) || 0;
            let custoEmb = parseFloat(document.getElementById('custoEmbalagem').value) || 0;
            let custoAgreg = parseFloat(document.getElementById('custoAgregados').value) || 0;

            let pontosUtilizados = qtdSemente * purezaDesejada; 
            document.getElementById('pontosUtilizados').value = pontosUtilizados.toFixed(2);
            let custoSementeTotal = pontosUtilizados * custoPonto; 
            let custoTotalSeedgel = qtdSeedgel * custoUnitSeedgel; 
            let custoTotalGrafite = qtdGrafite * custoUnitGrafite; 
            let custoBatida = custoSementeTotal + custoTotalSeedgel + custoTotalGrafite + 100; 
            let pesoTotalBatida = qtdSemente + qtdSeedgel + qtdGrafite;
            
            if (pesoTotalBatida === 0) { alert("Preencha as quantidades."); return; }

            let custoPorKg = custoBatida / pesoTotalBatida; 
            let custoConteudo10kg = custoPorKg * 10;
            let custoFinalSaco = (custoEmb + custoAgreg) + custoConteudo10kg;

            document.getElementById('resCustoBatida').innerText = custoBatida.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            document.getElementById('resPesoTotal').innerText = pesoTotalBatida.toFixed(2) + " kg";
            document.getElementById('resCustoKg').innerText = custoPorKg.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            document.getElementById('resSaco10kg').innerText = custoFinalSaco.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});

            document.getElementById('custoProduto').value = custoFinalSaco.toFixed(2);
            if(nomeSemente !== "") { document.getElementById('nomeProduto').value = nomeSemente; }
            setTimeout(function() { fecharModal(); }, 500); 
        }
    </script>
</body>
</html>
"""

# Renderizar o HTML dentro do Streamlit
components.html(html_codigo, height=1400, scrolling=True)