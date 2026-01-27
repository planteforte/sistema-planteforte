"""
Configuração de Logging - Dashboard Comercial Tiny ERP
Configura logging estruturado para toda a aplicação
"""

import logging
import logging.handlers
from config import Config

def configurar_logging():
    """
    Configura logging estruturado para a aplicação.
    Cria logs em arquivo e console com níveis apropriados.
    """
    # Criar logger raiz
    logger = logging.getLogger()
    logger.setLevel(Config.LOG_LEVEL)
    
    # Formato de log detalhado
    formato = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo (com rotação)
    try:
        # Verifica se o nome do arquivo está definido, senão usa padrão
        nome_arquivo = getattr(Config, 'LOG_FILE', 'dashboard.log')
        
        file_handler = logging.handlers.RotatingFileHandler(
            nome_arquivo,
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding='utf-8' # Importante para evitar erros de acentuação
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formato)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Aviso: Não foi possível criar arquivo de log: {e}")
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(Config.LOG_LEVEL)
    console_handler.setFormatter(formato)
    logger.addHandler(console_handler)
    
    return logger

# Configurar logging ao importar
logger = configurar_logging()
