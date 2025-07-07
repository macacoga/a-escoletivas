"""
Scraper para a API de Jurisprudência do Trabalho
Baseado no sistema legado mas com melhorias significativas
"""

import requests
import time
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import quote
import re
from selenium.webdriver.common.keys import Keys

from .base import BaseScraper, SearchParams, ScrapingResult
from ..utils.logging import LoggerMixin
from ..config.settings import settings


class JurisprudenciaTrabalhoScraper(BaseScraper):
    """
    Scraper para coleta de jurisprudência do trabalho usando API HTTP direta
    """
    
    def __init__(self):
        super().__init__()
        self.base_url = settings.jurisprudencia_base_url
        self.api_url = settings.jurisprudencia_api_url
        
        # Configurações
        self.collections = ['acordaos', 'sentencas']
        self.max_retries = settings.max_retries
        self.retry_delay = settings.retry_delay
        
        # Session para reutilizar conexões
        self.session = requests.Session()
        
        # Headers para requisições
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'referer': 'https://jurisprudencia.jt.jus.br/pesquisa',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.session.headers.update(self.headers)
        
        self.logger.info("Scraper de Jurisprudência do Trabalho inicializado em MODO HTTP")
    
    def initialize_session(self) -> bool:
        """
        Inicializa a sessão HTTP (não precisa de Selenium)
        """
        try:
            self.logger.info("Inicializando sessão HTTP...")
            
            # Testar conectividade
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                self.logger.info("Sessão HTTP inicializada com sucesso")
                return True
            else:
                self.logger.error(f"Erro ao acessar {self.base_url}: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao inicializar sessão HTTP: {e}")
            return False
    
    def search_documents(self, processos: List[str], batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Busca documentos para uma lista de processos
        """
        if not self.initialize_session():
            self.logger.error("Falha ao inicializar sessão")
            return []
        
        all_documents = []
        
        try:
            # Processar em lotes
            for i in range(0, len(processos), batch_size):
                batch = processos[i:i + batch_size]
                self.logger.info(f"📦 Processando lote {i//batch_size + 1}/{(len(processos)-1)//batch_size + 1}")
                self.logger.info(f"   Processos: {len(batch)}")
                
                batch_documents = []
                for j, processo in enumerate(batch):
                    self.logger.info(f"Processando {j+1}/{len(batch)}: {processo}")
                    
                    # Buscar em todas as coleções
                    for colecao in self.collections:
                        self.logger.info(f"Buscando na coleção: {colecao}")
                        documentos = self._buscar_colecao(processo, colecao)
                        batch_documents.extend(documentos)
                        
                        # Delay entre requisições
                        time.sleep(settings.scraper_delay)
                
                all_documents.extend(batch_documents)
                self.logger.info(f"Lote concluído: {len(batch)} processos - {len(batch_documents)} documentos")
                
                # Salvar documentos do lote
                if batch_documents:
                    saved_count = self.save_documents(batch_documents)
                    self.logger.info(f"   💾 Salvos: {saved_count} documentos")
                
        except Exception as e:
            self.logger.error(f"Erro durante busca em lotes: {e}")
        
        finally:
            self.cleanup()
        
        return all_documents
    
    def _buscar_colecao(self, numero_processo: str, colecao: str) -> List[Dict[str, Any]]:
        """
        Busca documentos em uma coleção específica usando a API HTTP
        """
        try:
            # Parâmetros da API
            params = {
                'sessionId': '_fqbkfrh',  # Valor padrão
                'latitude': '0',
                'longitude': '0', 
                'juristkn': '36745b514e3847',  # Valor padrão
                'texto': numero_processo,
                'verTodosPrecedentes': 'false',
                'colecao': colecao,
                'tribunais': '',
                'page': '0',
                'size': '5',
                'pesquisaSomenteNasEmentas': 'false'
            }
            
            self.logger.info(f"Fazendo requisição HTTP para {colecao}...")
            
            # Fazer requisição HTTP direta
            response = self.session.get(
                self.api_url,
                params=params,
                timeout=30
            )
            
            self.logger.info(f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.logger.info(f"API respondeu com sucesso para {colecao}")
                    return self._processar_resposta_api(data, numero_processo, colecao)
                except json.JSONDecodeError:
                    self.logger.error(f"Resposta não é JSON válido para {colecao}")
                    self.logger.debug(f"Corpo da resposta: {response.text[:500]}")
                    return []
            else:
                self.logger.warning(f"API retornou status {response.status_code} para {colecao}")
                self.logger.debug(f"Corpo da resposta: {response.text[:500]}")
                return []
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na requisição HTTP para {colecao}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro inesperado para {colecao}: {e}")
            return []
    
    def _processar_resposta_api(self, dados_json: Any, numero_processo: str, colecao: str) -> List[Dict[str, Any]]:
        """
        Processa a resposta da API e extrai os documentos
        """
        documentos = []
        
        try:
            # A API retorna um array de documentos
            if isinstance(dados_json, list):
                documentos_api = dados_json
            elif isinstance(dados_json, dict):
                # Se for um objeto, procurar pelo array de documentos
                if 'content' in dados_json:
                    documentos_api = dados_json['content']
                elif 'data' in dados_json:
                    documentos_api = dados_json['data']
                elif 'results' in dados_json:
                    documentos_api = dados_json['results']
                elif 'documentos' in dados_json:
                    documentos_api = dados_json['documentos']
                else:
                    # Se não encontrar estrutura conhecida, tentar usar o próprio objeto
                    documentos_api = [dados_json]
            else:
                self.logger.warning(f"Formato de resposta inesperado: {type(dados_json)}")
                return []
            
            self.logger.info(f"Processando {len(documentos_api)} documentos da API para {colecao}")
            
            # Processar cada documento
            for i, doc in enumerate(documentos_api):
                try:
                    if not isinstance(doc, dict):
                        self.logger.debug(f"Documento {i} não é um dicionário: {type(doc)}")
                        continue
                    
                    # Extrair texto específico baseado na coleção
                    if colecao == 'acordaos':
                        conteudo = doc.get('highlightTextoAcordao') or doc.get('textoAcordao') or doc.get('ementa', '')
                    elif colecao == 'sentencas':
                        conteudo = doc.get('textoSentenca') or doc.get('highlightTextoSentenca') or doc.get('ementa', '')
                    else:
                        conteudo = doc.get('ementa', doc.get('texto', str(doc)))
                    
                    # Extrair informações do documento
                    documento = {
                        'numero_processo': numero_processo,
                        'tribunal': doc.get('tribunal', doc.get('sigla_tribunal', doc.get('siglaTribunal', 'Tribunal do Trabalho'))),
                        'classe_processo': doc.get('classe', doc.get('classe_processo', doc.get('classeProcessual', 'Ação Civil Pública'))),
                        'tipo_documento': 'Acórdão' if colecao == 'acordaos' else 'Sentença',
                        'data_julgamento': doc.get('data_julgamento', doc.get('dataJulgamento', doc.get('data_publicacao', ''))),
                        'data_publicacao': doc.get('data_publicacao', doc.get('dataJuntada', doc.get('data_julgamento', ''))),
                        'relator': doc.get('relator', doc.get('magistrado', doc.get('nomeRedator', 'Relator não identificado'))),
                        'redator': doc.get('redator', doc.get('nomeRedator', 'Redator não identificado')),
                        'partes': doc.get('partes', doc.get('envolvidos', 'Partes não identificadas')),
                        'link_decisao': doc.get('link', doc.get('url', doc.get('linkInteiro', ''))),
                        'referenciaLegislativa': doc.get('referenciaLegislativa', []),
                        'conteudo_bruto_decisao': conteudo,
                        'origem_texto': f'API Jurisprudência HTTP - {colecao}',
                        'metadados': json.dumps({
                            'fonte': 'API Jurisprudência HTTP',
                            'colecao': colecao,
                            'data_coleta': datetime.now().isoformat(),
                            'campos_disponiveis': list(doc.keys()),
                            'tamanho_conteudo': len(conteudo) if conteudo else 0
                        })
                    }
                    
                    documentos.append(documento)
                    self.logger.info(f"Documento {i+1} processado: {len(conteudo)} caracteres")
                    
                except Exception as e:
                    self.logger.debug(f"Erro ao processar documento {i}: {e}")
                    continue
            
            self.logger.info(f"Total de {len(documentos)} documentos extraídos da API para {colecao}")
            return documentos
            
        except Exception as e:
            self.logger.error(f"Erro ao processar resposta da API: {e}")
            return []
    
    def save_documents(self, documentos: List[Dict[str, Any]]) -> int:
        """
        Salva documentos no banco de dados
        """
        try:
            from ..database.manager import DatabaseManager
            from ..database.models import ProcessoJudicial
            from datetime import datetime
            
            db = DatabaseManager()
            saved_count = 0
            
            for doc in documentos:
                try:
                    # Converter dict para ProcessoJudicial
                    processo = ProcessoJudicial(
                        numero_processo=doc.get('numero_processo', ''),
                        numero_processo_planilha=doc.get('numero_processo', ''),
                        tribunal=doc.get('tribunal', ''),
                        classe_processo=doc.get('classe_processo', ''),
                        tipo_documento=doc.get('tipo_documento', ''),
                        data_julgamento=doc.get('data_julgamento', ''),
                        data_publicacao=doc.get('data_publicacao', ''),
                        relator=doc.get('relator', ''),
                        redator=doc.get('redator', ''),
                        partes=doc.get('partes', ''),
                        link_decisao=doc.get('link_decisao', ''),
                        conteudo_bruto_decisao=doc.get('conteudo_bruto_decisao', ''),
                        origem_texto=doc.get('origem_texto', ''),
                        colecao_api=doc.get('colecao_api', ''),
                        referencia_legislativa=json.dumps(doc.get('referenciaLegislativa', [])),
                        id_documento_api=f"{doc.get('numero_processo', '')}_{doc.get('tipo_documento', '')}_{hash(doc.get('conteudo_bruto_decisao', ''))}",
                        processado_nlp=False,
                        data_coleta=datetime.now(),
                        data_processamento=None,
                        metadados=doc.get('metadados', '{}')
                    )
                    
                    # Verificar se já existe
                    if not db.processo_existe(processo.numero_processo_planilha, processo.id_documento_api):
                        # Salvar documento no banco
                        processo_id = db.insert_processo(processo)
                        if processo_id > 0:
                            saved_count += 1
                    else:
                        self.logger.debug(f"Documento já existe: {processo.numero_processo_planilha}")
                        
                except Exception as e:
                    self.logger.error(f"Erro ao salvar documento: {e}")
                    continue
            
            self.logger.info(f"Salvos {saved_count}/{len(documentos)} documentos")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar documentos: {e}")
            return 0
    
    def extract_document_content(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai e processa o conteúdo do documento (não precisa mais fazer scraping)
        """
        return document  # O conteúdo já está no documento
    
    def cleanup(self):
        """
        Limpa recursos (fecha sessão HTTP)
        """
        try:
            if hasattr(self, 'session'):
                self.session.close()
                self.logger.info("Sessão HTTP fechada")
        except Exception as e:
            self.logger.error(f"Erro ao limpar recursos: {e}")
    
    def __del__(self):
        """Destrutor para garantir limpeza"""
        self.cleanup()


# Aliases para compatibilidade
DataJudScraper = JurisprudenciaTrabalhoScraper
FalcaoScraper = JurisprudenciaTrabalhoScraper
JurisTKScraper = JurisprudenciaTrabalhoScraper 