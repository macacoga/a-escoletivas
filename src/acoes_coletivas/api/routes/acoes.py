"""
Endpoints da API para ações coletivas
"""

from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from marshmallow import ValidationError
from typing import Dict, Any, List, Optional
import math
from datetime import datetime
from sqlalchemy import text, or_, and_, func
from sqlalchemy.orm import sessionmaker, joinedload

from ...database.manager import DatabaseManager
from ...database.models import ProcessoJudicial, ResultadoNLP
from ...utils.logging import get_logger
from ..schemas import (
    search_filters_schema,
    processo_detalhado_schema,
    processos_listagem_schema,
    error_response_schema
)
from ..app import get_database


# Configurar namespace
acoes_ns = Namespace('acoes', description='Endpoints para ações coletivas')

# Modelos para documentação da API
pagination_model = acoes_ns.model('Pagination', {
    'page': fields.Integer(required=True, description='Página atual'),
    'per_page': fields.Integer(required=True, description='Itens por página'),
    'total': fields.Integer(required=True, description='Total de itens'),
    'pages': fields.Integer(required=True, description='Total de páginas'),
    'has_next': fields.Boolean(required=True, description='Tem próxima página'),
    'has_prev': fields.Boolean(required=True, description='Tem página anterior')
})

processo_resumo_model = acoes_ns.model('ProcessoResumo', {
    'id': fields.Integer(required=True, description='ID do processo'),
    'numero_processo': fields.String(required=True, description='Número do processo'),
    'tribunal': fields.String(required=True, description='Tribunal'),
    'data_publicacao': fields.String(description='Data de publicação'),
    'partes': fields.String(description='Partes envolvidas'),
    'processado_nlp': fields.Boolean(required=True, description='Processado pelo NLP'),
    'tema_principal': fields.String(description='Tema principal identificado'),
    'qualidade_texto': fields.Float(description='Qualidade do texto (0-1)'),
    'confianca_global': fields.Float(description='Confiança global (0-1)')
})

processos_lista_model = acoes_ns.model('ProcessosLista', {
    'data': fields.List(fields.Nested(processo_resumo_model), required=True, description='Lista de processos'),
    'pagination': fields.Nested(pagination_model, required=True, description='Informações de paginação'),
    'total_found': fields.Integer(required=True, description='Total de processos encontrados'),
    'filters_applied': fields.Raw(description='Filtros aplicados')
})

logger = get_logger("API.Acoes")


@acoes_ns.route('')
class AcoesListResource(Resource):
    """Listar todas as ações coletivas processadas"""
    
    @acoes_ns.doc('listar_acoes')
    @acoes_ns.expect(acoes_ns.parser()
                    .add_argument('page', type=int, default=1, help='Página (padrão: 1)')
                    .add_argument('per_page', type=int, default=20, help='Itens por página (padrão: 20, max: 100)')
                    .add_argument('include_content', type=bool, default=False, help='Incluir conteúdo completo'))
    @acoes_ns.marshal_with(processos_lista_model)
    def get(self):
        """Listar ações coletivas com paginação"""
        try:
            # Parâmetros de paginação
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            include_content = request.args.get('include_content', False, type=bool)
            
            logger.info(f"Listando ações - página {page}, {per_page} por página")
            
            # Obter banco de dados
            db = get_database()
            
            # Buscar processos com paginação
            offset = (page - 1) * per_page
            
            # Query base
            query = f"""
                SELECT p.*, 
                       r.resumo_extrativo,
                       r.tema_principal,
                       r.qualidade_texto,
                       r.confianca_global
                FROM processos_judiciais p
                LEFT JOIN resultados_nlp r ON p.id = r.processo_id
                ORDER BY p.data_coleta DESC
                LIMIT {per_page} OFFSET {offset}
            """
            
            # Contar total
            count_query = "SELECT COUNT(*) as total FROM processos_judiciais"
            
            # Executar queries
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Buscar processos
                cursor.execute(query)
                rows = cursor.fetchall()
                
                # Contar total
                cursor.execute(count_query)
                total = cursor.fetchone()[0]
            
            # Construir resposta
            processos = []
            for row in rows:
                processo = {
                    'id': row[0],
                    'numero_processo': row[1],
                    'numero_processo_planilha': row[2],
                    'tribunal': row[3],
                    'classe_processo': row[4],
                    'tipo_documento': row[5],
                    'data_julgamento': row[6],
                    'data_publicacao': row[7],
                    'relator': row[8],
                    'partes': row[9],
                    'link_decisao': row[10],
                    'origem_texto': row[11],
                    'processado_nlp': bool(row[12]),
                    'data_coleta': row[13],
                    'data_processamento': row[14],
                    'tema_principal': row[16] if len(row) > 16 else None,
                    'qualidade_texto': row[17] if len(row) > 17 else None,
                    'confianca_global': row[18] if len(row) > 18 else None
                }
                
                # Incluir conteúdo se solicitado
                if include_content:
                    processo['conteudo_bruto_decisao'] = row[15] if len(row) > 15 else None
                
                processos.append(processo)
            
            # Metadados de paginação
            total_pages = math.ceil(total / per_page)
            
            response_data = {
                'data': processos,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1,
                    'next_page': page + 1 if page < total_pages else None,
                    'prev_page': page - 1 if page > 1 else None
                },
                'total_found': total,
                'filters_applied': {
                    'include_content': include_content
                }
            }
            
            logger.info(f"Retornando {len(processos)} processos (página {page}/{total_pages})")
            return response_data
            
        except Exception as e:
            logger.error(f"Erro ao listar ações: {e}")
            acoes_ns.abort(500, f"Erro interno: {str(e)}")


