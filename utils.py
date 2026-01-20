"""
Módulo de Utilitários - Dashboard Comercial Tiny ERP
Funções auxiliares para processamento de dados
"""

import unicodedata
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TextUtils:
    """Utilitários para processamento de texto"""
    
    @staticmethod
    def remover_acentos(texto: str) -> str:
        """
        Remove acentos de um texto e converte para maiúsculas.
        
        Args:
            texto: Texto a ser processado
            
        Returns:
            Texto sem acentos em maiúsculas
            
        Exemplo:
            >>> TextUtils.remover_acentos("São Paulo")
            'SAO PAULO'
        """
        if not isinstance(texto, str):
            return ""
        
        try:
            texto = texto.upper()
            nfkd = unicodedata.normalize('NFKD', texto)
            return "".join([c for c in nfkd if not unicodedata.combining(c)])
        except Exception as e:
            logger.error(f"Erro ao remover acentos de '{texto}': {e}")
            return texto.upper()
    
    @staticmethod
    def gerar_chave_cidade(cidade: str, uf: str) -> str:
        """
        Gera uma chave única para cidade-estado.
        
        Args:
            cidade: Nome da cidade
            uf: Sigla do estado
            
        Returns:
            Chave formatada (ex: "SAO PAULO-SP")
            
        Exemplo:
            >>> TextUtils.gerar_chave_cidade("São Paulo", "SP")
            'SAO PAULO-SP'
        """
        cidade_limpa = TextUtils.remover_acentos(cidade)
        return f"{cidade_limpa}-{uf}"


class DataUtils:
    """Utilitários para processamento de dados"""
    
    @staticmethod
    def converter_valor(valor_str: Optional[str]) -> float:
        """
        Converte string de valor para float de forma segura.
        
        Args:
            valor_str: String contendo o valor
            
        Returns:
            Valor como float, ou 0.0 se inválido
            
        Exemplo:
            >>> DataUtils.converter_valor("100.50")
            100.5
            >>> DataUtils.converter_valor("abc")
            0.0
        """
        try:
            if valor_str is None or valor_str == "":
                return 0.0
            return float(valor_str)
        except (ValueError, TypeError) as e:
            logger.warning(f"Valor inválido para conversão: '{valor_str}' - {e}")
            return 0.0
    
    @staticmethod
    def validar_data(data_str: str, formato: str = "%d/%m/%Y") -> bool:
        """
        Valida se uma string é uma data válida.
        
        Args:
            data_str: String da data
            formato: Formato esperado da data
            
        Returns:
            True se válida, False caso contrário
        """
        try:
            from datetime import datetime
            datetime.strptime(data_str, formato)
            return True
        except ValueError:
            logger.warning(f"Data inválida: '{data_str}'")
            return False


class ValidationUtils:
    """Utilitários para validação de dados"""
    
    @staticmethod
    def validar_token_api(token: str) -> bool:
        """
        Valida se um token de API tem formato básico válido.
        
        Args:
            token: Token a validar
            
        Returns:
            True se tem formato válido
        """
        if not token or not isinstance(token, str):
            return False
        
        # Token deve ter pelo menos 10 caracteres
        if len(token) < 10:
            logger.warning("Token muito curto")
            return False
        
        return True
    
    @staticmethod
    def validar_periodo_datas(data_ini, data_fim) -> bool:
        """
        Valida se o período de datas é válido.
        
        Args:
            data_ini: Data inicial
            data_fim: Data final
            
        Returns:
            True se período é válido
        """
        if data_ini > data_fim:
            logger.warning(f"Data inicial ({data_ini}) maior que data final ({data_fim})")
            return False
        
        return True
