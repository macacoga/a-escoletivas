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
    partes: str = ""
    link_decisao: str = ""
    conteudo_bruto_decisao: str = ""
    origem_texto: str = ""
    colecao_api: str = ""
    id_documento_api: str = ""
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
            'partes': self.partes,
            'link_decisao': self.link_decisao,
            'conteudo_bruto_decisao': self.conteudo_bruto_decisao,
            'origem_texto': self.origem_texto,
            'colecao_api': self.colecao_api,
            'id_documento_api': self.id_documento_api,
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
    resumo_extrativo: str = ""
    palavras_chave: str = ""  # JSON string com lista de palavras-chave
    tema_principal: str = ""
    sentimento: str = ""
    entidades_nomeadas: str = ""  # JSON string com entidades identificadas
    metadados_nlp: str = ""  # JSON string com metadados do processamento
    data_processamento: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'processo_id': self.processo_id,
            'resumo_extrativo': self.resumo_extrativo,
            'palavras_chave': self.palavras_chave,
            'tema_principal': self.tema_principal,
            'sentimento': self.sentimento,
            'entidades_nomeadas': self.entidades_nomeadas,
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