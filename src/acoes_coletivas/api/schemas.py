"""
Schemas Marshmallow para serialização de dados da API
"""

from marshmallow import Schema, fields, post_load, validate, ValidationError
from typing import Dict, Any, List
import json


class PaginationSchema(Schema):
    """Schema para metadados de paginação"""
    page = fields.Integer(required=True, validate=validate.Range(min=1))
    per_page = fields.Integer(required=True, validate=validate.Range(min=1, max=100))
    total = fields.Integer(required=True)
    pages = fields.Integer(required=True)
    has_next = fields.Boolean(required=True)
    has_prev = fields.Boolean(required=True)
    next_page = fields.Integer(allow_none=True)
    prev_page = fields.Integer(allow_none=True)


class ProcessoJudicialResumoSchema(Schema):
    """Schema resumido para listagem de processos"""
    id = fields.Integer(required=True)
    numero_processo = fields.String(required=True)
    numero_processo_planilha = fields.String(required=True)
    tribunal = fields.String(required=True)
    classe_processo = fields.String(allow_none=True)
    data_julgamento = fields.String(allow_none=True)
    data_publicacao = fields.String(allow_none=True)
    partes = fields.String(allow_none=True)
    processado_nlp = fields.Boolean(required=True)
    data_coleta = fields.DateTime(required=True, format='iso')
    
    # Campos do NLP (se disponível)
    tema_principal = fields.String(allow_none=True)
    qualidade_texto = fields.Float(allow_none=True)
    confianca_global = fields.Float(allow_none=True)


class EntitySchema(Schema):
    """Schema para entidades nomeadas"""
    text = fields.String(required=True)
    label = fields.String(required=True)
    start = fields.Integer(required=True)
    end = fields.Integer(required=True)
    confidence = fields.Float(required=True)
    description = fields.String(required=True)


class WorkerRightSchema(Schema):
    """Schema para direitos trabalhistas"""
    type = fields.String(required=True)
    description = fields.String(required=True)
    mentions = fields.List(fields.String(), required=True)
    decision_outcome = fields.String(allow_none=True, validate=validate.OneOf(['granted', 'denied', 'partially_granted']))
    confidence = fields.Float(required=True)


class MonetaryValueSchema(Schema):
    """Schema para valores monetários"""
    text = fields.String(required=True)
    confidence = fields.Float(required=True)


