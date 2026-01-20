"""
Processador de Dados - Dashboard Comercial Tiny ERP
Realiza limpeza, transformação e cálculos nos dados
"""

import pandas as pd
import logging
import re  # Biblioteca para identificar padrões de texto
from typing import List, Dict, Any
from utils import TextUtils, DataUtils

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processamento centralizado de dados de vendas"""
    
    @staticmethod
    def identificar_canal(dados_venda: Dict[str, Any]) -> str:
        """
        Identifica o canal de venda analisando padrões no número do pedido ecommerce
        e nas observações, conforme regras de negócio da PlanteForte.
        """
        # Extrai os dados principais
        num_ecommerce = str(dados_venda.get('numero_ecommerce', '')).strip().upper()
        obs = str(dados_venda.get('obs', '')).lower()
        nome_cliente = str(dados_venda.get('nome', '')).lower()

        # -----------------------------------------------------------
        # REGRA 1: Análise pelo Número do Pedido (Padrão Ouro)
        # -----------------------------------------------------------
        
        if num_ecommerce and num_ecommerce != 'NONE' and num_ecommerce != '':
            # Padrão Shopee: Alfanumérico longo (ex: 260120HU3PR6HQ)
            # Verifica se tem letras E números misturados
            if re.search(r'[A-Z]', num_ecommerce) and re.search(r'[0-9]', num_ecommerce):
                return 'Shopee'
            
            # Padrão Mercado Livre: Apenas números e MUITO longo (ex: 2000011120510065)
            # Ou começa com #
            if num_ecommerce.startswith('#') or (num_ecommerce.isdigit() and len(num_ecommerce) > 10):
                return 'Mercado Livre'
            
            # Padrão Site: Apenas números e curto (ex: 9590)
            if num_ecommerce.isdigit() and len(num_ecommerce) <= 10:
                return 'Site'

        # -----------------------------------------------------------
        # REGRA 2: Pistas nas Observações (Fallback)
        # -----------------------------------------------------------
        if 'shopee' in obs:
            return 'Shopee'
        
        if 'mercadolivre' in obs or 'mercado livre' in obs or 'ebazar' in obs or 'meli' in obs:
            return 'Mercado Livre'
            
        if 'pagar-me' in obs or 'woocommerce' in obs or 'loja virtual' in obs:
            return 'Site'

        # -----------------------------------------------------------
        # REGRA 3: Venda Direta (Por exclusão)
        # -----------------------------------------------------------
        # Se não tem número de ecommerce e não caiu nas regras acima
        return 'Venda Direta'

    @staticmethod
    def processar_vendas_raw(vendas_raw: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Converte a lista crua da API para um DataFrame limpo e classificado.
        """
        if not vendas_raw:
            return pd.DataFrame()
            
        dados_processados = []
        
        for item in vendas_raw:
            # Proteção contra estrutura variada
            nf = item.get('nota_fiscal', item)
            
            # Dados do cliente
            cliente = nf.get('cliente', {})
            cidade = cliente.get('cidade', '')
            uf = cliente.get('uf', '')
            
            # Se não tiver cidade/uf no cliente, tenta na raiz
            if not cidade:
                cidade = nf.get('nome_municipio', '')
            if not uf:
                uf = nf.get('uf', '')
                
            # Só processa se tiver localização
            if cidade and uf:
                valor = DataUtils.converter_valor(nf.get('valor_nota', nf.get('valor', 0)))
                data_emissao = nf.get('data_emissao', '')
                
                # --- INTELIGÊNCIA DE CANAL APLICADA AQUI ---
                canal = DataProcessor.identificar_canal(nf)
                
                chave = TextUtils.gerar_chave_cidade(cidade, uf)
                
                dados_processados.append({
                    'Numero': nf.get('numero'),
                    'Cliente': nf.get('nome') or cliente.get('nome'),
                    'Data': data_emissao,
                    'Valor': valor,
                    'chave_cidade': chave,
                    'Cidade_Original': cidade,
                    'Estado': uf,
                    'Canal': canal
                })
                
        return pd.DataFrame(dados_processados)

    @staticmethod
    def enriquecer_com_coordenadas(df_vendas: pd.DataFrame, df_mapa: pd.DataFrame) -> pd.DataFrame:
        """
        Cruza as vendas com o mapa do IBGE (Inner Join).
        """
        if df_vendas.empty or df_mapa.empty:
            return pd.DataFrame()
            
        # Merge usando a chave única
        df_final = pd.merge(df_vendas, df_mapa, on='chave_cidade', how='inner')
        
        # Converter coluna de data
        df_final['Data_Obj'] = pd.to_datetime(df_final['Data'], dayfirst=True, errors='coerce')
        
        return df_final

    @staticmethod
    def calcular_kpis(df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula os indicadores principais."""
        if df.empty:
            return {
                'total_vendas': 0.0, 'ticket_medio': 0.0,
                'notas_emitidas': 0, 'cidades_atendidas': 0
            }
            
        return {
            'total_vendas': df['Valor'].sum(),
            'ticket_medio': df['Valor'].mean(),
            'notas_emitidas': len(df),
            'cidades_atendidas': df['chave_cidade'].nunique()
        }

    @staticmethod
    def agrupar_por_data(df: pd.DataFrame) -> pd.DataFrame:
        return df.groupby('Data_Obj')['Valor'].sum().reset_index().sort_values('Data_Obj')

    @staticmethod
    def agrupar_por_estado(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        return df.groupby('Estado')['Valor'].sum().reset_index().sort_values('Valor', ascending=False).head(top_n)

    @staticmethod
    def agrupar_por_cidade(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        return df.groupby('Cidade_Original')['Valor'].sum().reset_index().sort_values('Valor', ascending=False).head(top_n)