@acoes_ns.route('/<int:processo_id>')
class AcaoResource(Resource):
    """Obter detalhes de uma ação específica"""
    
    @acoes_ns.doc('obter_acao')
    @acoes_ns.expect(acoes_ns.parser()
                    .add_argument('include_content', type=bool, default=True, help='Incluir conteúdo completo'))
    def get(self, processo_id: int):
        """Obter detalhes completos de uma ação coletiva"""
        try:
            include_content = request.args.get('include_content', True, type=bool)
            
            logger.info(f"Buscando processo {processo_id}")
            
            # Obter banco de dados
            db = get_database()
            
            # Buscar processo específico
            query = f"""
                SELECT p.*, 
                       r.id as nlp_id,
                       r.resumo_extrativo,
                       r.tema_principal,
                       r.qualidade_texto,
                       r.confianca_global,
                       r.tempo_processamento,
                       r.metodo_sumarizacao,
                       r.data_processamento as nlp_data_processamento,
                       r.texto_processado,
                       r.entidades_nomeadas,
                       r.direitos_trabalhistas,
                       r.valores_monetarios,
                       r.resumo_estruturado,
                       r.base_legal
                FROM processos_judiciais p
                LEFT JOIN resultados_nlp r ON p.id = r.processo_id
                WHERE p.id = {processo_id}
            """
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                row = cursor.fetchone()
            
            if not row:
                acoes_ns.abort(404, f"Processo {processo_id} não encontrado")
            
            # Construir resposta detalhada
            processo = {
                'id': row[0],
                'numero_processo': row[1],
                'numero_processo_planilha': row[2],
                'tribunal': row[3],
                'classe_processo': row[4],
                'tipo_documento': row[5],
                'data_julgamento': row[6],
                'data_publicacao': row[7],
                'relator': row[8],
                'partes': row[9],
                'link_decisao': row[10],
                'origem_texto': row[11],
                'processado_nlp': bool(row[12]),
                'data_coleta': row[13],
                'data_processamento': row[14]
            }
            
            # Incluir conteúdo se solicitado
            if include_content:
                processo['conteudo_bruto_decisao'] = row[15]
            
            # Adicionar resultados NLP se disponíveis
            if row[16]:  # nlp_id
                import json
                
                processo['resultado_nlp'] = {
                    'id': row[16],
                    'processo_id': processo_id,
                    'resumo_extrativo': row[17],
                    'tema_principal': row[18],
                    'qualidade_texto': row[19],
                    'confianca_global': row[20],
                    'tempo_processamento': row[21],
                    'metodo_sumarizacao': row[22],
                    'data_processamento': row[23],
                    'texto_processado': row[24] if include_content else None,
                    'entidades': [],
                    'direitos_trabalhistas': [],
                    'valores_monetarios': [],
                    'resumo_estruturado': {},
                    'base_legal': row[28]
                }
                
                # Deserializar campos JSON
                try:
                    if row[25]:  # entidades_nomeadas
                        processo['resultado_nlp']['entidades'] = json.loads(row[25])
                except (json.JSONDecodeError, TypeError):
                    pass
                
                try:
                    if row[26]:  # direitos_trabalhistas
                        processo['resultado_nlp']['direitos_trabalhistas'] = json.loads(row[26])
                except (json.JSONDecodeError, TypeError):
                    pass
                
                try:
                    if row[27]:  # valores_monetarios
                        processo['resultado_nlp']['valores_monetarios'] = json.loads(row[27])
                except (json.JSONDecodeError, TypeError):
                    pass
                
                try:
                    if row[28]:  # resumo_estruturado
                        processo['resultado_nlp']['resumo_estruturado'] = json.loads(row[28])
                except (json.JSONDecodeError, TypeError):
                    pass
            
            logger.info(f"Processo {processo_id} encontrado")
            return processo
            
        except Exception as e:
            logger.error(f"Erro ao buscar processo {processo_id}: {e}")
            acoes_ns.abort(500, f"Erro interno: {str(e)}")


