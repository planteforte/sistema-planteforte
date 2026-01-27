"""
Cliente IBGE - Dashboard Comercial Tiny ERP
Carrega e processa dados geográficos do IBGE
"""

import pandas as pd
import logging
from config import Config
from utils import TextUtils

logger = logging.getLogger(__name__)


class IBGEClient:
    """Cliente para dados geográficos do IBGE"""
    
    @staticmethod
    def carregar_municipios() -> pd.DataFrame:
        """
        Carrega dados de municípios brasileiros com coordenadas.
        """
        try:
            logger.info(f"Carregando dados do IBGE de {Config.IBGE_URL}")
            
            # Carregar CSV
            df_ibge = pd.read_csv(Config.IBGE_URL)
            
            # Processar dados
            df_ibge['nome_limpo'] = df_ibge['nome'].apply(TextUtils.remover_acentos)
            
            # Mapear códigos UF para siglas (Define dicionário localmente se não estiver na config)
            codigos_uf_padrao = {
                11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
                21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
                31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR', 42: 'SC', 43: 'RS',
                50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
            }
            mapa_uf = getattr(Config, 'CODIGOS_UF', codigos_uf_padrao)
            
            df_ibge['UF'] = df_ibge['codigo_uf'].map(mapa_uf)
            
            # Gerar chave de cidade
            df_ibge['chave_cidade'] = (
                df_ibge['nome_limpo'] + '-' + df_ibge['UF']
            )
            
            # Selecionar colunas necessárias
            df_resultado = df_ibge[[
                'chave_cidade',
                'latitude',
                'longitude',
                'nome'
            ]].copy()
            
            logger.info(f"Carregados {len(df_resultado)} municípios")
            return df_resultado
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados do IBGE: {e}")
            raise    
