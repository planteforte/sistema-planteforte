"""
Arquivo de Configuração - Dashboard Comercial Tiny ERP
Centraliza todas as configurações da aplicação
"""

import os
from datetime import datetime

class Config:
    """Configurações da aplicação"""
    
    # ============ URLs de API ============
    TINY_API_URL = os.getenv(
        "TINY_API_URL",
        "https://api.tiny.com.br/api2/notas.fiscais.pesquisa.php"
    )
    
    # NOVO ENDEREÇO PARA DETALHES
    TINY_API_OBTER_URL = os.getenv(
        "TINY_API_OBTER_URL",
        "https://api.tiny.com.br/api2/nota.fiscal.obter.php"
    )
    
    IBGE_URL = os.getenv(
        "IBGE_URL",
        "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"
    )
    
    # ============ Datas Padrão ============
    DATA_INICIO_PADRAO = datetime(2026, 1, 1)
    DATA_FIM_PADRAO = datetime.now()
    
    # ============ Cache ============
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hora em segundos
    
    # ============ Logging ============
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "dashboard.log")
    
    # ============ Timeout ============
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))  # Aumentei para 20s
    
    # ============ Códigos UF (IBGE) ============
    CODIGOS_UF = {
        11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
        21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
        31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR', 42: 'SC', 43: 'RS',
        50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
    }
    
    # ============ Streamlit ============
    PAGE_TITLE = "Dashboard Comercial - Tiny ERP"
    PAGE_LAYOUT = "wide"
    SIDEBAR_STATE = "expanded"