@acoes_ns.route('/search')
class AcoesSearchResource(Resource):
    """Buscar ações com filtros"""
    
    @acoes_ns.doc('buscar_acoes')
    @acoes_ns.expect(acoes_ns.parser()
                    .add_argument('page', type=int, default=1, help='Página')
                    .add_argument('per_page', type=int, default=20, help='Itens por página')
                    .add_argument('numero_processo', type=str, help='Número do processo')
                    .add_argument('tribunal', type=str, help='Tribunal')
                    .add_argument('partes', type=str, help='Partes envolvidas')
                    .add_argument('keywords', type=str, help='Palavras-chave')
                    .add_argument('data_publicacao_inicio', type=str, help='Data início (YYYY-MM-DD)')
                    .add_argument('data_publicacao_fim', type=str, help='Data fim (YYYY-MM-DD)')
                    .add_argument('processado_nlp', type=bool, help='Processado pelo NLP')
                    .add_argument('tema_principal', type=str, help='Tema principal')
                    .add_argument('qualidade_minima', type=float, help='Qualidade mínima (0-1)')
                    .add_argument('confianca_minima', type=float, help='Confiança mínima (0-1)')
                    .add_argument('direito_trabalhista', type=str, help='Direito trabalhista')
                    .add_argument('resultado_decisao', type=str, help='Resultado da decisão')
                    .add_argument('sort_by', type=str, help='Ordenar por')
                    .add_argument('sort_order', type=str, default='desc', help='Ordem (asc/desc)')
                    .add_argument('include_content', type=bool, default=False, help='Incluir conteúdo'))
    @acoes_ns.marshal_with(processos_lista_model)
    def get(self):
        """Buscar ações coletivas com filtros avançados"""
        try:
            # Validar parâmetros
            try:
                filters = search_filters_schema.load(request.args)
            except ValidationError as e:
                acoes_ns.abort(400, f"Parâmetros inválidos: {e.messages}")
            
            logger.info(f"Buscando ações com filtros: {filters}")
            
            # Obter banco de dados
            db = get_database()
            
            # Construir query dinamicamente
            where_conditions = []
            params = []
            
            # Filtros básicos
            if filters.get('numero_processo'):
                where_conditions.append("p.numero_processo LIKE ?")
                params.append(f"%{filters['numero_processo']}%")
            
            if filters.get('tribunal'):
                where_conditions.append("p.tribunal LIKE ?")
                params.append(f"%{filters['tribunal']}%")
            
            if filters.get('partes'):
                where_conditions.append("p.partes LIKE ?")
                params.append(f"%{filters['partes']}%")
            
            # Filtros de data
            if filters.get('data_publicacao_inicio'):
                where_conditions.append("p.data_publicacao >= ?")
                params.append(filters['data_publicacao_inicio'])
            
            if filters.get('data_publicacao_fim'):
                where_conditions.append("p.data_publicacao <= ?")
                params.append(filters['data_publicacao_fim'])
            
            # Filtros de NLP
            if filters.get('processado_nlp') is not None:
                where_conditions.append("p.processado_nlp = ?")
                params.append(filters['processado_nlp'])
            
            if filters.get('tema_principal'):
                where_conditions.append("r.tema_principal LIKE ?")
                params.append(f"%{filters['tema_principal']}%")
            
            if filters.get('qualidade_minima'):
                where_conditions.append("r.qualidade_texto >= ?")
                params.append(filters['qualidade_minima'])
            
            if filters.get('confianca_minima'):
                where_conditions.append("r.confianca_global >= ?")
                params.append(filters['confianca_minima'])
            
            # Filtros de palavras-chave (busca no conteúdo)
            if filters.get('keywords'):
                keywords = filters['keywords'].split()
                keyword_conditions = []
                for keyword in keywords:
                    keyword_conditions.append("(p.conteudo_bruto_decisao LIKE ? OR r.resumo_extrativo LIKE ?)")
                    params.extend([f"%{keyword}%", f"%{keyword}%"])
                
                if keyword_conditions:
                    where_conditions.append(f"({' OR '.join(keyword_conditions)})")
            
            # Construir WHERE clause
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Ordenação
            order_by = "ORDER BY p.data_coleta DESC"
            if filters.get('sort_by'):
                sort_field = filters['sort_by']
                sort_order = filters.get('sort_order', 'desc').upper()
                
                field_mapping = {
                    'data_publicacao': 'p.data_publicacao',
                    'data_julgamento': 'p.data_julgamento',
                    'data_coleta': 'p.data_coleta',
                    'numero_processo': 'p.numero_processo',
                    'qualidade_texto': 'r.qualidade_texto',
                    'confianca_global': 'r.confianca_global'
                }
                
                if sort_field in field_mapping:
                    order_by = f"ORDER BY {field_mapping[sort_field]} {sort_order}"
            
            # Paginação
            page = filters.get('page', 1)
            per_page = filters.get('per_page', 20)
            offset = (page - 1) * per_page
            
            # Query principal
            query = f"""
                SELECT p.*, 
                       r.resumo_extrativo,
                       r.tema_principal,
                       r.qualidade_texto,
                       r.confianca_global
                FROM processos_judiciais p
                LEFT JOIN resultados_nlp r ON p.id = r.processo_id
                {where_clause}
                {order_by}
                LIMIT {per_page} OFFSET {offset}
            """
            
            # Query de contagem
            count_query = f"""
                SELECT COUNT(*)
                FROM processos_judiciais p
                LEFT JOIN resultados_nlp r ON p.id = r.processo_id
                {where_clause}
            """
            
            # Executar queries
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Buscar processos
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Contar total
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
            
            # Construir resposta
            processos = []
            for row in rows:
                processo = {
                    'id': row[0],
                    'numero_processo': row[1],
                    'numero_processo_planilha': row[2],
                    'tribunal': row[3],
                    'classe_processo': row[4],
                    'tipo_documento': row[5],
                    'data_julgamento': row[6],
                    'data_publicacao': row[7],
                    'relator': row[8],
                    'partes': row[9],
                    'link_decisao': row[10],
                    'origem_texto': row[11],
                    'processado_nlp': bool(row[12]),
                    'data_coleta': row[13],
                    'data_processamento': row[14],
                    'tema_principal': row[16] if len(row) > 16 else None,
                    'qualidade_texto': row[17] if len(row) > 17 else None,
                    'confianca_global': row[18] if len(row) > 18 else None
                }
                
                # Incluir conteúdo se solicitado
                if filters.get('include_content'):
                    processo['conteudo_bruto_decisao'] = row[15]
                
                processos.append(processo)
            
            # Metadados de paginação
            total_pages = math.ceil(total / per_page)
            
            response_data = {
                'data': processos,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1,
                    'next_page': page + 1 if page < total_pages else None,
                    'prev_page': page - 1 if page > 1 else None
                },
                'total_found': total,
                'filters_applied': filters
            }
            
            logger.info(f"Busca retornou {len(processos)} processos de {total} total")
            return response_data
            
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            acoes_ns.abort(500, f"Erro interno: {str(e)}") 