"""
Manager do banco de dados SQLite
"""

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from contextlib import contextmanager
import json
from datetime import datetime

from .models import ProcessoJudicial, ResultadoNLP, LogExecucao
from ..utils.logging import LoggerMixin


class DatabaseManager(LoggerMixin):
    """
    Gerenciador do banco de dados SQLite
    """
    
    def __init__(self, db_path: str = "data/acoes_coletivas.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexões com o banco"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Inicializa o banco de dados criando as tabelas"""
        with self.get_connection() as conn:
            # Tabela de processos judiciais
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processos_judiciais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_processo TEXT NOT NULL,
                    numero_processo_planilha TEXT NOT NULL,
                    tribunal TEXT,
                    classe_processo TEXT,
                    tipo_documento TEXT,
                    data_julgamento TEXT,
                    data_publicacao TEXT,
                    relator TEXT,
                    partes TEXT,
                    link_decisao TEXT,
                    conteudo_bruto_decisao TEXT,
                    origem_texto TEXT,
                    colecao_api TEXT,
                    id_documento_api TEXT,
                    processado_nlp BOOLEAN DEFAULT FALSE,
                    data_coleta TEXT NOT NULL,
                    data_processamento TEXT,
                    metadados TEXT,
                    UNIQUE(numero_processo_planilha, id_documento_api)
                )
            ''')
            
            # Tabela de resultados NLP
            conn.execute('''
                CREATE TABLE IF NOT EXISTS resultados_nlp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    processo_id INTEGER NOT NULL,
                    resumo_extrativo TEXT,
                    palavras_chave TEXT,
                    tema_principal TEXT,
                    sentimento TEXT,
                    entidades_nomeadas TEXT,
                    metadados_nlp TEXT,
                    data_processamento TEXT NOT NULL,
                    FOREIGN KEY (processo_id) REFERENCES processos_judiciais (id)
                )
            ''')
            
            # Tabela de logs de execução
            conn.execute('''
                CREATE TABLE IF NOT EXISTS logs_execucao (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operacao TEXT NOT NULL,
                    status TEXT NOT NULL,
                    mensagem TEXT,
                    detalhes TEXT,
                    tempo_execucao REAL,
                    data_execucao TEXT NOT NULL
                )
            ''')
            
            # Índices para melhorar performance
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_processos_numero 
                ON processos_judiciais(numero_processo)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_processos_planilha 
                ON processos_judiciais(numero_processo_planilha)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_processos_processado 
                ON processos_judiciais(processado_nlp)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_logs_operacao 
                ON logs_execucao(operacao)
            ''')
            
            conn.commit()
        
        self.log_operation("database_initialized", db_path=str(self.db_path))
    
    # Métodos para ProcessoJudicial
    def insert_processo(self, processo: ProcessoJudicial) -> int:
        """Insere um novo processo judicial"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO processos_judiciais (
                    numero_processo, numero_processo_planilha, tribunal,
                    classe_processo, tipo_documento, data_julgamento,
                    data_publicacao, relator, partes, link_decisao,
                    conteudo_bruto_decisao, origem_texto, colecao_api,
                    id_documento_api, processado_nlp, data_coleta,
                    data_processamento, metadados
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                processo.numero_processo, processo.numero_processo_planilha,
                processo.tribunal, processo.classe_processo, processo.tipo_documento,
                processo.data_julgamento, processo.data_publicacao, processo.relator,
                processo.partes, processo.link_decisao, processo.conteudo_bruto_decisao,
                processo.origem_texto, processo.colecao_api, processo.id_documento_api,
                processo.processado_nlp, processo.data_coleta.isoformat(),
                processo.data_processamento.isoformat() if processo.data_processamento else None,
                processo.metadados
            ))
            
            conn.commit()
            processo_id = cursor.lastrowid
            
            self.log_operation(
                "processo_inserted",
                processo_id=processo_id,
                numero_processo=processo.numero_processo_planilha
            )
            
            return processo_id
    
    def get_processo_by_id(self, processo_id: int) -> Optional[ProcessoJudicial]:
        """Busca um processo por ID"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM processos_judiciais WHERE id = ?
            ''', (processo_id,))
            
            row = cursor.fetchone()
            if row:
                return ProcessoJudicial.from_dict(dict(row))
            return None
    
    def get_processos_nao_processados(self, limit: int = 100) -> List[ProcessoJudicial]:
        """Busca processos que ainda não foram processados por NLP"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM processos_judiciais 
                WHERE processado_nlp = FALSE 
                LIMIT ?
            ''', (limit,))
            
            return [ProcessoJudicial.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def update_processo_processado(self, processo_id: int, data_processamento: datetime = None):
        """Marca um processo como processado"""
        if data_processamento is None:
            data_processamento = datetime.now()
        
        with self.get_connection() as conn:
            conn.execute('''
                UPDATE processos_judiciais 
                SET processado_nlp = TRUE, data_processamento = ?
                WHERE id = ?
            ''', (data_processamento.isoformat(), processo_id))
            
            conn.commit()
            
            self.log_operation(
                "processo_marked_processed",
                processo_id=processo_id
            )
    
    def processo_existe(self, numero_processo_planilha: str, id_documento_api: str) -> bool:
        """Verifica se um processo já existe no banco"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM processos_judiciais 
                WHERE numero_processo_planilha = ? AND id_documento_api = ?
            ''', (numero_processo_planilha, id_documento_api))
            
            return cursor.fetchone()[0] > 0
    
    # Métodos para ResultadoNLP
    def insert_resultado_nlp(self, resultado: ResultadoNLP) -> int:
        """Insere um resultado de processamento NLP"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO resultados_nlp (
                    processo_id, resumo_extrativo, palavras_chave,
                    tema_principal, sentimento, entidades_nomeadas,
                    metadados_nlp, data_processamento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                resultado.processo_id, resultado.resumo_extrativo,
                resultado.palavras_chave, resultado.tema_principal,
                resultado.sentimento, resultado.entidades_nomeadas,
                resultado.metadados_nlp, resultado.data_processamento.isoformat()
            ))
            
            conn.commit()
            resultado_id = cursor.lastrowid
            
            self.log_operation(
                "resultado_nlp_inserted",
                resultado_id=resultado_id,
                processo_id=resultado.processo_id
            )
            
            return resultado_id
    
    def get_resultado_nlp_by_processo(self, processo_id: int) -> Optional[ResultadoNLP]:
        """Busca resultado NLP por processo"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM resultados_nlp WHERE processo_id = ?
            ''', (processo_id,))
            
            row = cursor.fetchone()
            if row:
                return ResultadoNLP.from_dict(dict(row))
            return None
    
    # Métodos para LogExecucao
    def insert_log(self, log: LogExecucao) -> int:
        """Insere um log de execução"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO logs_execucao (
                    operacao, status, mensagem, detalhes,
                    tempo_execucao, data_execucao
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                log.operacao, log.status, log.mensagem,
                log.detalhes, log.tempo_execucao,
                log.data_execucao.isoformat()
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_logs_by_operacao(self, operacao: str, limit: int = 100) -> List[LogExecucao]:
        """Busca logs por operação"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM logs_execucao 
                WHERE operacao = ? 
                ORDER BY data_execucao DESC 
                LIMIT ?
            ''', (operacao, limit))
            
            return [LogExecucao.from_dict(dict(row)) for row in cursor.fetchall()]
    
    # Métodos de estatísticas
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco de dados"""
        with self.get_connection() as conn:
            stats = {}
            
            # Contagem de processos
            cursor = conn.execute('SELECT COUNT(*) FROM processos_judiciais')
            stats['total_processos'] = cursor.fetchone()[0]
            
            # Contagem de processos processados
            cursor = conn.execute('SELECT COUNT(*) FROM processos_judiciais WHERE processado_nlp = TRUE')
            stats['processos_processados'] = cursor.fetchone()[0]
            
            # Contagem de resultados NLP
            cursor = conn.execute('SELECT COUNT(*) FROM resultados_nlp')
            stats['resultados_nlp'] = cursor.fetchone()[0]
            
            # Contagem de logs
            cursor = conn.execute('SELECT COUNT(*) FROM logs_execucao')
            stats['total_logs'] = cursor.fetchone()[0]
            
            # Tribunais únicos
            cursor = conn.execute('SELECT COUNT(DISTINCT tribunal) FROM processos_judiciais')
            stats['tribunais_unicos'] = cursor.fetchone()[0]
            
            # Data da última coleta
            cursor = conn.execute('SELECT MAX(data_coleta) FROM processos_judiciais')
            ultima_coleta = cursor.fetchone()[0]
            stats['ultima_coleta'] = ultima_coleta
            
            return stats 