"""
Classes base para scrapers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import time
import random
from datetime import datetime

from ..utils.logging import LoggerMixin, log_execution_time
from ..config.settings import settings


@dataclass
class SearchParams:
    """Parâmetros de busca para o scraper"""
    texto: str
    colecao: str = "acordaos"
    page: int = 0
    size: int = 10
    tribunais: str = ""
    pesquisa_somente_nas_ementas: bool = False
    ver_todos_precedentes: bool = False
    session_id: Optional[str] = None
    juris_token: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para uso em requisições"""
        return {
            'texto': self.texto,
            'colecao': self.colecao,
            'page': self.page,
            'size': self.size,
            'tribunais': self.tribunais,
            'pesquisaSomenteNasEmentas': str(self.pesquisa_somente_nas_ementas).lower(),
            'verTodosPrecedentes': str(self.ver_todos_precedentes).lower(),
            'sessionId': self.session_id,
            'juristkn': self.juris_token
        }


@dataclass
class ScrapingResult:
    """Resultado de uma operação de scraping"""
    success: bool
    data: List[Dict[str, Any]]
    error: Optional[str] = None
    status_code: Optional[int] = None
    total_found: int = 0
    page: int = 0
    execution_time: float = 0.0
    
    def __post_init__(self):
        if self.data is None:
            self.data = []
        if self.total_found == 0:
            self.total_found = len(self.data)


class BaseScraper(ABC, LoggerMixin):
    """
    Classe base para todos os scrapers
    """
    
    def __init__(self):
        self.session_id: Optional[str] = None
        self.juris_token: Optional[str] = None
        self.last_request_time: Optional[datetime] = None
        self.retry_count: int = 0
        self.max_retries: int = settings.max_retries
        self.retry_delay: float = settings.retry_delay
        self.request_delay: float = settings.request_delay
    
    @abstractmethod
    def initialize_session(self) -> bool:
        """
        Inicializa a sessão do scraper
        
        Returns:
            bool: True se a inicialização foi bem-sucedida
        """
        pass
    
    @abstractmethod
    def search_documents(self, params: SearchParams) -> ScrapingResult:
        """
        Busca documentos com base nos parâmetros
        
        Args:
            params: Parâmetros de busca
            
        Returns:
            ScrapingResult: Resultado da busca
        """
        pass
    
    @abstractmethod
    def extract_document_content(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai o conteúdo de um documento
        
        Args:
            document: Dados do documento
            
        Returns:
            Dict com conteúdo extraído
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Limpa recursos utilizados pelo scraper"""
        pass
    
    def set_tokens(self, session_id: str, juris_token: str):
        """Define os tokens de autenticação"""
        self.session_id = session_id
        self.juris_token = juris_token
        self.log_operation("tokens_set", session_id=session_id[:10] + "...")
    
    def wait_between_requests(self):
        """Aguarda entre requisições para evitar rate limiting"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.request_delay:
                wait_time = self.request_delay - elapsed
                time.sleep(wait_time)
        
        self.last_request_time = datetime.now()
    
    def retry_on_failure(self, func, *args, **kwargs):
        """
        Executa uma função com retry automático
        
        Args:
            func: Função a ser executada
            *args: Argumentos da função
            **kwargs: Argumentos nomeados da função
            
        Returns:
            Resultado da função
        """
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries:
                    self.log_error(e, f"retry_failed_after_{self.max_retries}_attempts")
                    raise
                
                wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                self.logger.warning(
                    "retry_attempt",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    wait_time=wait_time,
                    error=str(e)
                )
                time.sleep(wait_time)
    
    def validate_tokens(self) -> bool:
        """Valida se os tokens estão definidos"""
        if not self.session_id or not self.juris_token:
            self.logger.error("tokens_missing", session_id=bool(self.session_id), juris_token=bool(self.juris_token))
            return False
        return True
    
    def add_random_delay(self, min_delay: float = 0.5, max_delay: float = 2.0):
        """Adiciona um delay aleatório para simular comportamento humano"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    @log_execution_time
    def process_processo_list(self, processos: List[str], collections: List[str] = None) -> List[Dict[str, Any]]:
        """
        Processa uma lista de processos
        
        Args:
            processos: Lista de números de processo
            collections: Lista de coleções a pesquisar
            
        Returns:
            Lista de documentos extraídos
        """
        if collections is None:
            collections = settings.default_collections
        
        all_documents = []
        
        for i, processo in enumerate(processos):
            self.logger.info(
                "processing_processo",
                processo=processo,
                index=i + 1,
                total=len(processos)
            )
            
            for collection in collections:
                try:
                    params = SearchParams(
                        texto=processo,
                        colecao=collection,
                        size=settings.default_page_size,
                        session_id=self.session_id,
                        juris_token=self.juris_token
                    )
                    
                    result = self.search_documents(params)
                    
                    if result.success:
                        # Processar cada documento encontrado
                        for doc in result.data:
                            enhanced_doc = self.extract_document_content(doc)
                            enhanced_doc.update({
                                'processo_planilha': processo,
                                'colecao_api': collection,
                                'data_coleta': datetime.now().isoformat()
                            })
                            all_documents.append(enhanced_doc)
                        
                        self.log_operation(
                            "collection_processed",
                            processo=processo,
                            collection=collection,
                            documents_found=len(result.data)
                        )
                    else:
                        self.logger.warning(
                            "collection_processing_failed",
                            processo=processo,
                            collection=collection,
                            error=result.error
                        )
                    
                    # Aguardar entre coleções
                    self.wait_between_requests()
                    
                except Exception as e:
                    self.log_error(e, "process_collection_error", processo=processo, collection=collection)
                    continue
            
            # Aguardar entre processos
            self.add_random_delay()
        
        self.log_metrics({
            'total_processos': len(processos),
            'total_documents': len(all_documents),
            'average_docs_per_processo': len(all_documents) / len(processos) if processos else 0
        }, "process_processo_list")
        
        return all_documents


class ScraperException(Exception):
    """Exceção personalizada para erros de scraping"""
    pass


class AuthenticationException(ScraperException):
    """Exceção para erros de autenticação"""
    pass


class RateLimitException(ScraperException):
    """Exceção para erros de rate limiting"""
    pass


class ParseException(ScraperException):
    """Exceção para erros de parsing"""
    pass 