class ResultadoNLPSchema(Schema):
    """Schema para resultados de NLP"""
    id = fields.Integer(required=True)
    processo_id = fields.Integer(required=True)
    resumo_extrativo = fields.String(allow_none=True)
    tema_principal = fields.String(allow_none=True)
    qualidade_texto = fields.Float(required=True)
    confianca_global = fields.Float(required=True)
    tempo_processamento = fields.Float(required=True)
    metodo_sumarizacao = fields.String(allow_none=True)
    data_processamento = fields.DateTime(required=True, format='iso')
    
    # Campos JSON deserializados
    entidades = fields.List(fields.Nested(EntitySchema), dump_only=True)
    direitos_trabalhistas = fields.List(fields.Nested(WorkerRightSchema), dump_only=True)
    valores_monetarios = fields.List(fields.Nested(MonetaryValueSchema), dump_only=True)
    resumo_estruturado = fields.Dict(dump_only=True)
    
    @post_load
    def deserialize_json_fields(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Deserializa campos JSON para objetos Python"""
        
        # Deserializar entidades
        if 'entidades_nomeadas' in data and data['entidades_nomeadas']:
            try:
                entidades_data = json.loads(data['entidades_nomeadas'])
                data['entidades'] = entidades_data
            except (json.JSONDecodeError, TypeError):
                data['entidades'] = []
        
        # Deserializar direitos
        if 'direitos_trabalhistas' in data and data['direitos_trabalhistas']:
            try:
                direitos_data = json.loads(data['direitos_trabalhistas'])
                data['direitos_trabalhistas'] = direitos_data
            except (json.JSONDecodeError, TypeError):
                data['direitos_trabalhistas'] = []
        
        # Deserializar valores monetários
        if 'valores_monetarios' in data and data['valores_monetarios']:
            try:
                valores_data = json.loads(data['valores_monetarios'])
                data['valores_monetarios'] = valores_data
            except (json.JSONDecodeError, TypeError):
                data['valores_monetarios'] = []
        
        # Deserializar resumo estruturado
        if 'resumo_estruturado' in data and data['resumo_estruturado']:
            try:
                resumo_data = json.loads(data['resumo_estruturado'])
                data['resumo_estruturado'] = resumo_data
            except (json.JSONDecodeError, TypeError):
                data['resumo_estruturado'] = {}
        
        return data


class ProcessoJudicialDetalhadoSchema(Schema):
    """Schema detalhado para processo individual"""
    id = fields.Integer(required=True)
    numero_processo = fields.String(required=True)
    numero_processo_planilha = fields.String(required=True)
    tribunal = fields.String(required=True)
    classe_processo = fields.String(allow_none=True)
    tipo_documento = fields.String(allow_none=True)
    data_julgamento = fields.String(allow_none=True)
    data_publicacao = fields.String(allow_none=True)
    relator = fields.String(allow_none=True)
    partes = fields.String(allow_none=True)
    link_decisao = fields.String(allow_none=True)
    origem_texto = fields.String(allow_none=True)
    processado_nlp = fields.Boolean(required=True)
    data_coleta = fields.DateTime(required=True, format='iso')
    data_processamento = fields.DateTime(allow_none=True, format='iso')
    
    # Conteúdo da decisão (opcional para economizar bandwidth)
    conteudo_bruto_decisao = fields.String(allow_none=True, missing=None)
    
    # Resultados de NLP
    resultado_nlp = fields.Nested(ResultadoNLPSchema, allow_none=True)


class ProcessosListagemSchema(Schema):
    """Schema para listagem paginada de processos"""
    data = fields.List(fields.Nested(ProcessoJudicialResumoSchema), required=True)
    pagination = fields.Nested(PaginationSchema, required=True)
    total_found = fields.Integer(required=True)
    filters_applied = fields.Dict(required=True)


class SearchFiltersSchema(Schema):
    """Schema para filtros de busca"""
    # Parâmetros de paginação
    page = fields.Integer(missing=1, validate=validate.Range(min=1))
    per_page = fields.Integer(missing=20, validate=validate.Range(min=1, max=100))
    
    # Filtros de busca
    numero_processo = fields.String(allow_none=True)
    tribunal = fields.String(allow_none=True)
    partes = fields.String(allow_none=True)
    keywords = fields.String(allow_none=True)
    
    # Filtros de data
    data_publicacao_inicio = fields.Date(allow_none=True)
    data_publicacao_fim = fields.Date(allow_none=True)
    data_julgamento_inicio = fields.Date(allow_none=True)
    data_julgamento_fim = fields.Date(allow_none=True)
    
    # Filtros de NLP
    processado_nlp = fields.Boolean(allow_none=True)
    tema_principal = fields.String(allow_none=True)
    qualidade_minima = fields.Float(allow_none=True, validate=validate.Range(min=0, max=1))
    confianca_minima = fields.Float(allow_none=True, validate=validate.Range(min=0, max=1))
    
    # Filtros de direitos trabalhistas
    direito_trabalhista = fields.String(allow_none=True)
    resultado_decisao = fields.String(allow_none=True, validate=validate.OneOf(['granted', 'denied', 'partially_granted']))
    
    # Ordenação
    sort_by = fields.String(allow_none=True, validate=validate.OneOf([
        'data_publicacao', 'data_julgamento', 'data_coleta', 
        'numero_processo', 'qualidade_texto', 'confianca_global'
    ]))
    sort_order = fields.String(missing='desc', validate=validate.OneOf(['asc', 'desc']))
    
    # Incluir conteúdo completo?
    include_content = fields.Boolean(missing=False)


class TopicoSchema(Schema):
    """Schema para tópicos/temas"""
    nome = fields.String(required=True)
    descricao = fields.String(required=True)
    frequencia = fields.Integer(required=True)
    porcentagem = fields.Float(required=True)
    exemplos = fields.List(fields.String(), required=True)


class TopicosListagemSchema(Schema):
    """Schema para listagem de tópicos"""
    temas_principais = fields.List(fields.Nested(TopicoSchema), required=True)
    direitos_trabalhistas = fields.List(fields.Nested(TopicoSchema), required=True)
    tribunais = fields.List(fields.Nested(TopicoSchema), required=True)
    total_processos_analisados = fields.Integer(required=True)
    data_analise = fields.DateTime(required=True, format='iso')


class EstatisticasSchema(Schema):
    """Schema para estatísticas gerais"""
    total_processos = fields.Integer(required=True)
    processos_processados = fields.Integer(required=True)
    resultados_nlp = fields.Integer(required=True)
    tribunais_unicos = fields.Integer(required=True)
    ultima_coleta = fields.String(allow_none=True)
    
    # Estatísticas de NLP
    qualidade_media = fields.Float(allow_none=True)
    confianca_media = fields.Float(allow_none=True)
    tempo_processamento_medio = fields.Float(allow_none=True)
    
    # Distribuições
    distribuicao_tribunais = fields.Dict(allow_none=True)
    distribuicao_qualidade = fields.Dict(allow_none=True)
    direitos_mais_comuns = fields.Dict(allow_none=True)
    
    data_analise = fields.DateTime(required=True, format='iso')


class ErrorResponseSchema(Schema):
    """Schema para respostas de erro"""
    error = fields.String(required=True)
    message = fields.String(required=True)
    status = fields.Integer(required=True)
    timestamp = fields.DateTime(required=True, format='iso')
    details = fields.Dict(allow_none=True)


class SuccessResponseSchema(Schema):
    """Schema para respostas de sucesso"""
    success = fields.Boolean(required=True)
    message = fields.String(required=True)
    data = fields.Dict(allow_none=True)
    timestamp = fields.DateTime(required=True, format='iso')


# Instâncias dos schemas para reutilização
pagination_schema = PaginationSchema()
processo_resumo_schema = ProcessoJudicialResumoSchema()
processos_resumo_schema = ProcessoJudicialResumoSchema(many=True)
processo_detalhado_schema = ProcessoJudicialDetalhadoSchema()
processos_listagem_schema = ProcessosListagemSchema()
search_filters_schema = SearchFiltersSchema()
topicos_listagem_schema = TopicosListagemSchema()
estatisticas_schema = EstatisticasSchema()
error_response_schema = ErrorResponseSchema()
success_response_schema = SuccessResponseSchema() 