"""
Configurações centralizadas do sistema
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
import os


class Settings(BaseSettings):
    """Configurações principais do sistema"""
    
    # Configurações da aplicação
    app_name: str = Field(default="Ferramenta de Análise de Ações Coletivas", alias="APP_NAME")
    version: str = Field(default="1.0.0", alias="VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Configurações do banco de dados
    database_url: str = Field(default="sqlite:///./data/acoes_coletivas.db", alias="DATABASE_URL")
    
    # Configurações do scraper
    selenium_timeout: int = Field(default=30, alias="SELENIUM_TIMEOUT")
    request_timeout: int = Field(default=30, alias="REQUEST_TIMEOUT")
    request_delay: float = Field(default=2.0, alias="REQUEST_DELAY")
    selenium_headless: bool = Field(default=True, alias="SELENIUM_HEADLESS")
    
    # URLs do sistema Falcão
    falcao_base_url: str = Field(default="https://jurisprudencia.jt.jus.br", alias="FALCAO_BASE_URL")
    falcao_search_url: str = Field(default="https://jurisprudencia.jt.jus.br/jurisprudencia-nacional/pesquisa", alias="FALCAO_SEARCH_URL")
    falcao_api_url: str = Field(default="https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa", alias="FALCAO_API_URL")
    
    # Configurações de busca
    default_collections: list = Field(default=["acordaos", "sentencas"], alias="DEFAULT_COLLECTIONS")
    default_page_size: int = Field(default=10, alias="DEFAULT_PAGE_SIZE")
    
    # Configurações de processamento NLP
    nlp_sentence_count: int = Field(default=10, alias="NLP_SENTENCE_COUNT")
    nlp_language: str = Field(default="portuguese", alias="NLP_LANGUAGE")
    
    # Configurações de logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/acoes_coletivas.log", alias="LOG_FILE")
    
    # Configurações de diretórios
    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    raw_data_dir: Path = Field(default=Path("data/raw"), alias="RAW_DATA_DIR")
    processed_data_dir: Path = Field(default=Path("data/processed"), alias="PROCESSED_DATA_DIR")
    exports_dir: Path = Field(default=Path("data/exports"), alias="EXPORTS_DIR")
    logs_dir: Path = Field(default=Path("logs"), alias="LOGS_DIR")
    
    # Configurações de filtros padrão
    default_defendant: str = Field(default="Banco do Brasil", alias="DEFAULT_DEFENDANT")
    collective_action_keywords: list = Field(
        default=["sindicato", "ação coletiva", "substituição processual", "tutela coletiva"],
        alias="COLLECTIVE_ACTION_KEYWORDS"
    )
    
    # Configurações de retry
    max_retries: int = Field(default=3, description="Número máximo de tentativas")
    retry_delay: float = Field(default=2.0, description="Delay entre tentativas")
    
    # Configurações da API Flask
    flask_env: str = Field(default="production", alias="FLASK_ENV")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=5000, alias="PORT")
    secret_key: str = Field(default="dev-secret-key-change-in-production", alias="SECRET_KEY")
    
    # Configurações de CORS
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    
    # Configurações de cache
    redis_url: str = Field(default="", alias="REDIS_URL")
    
    # Configurações de documentação
    api_docs_enabled: bool = Field(default=True, alias="API_DOCS_ENABLED")
    api_docs_path: str = Field(default="/api/docs/", alias="API_DOCS_PATH")
    
    # Configurações de performance
    max_content_length: int = Field(default=16777216, alias="MAX_CONTENT_LENGTH")
    threads: int = Field(default=6, alias="THREADS")
    
    # Configurações de logging adicional
    log_json_format: bool = Field(default=True, alias="LOG_JSON_FORMAT")
    
    # Configurações do Scraper
    scraper_headless: bool = Field(default=True, description="Executar Chrome em modo headless")
    scraper_timeout: int = Field(default=30, description="Timeout para operações do Selenium")
    scraper_delay: float = Field(default=1.5, description="Delay entre requisições")
    
    # URLs da Jurisprudência do Trabalho
    jurisprudencia_base_url: str = Field(default="https://jurisprudencia.jt.jus.br", description="URL base da jurisprudência")
    jurisprudencia_search_url: str = Field(default="https://jurisprudencia.jt.jus.br/pesquisa", description="URL de pesquisa")
    jurisprudencia_api_url: str = Field(default="https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa", description="URL da API")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Permite campos extras
        
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