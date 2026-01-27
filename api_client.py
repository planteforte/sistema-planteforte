"""
Cliente da API Tiny ERP - Dashboard Comercial Tiny ERP
Encapsula toda a lógica de comunicação com a API
"""

import requests
import logging
import time
from datetime import datetime, date
from typing import List, Dict, Any, Union
from config import Config
from utils import ValidationUtils

logger = logging.getLogger(__name__)

class TinyAPIError(Exception):
    """Exceção personalizada para erros da API Tiny"""
    pass

class TinyAPIClient:
    """Cliente para comunicação com a API do Tiny ERP"""
    
    def __init__(self, token: str):
        if not ValidationUtils.validar_token_api(token):
            raise ValueError("Token de API inválido")
        
        self.token = token
        self.url_pesquisa = Config.TINY_API_URL
        self.url_obter = Config.TINY_API_OBTER_URL
        self.timeout = getattr(Config, 'REQUEST_TIMEOUT', 30)
        logger.info("TinyAPIClient inicializado")
    
    def buscar_vendas(self, data_ini: Union[date, datetime], data_fim: Union[date, datetime]) -> List[Dict[str, Any]]:
        """
        Busca a LISTA de notas fiscais (sem os produtos).
        """
        if not ValidationUtils.validar_periodo_datas(data_ini, data_fim):
            raise ValueError("Período de datas inválido")
        
        vendas = []
        pagina_atual = 1
        total_paginas = 1
        
        logger.info(f"Iniciando busca de vendas: {str(data_ini)} a {str(data_fim)}")
        
        while pagina_atual <= total_paginas:
            try:
                payload = {
                    'token': self.token,
                    'dataInicial': data_ini.strftime('%d/%m/%Y'),
                    'dataFinal': data_fim.strftime('%d/%m/%Y'),
                    'formato': 'JSON',
                    'pagina': pagina_atual
                }
                
                response = requests.post(self.url_pesquisa, data=payload, timeout=self.timeout)
                response.raise_for_status() 
                dados = response.json()
                
                status = dados.get('retorno', {}).get('status')
                if status == 'Erro':
                    erros = dados.get('retorno', {}).get('erros', [])
                    erro_msg = erros[0].get('erro', 'Erro desconhecido') if erros else "Erro desconhecido"

                    if "não retornou resultados" in erro_msg.lower():
                        break
                    elif "autenticação" in erro_msg.lower():
                        raise TinyAPIError("Token inválido")
                    else:
                        raise TinyAPIError(f"Erro na API: {erro_msg}")
                
                notas = dados.get('retorno', {}).get('notas_fiscais', [])
                vendas.extend(notas)
                total_paginas = int(dados.get('retorno', {}).get('numero_paginas', 1))
                pagina_atual += 1
                
            except Exception as e:
                logger.error(f"Erro na página {pagina_atual}: {e}")
                # Se der erro numa página, tenta parar para não travar tudo
                break
        
        return vendas

    def obter_detalhes_nota(self, id_nota: str) -> Dict[str, Any]:
        """
        Busca os DETALHES de uma única nota (incluindo produtos).
        """
        try:
            payload = {
                'token': self.token,
                'id': id_nota,
                'formato': 'JSON'
            }
            
            response = requests.post(self.url_obter, data=payload, timeout=self.timeout)
            
            # Tiny às vezes falha se fizermos muitas requisições rápidas.
            if response.status_code == 429:
                time.sleep(2)
                response = requests.post(self.url_obter, data=payload, timeout=self.timeout)
            
            if response.status_code != 200:
                return {}

            dados = response.json()
            status = dados.get('retorno', {}).get('status')
            
            # CORREÇÃO AQUI: Aceitar 'Sucesso' OU 'OK'
            if status == 'Sucesso' or status == 'OK':
                return dados.get('retorno', {}).get('nota_fiscal', {})
            
            return {}
            
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes da nota {id_nota}: {e}")
            return {}    
