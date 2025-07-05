"""
Sistema de logging estruturado para a aplicação
"""

import logging
import structlog
from pathlib import Path
import sys
from datetime import datetime
from typing import Any, Dict


def setup_logging(
    level: str = "INFO",
    log_file: str = "logs/acoes_coletivas.log",
    json_format: bool = True
) -> None:
    """
    Configura o sistema de logging estruturado
    
    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho para o arquivo de log
        json_format: Se True, usa formato JSON para logs
    """
    
    # Criar diretório de logs se não existir
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configurar o logging padrão do Python
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configurar structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Obtém um logger estruturado
    
    Args:
        name: Nome do logger (normalmente __name__)
        
    Returns:
        Logger estruturado
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Mixin para adicionar capacidades de logging a classes
    """
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Retorna um logger para a classe"""
        return get_logger(self.__class__.__name__)
    
    def log_operation(self, operation: str, **kwargs: Any) -> None:
        """
        Registra uma operação com contexto
        
        Args:
            operation: Nome da operação
            **kwargs: Dados de contexto
        """
        self.logger.info(
            "operation_executed",
            operation=operation,
            **kwargs
        )
    
    def log_error(self, error: Exception, operation: str = "", **kwargs: Any) -> None:
        """
        Registra um erro com contexto
        
        Args:
            error: Exceção ocorrida
            operation: Nome da operação onde ocorreu o erro
            **kwargs: Dados de contexto adicionais
        """
        self.logger.error(
            "error_occurred",
            error=str(error),
            error_type=type(error).__name__,
            operation=operation,
            **kwargs
        )
    
    def log_metrics(self, metrics: Dict[str, Any], operation: str = "") -> None:
        """
        Registra métricas de uma operação
        
        Args:
            metrics: Dicionário com métricas
            operation: Nome da operação
        """
        self.logger.info(
            "metrics_recorded",
            operation=operation,
            **metrics
        )


def log_execution_time(func):
    """
    Decorator para registrar o tempo de execução de uma função
    """
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        logger = get_logger(func.__module__)
        
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                "function_executed",
                function=func.__name__,
                execution_time=execution_time,
                success=True
            )
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.error(
                "function_failed",
                function=func.__name__,
                execution_time=execution_time,
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise
    
    return wrapper 