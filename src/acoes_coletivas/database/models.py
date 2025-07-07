"""
Modelos de dados para o banco SQLite
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import json


@dataclass
class ProcessoJudicial:
    """
    Modelo para representar um processo judicial
    """
    id: Optional[int] = None
    numero_processo: str = ""
    numero_processo_planilha: str = ""
    tribunal: str = ""
    classe_processo: str = ""
    tipo_documento: str = ""
    data_julgamento: Optional[str] = None
    data_publicacao: Optional[str] = None
    relator: str = ""
    redator: str = ""
    partes: str = ""
    link_decisao: str = ""
    conteudo_bruto_decisao: str = ""
    origem_texto: str = ""
    colecao_api: str = ""
    id_documento_api: str = ""
    referencia_legislativa: str = ""  # JSON string para armazenar a lista
    processado_nlp: bool = False
    data_coleta: datetime = field(default_factory=datetime.now)
    data_processamento: Optional[datetime] = None
    metadados: str = ""  # JSON string para metadados adicionais
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'numero_processo': self.numero_processo,
            'numero_processo_planilha': self.numero_processo_planilha,
            'tribunal': self.tribunal,
            'classe_processo': self.classe_processo,
            'tipo_documento': self.tipo_documento,
            'data_julgamento': self.data_julgamento,
            'data_publicacao': self.data_publicacao,
            'relator': self.relator,
            'redator': self.redator,
            'partes': self.partes,
            'link_decisao': self.link_decisao,
            'conteudo_bruto_decisao': self.conteudo_bruto_decisao,
            'origem_texto': self.origem_texto,
            'colecao_api': self.colecao_api,
            'id_documento_api': self.id_documento_api,
            'referencia_legislativa': self.referencia_legislativa,
            'processado_nlp': self.processado_nlp,
            'data_coleta': self.data_coleta.isoformat() if self.data_coleta else None,
            'data_processamento': self.data_processamento.isoformat() if self.data_processamento else None,
            'metadados': self.metadados
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessoJudicial':
        """Cria objeto a partir de dicionário"""
        # Converter strings de data para datetime
        if data.get('data_coleta') and isinstance(data['data_coleta'], str):
            data['data_coleta'] = datetime.fromisoformat(data['data_coleta'])
        if data.get('data_processamento') and isinstance(data['data_processamento'], str):
            data['data_processamento'] = datetime.fromisoformat(data['data_processamento'])
        
        return cls(**data)


@dataclass
class ResultadoNLP:
    """
    Modelo para armazenar resultados do processamento NLP
    """
    id: Optional[int] = None
    processo_id: int = 0
    texto_processado: str = ""
    resumo_extrativo: str = ""
    resumo_estruturado: str = ""  # JSON string com resumo por seções
    palavras_chave: str = ""  # JSON string com lista de palavras-chave
    tema_principal: str = ""
    entidades_nomeadas: str = ""  # JSON string com entidades identificadas
    direitos_trabalhistas: str = ""  # JSON string com direitos identificados
    valores_monetarios: str = ""  # JSON string com valores extraídos
    base_legal: str = ""  # JSON string com base legal identificada
    qualidade_texto: float = 0.0
    confianca_global: float = 0.0
    tempo_processamento: float = 0.0
    metodo_sumarizacao: str = ""
    versao_pipeline: str = "1.0.0"
    metadados_nlp: str = ""  # JSON string com metadados do processamento
    data_processamento: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'processo_id': self.processo_id,
            'texto_processado': self.texto_processado,
            'resumo_extrativo': self.resumo_extrativo,
            'resumo_estruturado': self.resumo_estruturado,
            'palavras_chave': self.palavras_chave,
            'tema_principal': self.tema_principal,
            'entidades_nomeadas': self.entidades_nomeadas,
            'direitos_trabalhistas': self.direitos_trabalhistas,
            'valores_monetarios': self.valores_monetarios,
            'base_legal': self.base_legal,
            'qualidade_texto': self.qualidade_texto,
            'confianca_global': self.confianca_global,
            'tempo_processamento': self.tempo_processamento,
            'metodo_sumarizacao': self.metodo_sumarizacao,
            'versao_pipeline': self.versao_pipeline,
            'metadados_nlp': self.metadados_nlp,
            'data_processamento': self.data_processamento.isoformat() if self.data_processamento else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResultadoNLP':
        """Cria objeto a partir de dicionário"""
        if data.get('data_processamento') and isinstance(data['data_processamento'], str):
            data['data_processamento'] = datetime.fromisoformat(data['data_processamento'])
        
        return cls(**data)


@dataclass
class EstatisticasNLP:
    """
    Modelo para armazenar estatísticas de processamento NLP
    """
    id: Optional[int] = None
    data_analise: datetime = field(default_factory=datetime.now)
    total_processos: int = 0
    processos_com_nlp: int = 0
    tempo_processamento_medio: float = 0.0
    qualidade_media: float = 0.0
    confianca_media: float = 0.0
    entidades_mais_comuns: str = ""  # JSON string
    direitos_mais_comuns: str = ""  # JSON string
    tribunais_distribuicao: str = ""  # JSON string
    valores_estatisticas: str = ""  # JSON string com estatísticas de valores
    metadados_estatisticas: str = ""  # JSON string com metadados adicionais
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'data_analise': self.data_analise.isoformat() if self.data_analise else None,
            'total_processos': self.total_processos,
            'processos_com_nlp': self.processos_com_nlp,
            'tempo_processamento_medio': self.tempo_processamento_medio,
            'qualidade_media': self.qualidade_media,
            'confianca_media': self.confianca_media,
            'entidades_mais_comuns': self.entidades_mais_comuns,
            'direitos_mais_comuns': self.direitos_mais_comuns,
            'tribunais_distribuicao': self.tribunais_distribuicao,
            'valores_estatisticas': self.valores_estatisticas,
            'metadados_estatisticas': self.metadados_estatisticas
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EstatisticasNLP':
        """Cria objeto a partir de dicionário"""
        if data.get('data_analise') and isinstance(data['data_analise'], str):
            data['data_analise'] = datetime.fromisoformat(data['data_analise'])
        
        return cls(**data)


@dataclass
class LogExecucao:
    """
    Modelo para logs de execução
    """
    id: Optional[int] = None
    operacao: str = ""
    status: str = ""  # 'success', 'error', 'warning'
    mensagem: str = ""
    detalhes: str = ""  # JSON string com detalhes adicionais
    tempo_execucao: float = 0.0
    data_execucao: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'operacao': self.operacao,
            'status': self.status,
            'mensagem': self.mensagem,
            'detalhes': self.detalhes,
            'tempo_execucao': self.tempo_execucao,
            'data_execucao': self.data_execucao.isoformat() if self.data_execucao else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogExecucao':
        """Cria objeto a partir de dicionário"""
        if data.get('data_execucao') and isinstance(data['data_execucao'], str):
            data['data_execucao'] = datetime.fromisoformat(data['data_execucao'])
        
        return cls(**data) 