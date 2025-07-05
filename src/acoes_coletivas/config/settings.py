"""
Configurações centralizadas do sistema
"""

from pydantic import BaseSettings, Field
from pathlib import Path
import os


class Settings(BaseSettings):
    """Configurações principais do sistema"""
    
    # Configurações da aplicação
    app_name: str = Field("Ferramenta de Análise de Ações Coletivas", env="APP_NAME")
    version: str = Field("1.0.0", env="VERSION")
    debug: bool = Field(False, env="DEBUG")
    
    # Configurações do banco de dados
    database_url: str = Field("sqlite:///./data/acoes_coletivas.db", env="DATABASE_URL")
    
    # Configurações do scraper
    selenium_timeout: int = Field(30, env="SELENIUM_TIMEOUT")
    request_timeout: int = Field(30, env="REQUEST_TIMEOUT")
    request_delay: float = Field(2.0, env="REQUEST_DELAY")
    selenium_headless: bool = Field(True, env="SELENIUM_HEADLESS")
    
    # URLs do sistema Falcão
    falcao_base_url: str = Field("https://jurisprudencia.jt.jus.br", env="FALCAO_BASE_URL")
    falcao_search_url: str = Field("https://jurisprudencia.jt.jus.br/jurisprudencia-nacional/pesquisa", env="FALCAO_SEARCH_URL")
    falcao_api_url: str = Field("https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa", env="FALCAO_API_URL")
    
    # Configurações de busca
    default_collections: list = Field(["acordaos", "sentencas"], env="DEFAULT_COLLECTIONS")
    default_page_size: int = Field(10, env="DEFAULT_PAGE_SIZE")
    
    # Configurações de processamento NLP
    nlp_sentence_count: int = Field(10, env="NLP_SENTENCE_COUNT")
    nlp_language: str = Field("portuguese", env="NLP_LANGUAGE")
    
    # Configurações de logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/acoes_coletivas.log", env="LOG_FILE")
    
    # Configurações de diretórios
    data_dir: Path = Field(Path("data"), env="DATA_DIR")
    raw_data_dir: Path = Field(Path("data/raw"), env="RAW_DATA_DIR")
    processed_data_dir: Path = Field(Path("data/processed"), env="PROCESSED_DATA_DIR")
    exports_dir: Path = Field(Path("data/exports"), env="EXPORTS_DIR")
    logs_dir: Path = Field(Path("logs"), env="LOGS_DIR")
    
    # Configurações de filtros padrão
    default_defendant: str = Field("Banco do Brasil", env="DEFAULT_DEFENDANT")
    collective_action_keywords: list = Field(
        ["sindicato", "ação coletiva", "substituição processual", "tutela coletiva"],
        env="COLLECTIVE_ACTION_KEYWORDS"
    )
    
    # Configurações de retry
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_delay: float = Field(5.0, env="RETRY_DELAY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Criar diretórios se não existirem
        self.create_directories()
    
    def create_directories(self):
        """Cria os diretórios necessários se não existirem"""
        directories = [
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.exports_dir,
            self.logs_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Instância global das configurações
settings = Settings() 