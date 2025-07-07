"""
Manager do banco de dados SQLite
"""

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from contextlib import contextmanager
import json
from datetime import datetime

from .models import ProcessoJudicial, ResultadoNLP, LogExecucao, EstatisticasNLP
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
                    redator TEXT,
                    partes TEXT,
                    link_decisao TEXT,
                    conteudo_bruto_decisao TEXT,
                    origem_texto TEXT,
                    colecao_api TEXT,
                    id_documento_api TEXT,
                    referencia_legislativa TEXT,
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
                    texto_processado TEXT,
                    resumo_extrativo TEXT,
                    resumo_estruturado TEXT,
                    palavras_chave TEXT,
                    tema_principal TEXT,
                    entidades_nomeadas TEXT,
                    direitos_trabalhistas TEXT,
                    valores_monetarios TEXT,
                    base_legal TEXT,
                    qualidade_texto REAL DEFAULT 0.0,
                    confianca_global REAL DEFAULT 0.0,
                    tempo_processamento REAL DEFAULT 0.0,
                    metodo_sumarizacao TEXT,
                    versao_pipeline TEXT DEFAULT '1.0.0',
                    metadados_nlp TEXT,
                    data_processamento TEXT NOT NULL,
                    FOREIGN KEY (processo_id) REFERENCES processos_judiciais (id)
                )
            ''')
            
            # Tabela de estatísticas NLP
            conn.execute('''
                CREATE TABLE IF NOT EXISTS estatisticas_nlp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_analise TEXT NOT NULL,
                    total_processos INTEGER DEFAULT 0,
                    processos_com_nlp INTEGER DEFAULT 0,
                    tempo_processamento_medio REAL DEFAULT 0.0,
                    qualidade_media REAL DEFAULT 0.0,
                    confianca_media REAL DEFAULT 0.0,
                    entidades_mais_comuns TEXT,
                    direitos_mais_comuns TEXT,
                    tribunais_distribuicao TEXT,
                    valores_estatisticas TEXT,
                    metadados_estatisticas TEXT
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
                    data_publicacao, relator, redator, partes, link_decisao,
                    conteudo_bruto_decisao, origem_texto, colecao_api,
                    id_documento_api, referencia_legislativa, processado_nlp, data_coleta,
                    data_processamento, metadados
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                processo.numero_processo, processo.numero_processo_planilha,
                processo.tribunal, processo.classe_processo, processo.tipo_documento,
                processo.data_julgamento, processo.data_publicacao, processo.relator,
                processo.redator, processo.partes, processo.link_decisao, processo.conteudo_bruto_decisao,
                processo.origem_texto, processo.colecao_api, processo.id_documento_api,
                processo.referencia_legislativa, processo.processado_nlp, processo.data_coleta.isoformat(),
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
            
            return processo_id if processo_id else 0
    
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
        """Busca processos que ainda não foram processados por NLP e têm texto"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM processos_judiciais 
                WHERE processado_nlp = 0 
                AND conteudo_bruto_decisao IS NOT NULL 
                AND LENGTH(conteudo_bruto_decisao) > 100
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,))
            
            return [ProcessoJudicial.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def get_processos_sem_conteudo(self, limit: int = 100) -> List[ProcessoJudicial]:
        """Busca processos que precisam de coleta (sem conteúdo)"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM processos_judiciais 
                WHERE (conteudo_bruto_decisao IS NULL OR conteudo_bruto_decisao = '')
                AND numero_processo_planilha IS NOT NULL
                AND numero_processo_planilha != ''
                ORDER BY id ASC
                LIMIT ?
            ''', (limit,))
            
            return [ProcessoJudicial.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def update_processo_processado(self, processo_id: int, data_processamento: datetime = datetime.now()):
        """Marca um processo como processado"""
        
        with self.get_connection() as conn:
            conn.execute('''
                UPDATE processos_judiciais 
                SET processado_nlp = 1, data_processamento = ?
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
                    processo_id, texto_processado, resumo_extrativo, resumo_estruturado,
                    palavras_chave, tema_principal, entidades_nomeadas,
                    direitos_trabalhistas, valores_monetarios, base_legal,
                    qualidade_texto, confianca_global, tempo_processamento,
                    metodo_sumarizacao, versao_pipeline, metadados_nlp, data_processamento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                resultado.processo_id, resultado.texto_processado,
                resultado.resumo_extrativo, resultado.resumo_estruturado,
                resultado.palavras_chave, resultado.tema_principal,
                resultado.entidades_nomeadas, resultado.direitos_trabalhistas,
                resultado.valores_monetarios, resultado.base_legal,
                resultado.qualidade_texto, resultado.confianca_global,
                resultado.tempo_processamento, resultado.metodo_sumarizacao,
                resultado.versao_pipeline, resultado.metadados_nlp,
                resultado.data_processamento.isoformat()
            ))
            
            conn.commit()
            resultado_id = cursor.lastrowid
            
            self.log_operation(
                "resultado_nlp_inserted",
                resultado_id=resultado_id,
                processo_id=resultado.processo_id
            )
            
            return resultado_id if resultado_id else 0
    
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
            return cursor.lastrowid if cursor.lastrowid else 0
    
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
            cursor = conn.execute('SELECT COUNT(*) FROM processos_judiciais WHERE processado_nlp = 1')
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
    
    # Métodos para EstatisticasNLP
    def insert_estatisticas_nlp(self, estatisticas: EstatisticasNLP) -> int:
        """Insere estatísticas de processamento NLP"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO estatisticas_nlp (
                    data_analise, total_processos, processos_com_nlp,
                    tempo_processamento_medio, qualidade_media, confianca_media,
                    entidades_mais_comuns, direitos_mais_comuns, tribunais_distribuicao,
                    valores_estatisticas, metadados_estatisticas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                estatisticas.data_analise.isoformat(),
                estatisticas.total_processos, estatisticas.processos_com_nlp,
                estatisticas.tempo_processamento_medio, estatisticas.qualidade_media,
                estatisticas.confianca_media, estatisticas.entidades_mais_comuns,
                estatisticas.direitos_mais_comuns, estatisticas.tribunais_distribuicao,
                estatisticas.valores_estatisticas, estatisticas.metadados_estatisticas
            ))
            
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else 0
    
    def get_latest_estatisticas_nlp(self) -> Optional[EstatisticasNLP]:
        """Busca as estatísticas NLP mais recentes"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM estatisticas_nlp 
                ORDER BY data_analise DESC 
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            if row:
                return EstatisticasNLP.from_dict(dict(row))
            return None
    
    # Métodos integrados com pipeline NLP
    def processar_texto_nlp(self, processo_id: int, pipeline) -> bool:
        """
        Processa um texto específico através do pipeline NLP
        
        Args:
            processo_id: ID do processo
            pipeline: Instância do pipeline NLP
            
        Returns:
            True se processado com sucesso, False caso contrário
        """
        try:
            # Buscar processo
            processo = self.get_processo_by_id(processo_id)
            if not processo:
                return False
            
            # Verificar se já foi processado
            if processo.processado_nlp:
                return True
            
            # Processar com pipeline
            resultado_nlp = pipeline.process_text(
                processo.conteudo_bruto_decisao,
                str(processo_id)
            )
            
            # Criar objeto ResultadoNLP
            resultado_db = ResultadoNLP(
                processo_id=processo_id,
                texto_processado=resultado_nlp.processed_text,
                resumo_extrativo=resultado_nlp.summary.get('summary', ''),
                resumo_estruturado=json.dumps(resultado_nlp.summary.get('context', {}), ensure_ascii=False),
                palavras_chave=json.dumps([e.text for e in resultado_nlp.entities], ensure_ascii=False),
                tema_principal=self._extract_main_theme(resultado_nlp.worker_rights),
                entidades_nomeadas=json.dumps([e.to_dict() for e in resultado_nlp.entities], ensure_ascii=False),
                direitos_trabalhistas=json.dumps([r.to_dict() for r in resultado_nlp.worker_rights], ensure_ascii=False),
                valores_monetarios=json.dumps(self._extract_monetary_values(resultado_nlp.entities), ensure_ascii=False),
                base_legal=json.dumps(self._extract_legal_basis(resultado_nlp.entities), ensure_ascii=False),
                qualidade_texto=resultado_nlp.text_quality.get('quality_score', 0.0),
                confianca_global=resultado_nlp.confidence_score,
                tempo_processamento=resultado_nlp.processing_time,
                metodo_sumarizacao=resultado_nlp.summary.get('method', 'unknown'),
                versao_pipeline='1.0.0',
                metadados_nlp=json.dumps(resultado_nlp.to_dict(), ensure_ascii=False)
            )
            
            # Salvar resultado
            self.insert_resultado_nlp(resultado_db)
            
            # Marcar processo como processado
            self.update_processo_processado(processo_id)
            
            return True
            
        except Exception as e:
            self.log_error(e, "processar_texto_nlp", processo_id=processo_id)
            return False
    
    def _extract_main_theme(self, worker_rights: List) -> str:
        """Extrai tema principal baseado nos direitos identificados"""
        if not worker_rights:
            return "Não identificado"
        
        # Pegar o direito com maior confiança
        main_right = max(worker_rights, key=lambda r: r.confidence)
        return main_right.description
    
    def _extract_monetary_values(self, entities: List) -> List[Dict]:
        """Extrai valores monetários das entidades"""
        monetary_values = []
        for entity in entities:
            if entity.label == 'MONEY':
                monetary_values.append({
                    'text': entity.text,
                    'confidence': entity.confidence
                })
        return monetary_values
    
    def _extract_legal_basis(self, entities: List) -> List[Dict]:
        """Extrai base legal das entidades"""
        legal_basis = []
        for entity in entities:
            if entity.label == 'LAW':
                legal_basis.append({
                    'text': entity.text,
                    'confidence': entity.confidence
                })
        return legal_basis
    
    def processar_lote_nlp(self, pipeline, limit: int = 50) -> Dict[str, Any]:
        """
        Processa um lote de textos através do pipeline NLP
        
        Args:
            pipeline: Instância do pipeline NLP
            limit: Número máximo de processos para processar
            
        Returns:
            Estatísticas do processamento
        """
        try:
            # Buscar processos não processados
            processos = self.get_processos_nao_processados(limit)
            
            if not processos:
                return {'message': 'Nenhum processo para processar'}
            
            sucessos = 0
            erros = 0
            
            for processo in processos:
                if self.processar_texto_nlp(processo.id if processo.id else 0, pipeline):
                    sucessos += 1
                else:
                    erros += 1
            
            # Calcular estatísticas
            estatisticas = {
                'total_processos': len(processos),
                'sucessos': sucessos,
                'erros': erros,
                'taxa_sucesso': sucessos / len(processos) if processos else 0
            }
            
            self.log_operation(
                "lote_nlp_processado",
                **estatisticas
            )
            
            return estatisticas
            
        except Exception as e:
            self.log_error(e, "processar_lote_nlp")
            return {'error': str(e)}
    
    def get_nlp_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas avançadas de NLP"""
        with self.get_connection() as conn:
            stats = {}
            
            # Total de processos no banco
            cursor = conn.execute('SELECT COUNT(*) as total FROM processos_judiciais')
            total_processos = cursor.fetchone()['total']
            stats['total_processos'] = total_processos
            
            # Estatísticas básicas de NLP
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_resultados,
                    AVG(qualidade_texto) as qualidade_media,
                    AVG(confianca_global) as confianca_media,
                    AVG(tempo_processamento) as tempo_medio,
                    MIN(data_processamento) as primeiro_processamento,
                    MAX(data_processamento) as ultimo_processamento
                FROM resultados_nlp
            ''')
            
            row = cursor.fetchone()
            if row:
                stats['processos_com_nlp'] = row['total_resultados']
                stats['qualidade_media'] = row['qualidade_media'] or 0
                stats['confianca_media'] = row['confianca_media'] or 0
                stats['tempo_medio'] = row['tempo_medio'] or 0
                stats['primeiro_processamento'] = row['primeiro_processamento']
                stats['ultimo_processamento'] = row['ultimo_processamento']
            else:
                stats['processos_com_nlp'] = 0
                stats['qualidade_media'] = 0
                stats['confianca_media'] = 0
                stats['tempo_medio'] = 0
                stats['primeiro_processamento'] = None
                stats['ultimo_processamento'] = None
            
            # Taxa de cobertura
            if total_processos > 0:
                stats['taxa_cobertura'] = (stats['processos_com_nlp'] / total_processos) * 100
            else:
                stats['taxa_cobertura'] = 0
            
            # Temas mais comuns
            cursor = conn.execute('''
                SELECT tema_principal, COUNT(*) as count
                FROM resultados_nlp
                WHERE tema_principal IS NOT NULL AND tema_principal != 'Não identificado'
                GROUP BY tema_principal
                ORDER BY count DESC
                LIMIT 10
            ''')
            stats['temas_comuns'] = [(row['tema_principal'], row['count']) for row in cursor.fetchall()]
            
            # Distribuição por tribunal
            cursor = conn.execute('''
                SELECT p.tribunal, COUNT(*) as count
                FROM resultados_nlp r
                JOIN processos_judiciais p ON r.processo_id = p.id
                WHERE p.tribunal IS NOT NULL
                GROUP BY p.tribunal
                ORDER BY count DESC
                LIMIT 10
            ''')
            stats['tribunais_distribuicao'] = [(row['tribunal'], row['count']) for row in cursor.fetchall()]
            
            # Distribuição de métodos de sumarização
            cursor = conn.execute('''
                SELECT metodo_sumarizacao, COUNT(*) as count
                FROM resultados_nlp
                GROUP BY metodo_sumarizacao
            ''')
            stats['metodos_sumarizacao'] = {row['metodo_sumarizacao']: row['count'] for row in cursor.fetchall()}
            
            # Distribuição de qualidade
            cursor = conn.execute('''
                SELECT 
                    SUM(CASE WHEN qualidade_texto >= 0.8 THEN 1 ELSE 0 END) as alta_qualidade,
                    SUM(CASE WHEN qualidade_texto >= 0.5 AND qualidade_texto < 0.8 THEN 1 ELSE 0 END) as media_qualidade,
                    SUM(CASE WHEN qualidade_texto < 0.5 THEN 1 ELSE 0 END) as baixa_qualidade
                FROM resultados_nlp
            ''')
            
            row = cursor.fetchone()
            if row:
                stats['distribuicao_qualidade'] = dict(row)
            
            return stats
    
    def export_nlp_results(self, output_path: str = "data/nlp_results.json") -> str:
        """
        Exporta resultados NLP para arquivo JSON
        
        Args:
            output_path: Caminho do arquivo de saída
            
        Returns:
            Caminho do arquivo criado ou JSON string
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        p.numero_processo,
                        p.tribunal,
                        p.data_publicacao,
                        r.resumo_extrativo,
                        r.palavras_chave,
                        r.tema_principal,
                        r.entidades_nomeadas,
                        r.direitos_trabalhistas,
                        r.valores_monetarios,
                        r.qualidade_texto,
                        r.confianca_global,
                        r.data_processamento
                    FROM resultados_nlp r
                    JOIN processos_judiciais p ON r.processo_id = p.id
                    ORDER BY r.data_processamento DESC
                ''')
                
                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    
                    # Converter campos JSON
                    for field in ['palavras_chave', 'entidades_nomeadas', 'direitos_trabalhistas', 'valores_monetarios']:
                        if result[field]:
                            try:
                                result[field] = json.loads(result[field])
                            except json.JSONDecodeError:
                                result[field] = []
                    
                    results.append(result)
                
                export_data = {
                    'metadata': {
                        'export_date': datetime.now().isoformat(),
                        'total_records': len(results),
                        'version': '1.0.0'
                    },
                    'results': results
                }
                
                json_string = json.dumps(export_data, ensure_ascii=False, indent=2)
                
                if output_path:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(json_string)
                    
                    self.log_operation(
                        "nlp_results_exported",
                        output_path=output_path,
                        total_records=len(results)
                    )
                    
                    return output_path
                
                return json_string
                
        except Exception as e:
            self.log_error(e, "export_nlp_results")
            raise
    
    def processar_texto_nlp_enhanced(self, processo_id: int, pipeline) -> bool:
        """
        Processa um texto específico através do pipeline NLP aprimorado
        
        Args:
            processo_id: ID do processo
            pipeline: Instância do pipeline NLP
            
        Returns:
            True se processado com sucesso, False caso contrário
        """
        try:
            # Buscar processo
            processo = self.get_processo_by_id(processo_id)
            if not processo:
                return False
            
            # Verificar se já foi processado
            if processo.processado_nlp:
                return True
            
            # Preparar referências legislativas existentes
            existing_references = []
            if processo.referencia_legislativa:
                try:
                    existing_references = json.loads(processo.referencia_legislativa)
                except json.JSONDecodeError:
                    existing_references = []
            
            # Processar com pipeline aprimorado
            resultado_enhanced = pipeline.process_text_enhanced(
                processo.conteudo_bruto_decisao,
                str(processo_id),
                existing_parts=processo.partes,
                existing_references=existing_references
            )
            
            # Criar objeto ResultadoNLP com dados aprimorados
            resultado_db = ResultadoNLP(
                processo_id=processo_id,
                texto_processado=resultado_enhanced['text_quality'].get('processed_text', ''),
                resumo_extrativo=resultado_enhanced.get('resumo_extrativo', ''),
                resumo_estruturado=json.dumps(resultado_enhanced.get('structured_summary', {}), ensure_ascii=False),
                palavras_chave=json.dumps(resultado_enhanced.get('palavras_chave', []), ensure_ascii=False),
                tema_principal=resultado_enhanced.get('tema_principal', 'Não identificado'),
                entidades_nomeadas=json.dumps(resultado_enhanced.get('entities', []), ensure_ascii=False),
                direitos_trabalhistas=json.dumps(resultado_enhanced.get('worker_rights', []), ensure_ascii=False),
                valores_monetarios=json.dumps(self._extract_monetary_values_enhanced(resultado_enhanced), ensure_ascii=False),
                base_legal=json.dumps(self._extract_legal_references_enhanced(resultado_enhanced), ensure_ascii=False),
                qualidade_texto=resultado_enhanced['text_quality'].get('quality_score', 0.0),
                confianca_global=resultado_enhanced.get('confidence_score', 0.0),
                tempo_processamento=resultado_enhanced.get('processing_time', 0.0),
                metodo_sumarizacao='enhanced_structured',
                versao_pipeline='2.0.0',
                metadados_nlp=json.dumps({
                    **resultado_enhanced,
                    'resultado_principal': resultado_enhanced.get('resultado_principal', 'Resultado não identificado'),
                    'partes_formatadas': resultado_enhanced.get('partes_formatadas', ''),
                    'referencias_formatadas': resultado_enhanced.get('referencias_formatadas', '')
                }, ensure_ascii=False, default=str)
            )
            
            # Salvar resultado
            self.insert_resultado_nlp(resultado_db)
            
            # Marcar processo como processado
            self.update_processo_processado(processo_id)
            
            return True
            
        except Exception as e:
            self.log_error(e, "processar_texto_nlp_enhanced", processo_id=processo_id)
            return False
    
    def _extract_monetary_values_enhanced(self, resultado_enhanced: Dict) -> List[Dict]:
        """Extrai valores monetários do resultado aprimorado"""
        monetary_values = []
        
        # Valores do resumo estruturado
        structured_summary = resultado_enhanced.get('structured_summary', {})
        valores_envolvidos = structured_summary.get('valores_envolvidos', [])
        
        for valor in valores_envolvidos:
            monetary_values.append({
                'text': valor.get('text', ''),
                'numeric_value': valor.get('numeric_value'),
                'context': valor.get('context', ''),
                'confidence': 0.9
            })
        
        # Valores das entidades (fallback)
        entities = resultado_enhanced.get('entities', [])
        for entity in entities:
            if entity.get('label') == 'MONEY':
                monetary_values.append({
                    'text': entity.get('text', ''),
                    'confidence': entity.get('confidence', 0.8)
                })
        
        return monetary_values
    
    def _extract_legal_references_enhanced(self, resultado_enhanced: Dict) -> List[Dict]:
        """Extrai referências legais do resultado aprimorado"""
        legal_refs = []
        
        # Referências do extrator
        legal_references = resultado_enhanced.get('legal_references', {})
        references = legal_references.get('references', [])
        
        for ref in references:
            legal_refs.append({
                'text': ref.get('text', ''),
                'type': ref.get('type', ''),
                'source': ref.get('source', ''),
                'confidence': ref.get('confidence', 0.8)
            })
        
        # Referências das entidades (fallback)
        entities = resultado_enhanced.get('entities', [])
        for entity in entities:
            if entity.get('label') == 'LAW':
                legal_refs.append({
                    'text': entity.get('text', ''),
                    'type': 'law',
                    'confidence': entity.get('confidence', 0.7)
                })
        
        return legal_refs