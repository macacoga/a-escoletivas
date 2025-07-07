"""
Endpoints da API para ações coletivas
"""

from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from marshmallow import ValidationError
from typing import Dict, Any, List, Optional, cast
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
                       r.confianca_global,
                       r.palavras_chave,
                       r.entidades_nomeadas,
                       r.direitos_trabalhistas
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
                    'redator': row[9],
                    'partes': row[10],
                    'link_decisao': row[11],
                    'conteudo_bruto_decisao': row[12] if include_content else None,
                    'origem_texto': row[13],
                    'colecao_api': row[14],
                    'id_documento_api': row[15],
                    'referencia_legislativa': row[16],
                    'processado_nlp': bool(row[17]),
                    'data_coleta': row[18],
                    'data_processamento': row[19],
                    'metadados': row[20],
                    # Campos NLP básicos (começam na posição 21)
                    'tema_principal': row[22] if len(row) > 22 else None,
                    'qualidade_texto': row[23] if len(row) > 23 else None,
                    'confianca_global': row[24] if len(row) > 24 else None,
                    # Campos NLP avançados
                    'palavras_chave': row[25] if len(row) > 25 else None,
                    'entidades_nomeadas': row[26] if len(row) > 26 else None,
                    'direitos_trabalhistas': row[27] if len(row) > 27 else None
                }
                
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
            
            # Buscar processo e dados NLP
            query = """
                SELECT p.*, 
                       r.id as nlp_id, r.resumo_extrativo, r.tema_principal, r.qualidade_texto, 
                       r.confianca_global, r.palavras_chave, r.entidades_nomeadas,
                       r.direitos_trabalhistas, r.valores_monetarios, r.base_legal,
                       r.tempo_processamento, r.metodo_sumarizacao, r.versao_pipeline,
                       r.texto_processado, r.resumo_estruturado
                FROM processos_judiciais p
                LEFT JOIN resultados_nlp r ON p.id = r.processo_id
                WHERE p.id = ?
            """
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (processo_id,))
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
                'conteudo_bruto_decisao': row[11] if include_content else None,
                'origem_texto': row[12],
                'colecao_api': row[13],
                'id_documento_api': row[14],
                'referencia_legislativa': row[15],
                'processado_nlp': bool(row[16]),
                'data_coleta': row[17],
                'data_processamento': row[18],
                'metadados': row[19]
            }
            
            # Adicionar resultados NLP se disponíveis
            if row[21]:  # nlp_id
                import json
                
                processo['resultado_nlp'] = {
                    'id': row[21],
                    'processo_id': processo_id,
                    'resumo_extrativo': row[22],
                    'tema_principal': row[23],
                    'qualidade_texto': row[24],
                    'confianca_global': row[25],
                    'palavras_chave': row[26],
                    'entidades_nomeadas': row[27],
                    'direitos_trabalhistas': row[28],
                    'valores_monetarios': row[29],
                    'base_legal': row[30],
                    'tempo_processamento': row[31],
                    'metodo_sumarizacao': row[32],
                    'versao_pipeline': row[33],
                    'texto_processado': row[34] if include_content else None,
                    'resumo_estruturado': row[35]
                }
                
                # Deserializar campos JSON
                try:
                    if row[27]:  # entidades_nomeadas
                        processo['resultado_nlp']['entidades'] = json.loads(row[27])
                except (json.JSONDecodeError, TypeError):
                    pass
                
                try:
                    if row[28]:  # direitos_trabalhistas
                        processo['resultado_nlp']['direitos_trabalhistas'] = json.loads(row[28])
                except (json.JSONDecodeError, TypeError):
                    pass
                
                try:
                    if row[29]:  # valores_monetarios
                        processo['resultado_nlp']['valores_monetarios'] = json.loads(row[29])
                except (json.JSONDecodeError, TypeError):
                    pass
                
                try:
                    if row[35]:  # resumo_estruturado
                        processo['resultado_nlp']['resumo_estruturado'] = json.loads(row[35])
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
            
            # Garantir que filters é um dicionário
            if not isinstance(filters, dict):
                acoes_ns.abort(400, "Erro na validação dos parâmetros")
            
            # Use cast to help the linter
            filters = cast(Dict[str, Any], filters)
            
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
                       r.confianca_global,
                       r.palavras_chave,
                       r.entidades_nomeadas,
                       r.direitos_trabalhistas
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
                    # Campos NLP básicos
                    'tema_principal': row[16] if len(row) > 16 else None,
                    'qualidade_texto': row[17] if len(row) > 17 else None,
                    'confianca_global': row[18] if len(row) > 18 else None,
                    # Campos NLP avançados
                    'palavras_chave': row[19] if len(row) > 19 else None,
                    'entidades_nomeadas': row[20] if len(row) > 20 else None,
                    'direitos_trabalhistas': row[21] if len(row) > 21 else None
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


# Modelo para resumo rápido
resumo_rapido_model = acoes_ns.model('ResumoRapido', {
    'processo': fields.String(required=True, description='Número do processo'),
    'tribunal': fields.String(required=True, description='Tribunal'),
    'tipo_documento': fields.String(description='Tipo do documento'),
    'resumo_rapido': fields.String(required=True, description='Resumo em texto corrido'),
    'resultado_principal': fields.String(description='Resultado principal da decisão'),
    'principais_direitos': fields.List(fields.String, description='Principais direitos identificados'),
    'valor_total': fields.String(description='Valor total identificado'),
    'qualidade_analise': fields.String(description='Qualidade da análise (Alta/Média/Baixa)'),
    'confianca_percentual': fields.String(description='Confiança da análise em percentual'),
    'data_julgamento': fields.String(description='Data do julgamento'),
    'relator': fields.String(description='Relator da decisão'),
    'partes_resumo': fields.String(description='Resumo das partes envolvidas')
})


@acoes_ns.route('/<int:processo_id>/resumo')
class AcaoResumoResource(Resource):
    """Obter resumo rápido e inteligente de uma ação específica"""
    
    @acoes_ns.doc('obter_resumo_rapido')
    @acoes_ns.marshal_with(resumo_rapido_model)
    def get(self, processo_id: int):
        """Gerar resumo rápido e inteligente de uma ação coletiva"""
        try:
            logger.info(f"Gerando resumo rápido para processo {processo_id}")
            
            # Obter banco de dados
            db = get_database()
            
            # Buscar processo e dados NLP
            query = """
                SELECT p.numero_processo, p.tribunal, p.tipo_documento, p.data_julgamento,
                       p.relator, p.partes, p.conteudo_bruto_decisao,
                       r.resumo_extrativo, r.tema_principal, r.qualidade_texto, 
                       r.confianca_global, r.palavras_chave, r.entidades_nomeadas,
                       r.direitos_trabalhistas, r.valores_monetarios,
                       r.base_legal, r.resumo_estruturado
                FROM processos_judiciais p
                LEFT JOIN resultados_nlp r ON p.id = r.processo_id
                WHERE p.id = ?
            """
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (processo_id,))
                row = cursor.fetchone()
                
                if not row:
                    acoes_ns.abort(404, f"Processo {processo_id} não encontrado")
            
            # Extrair dados
            numero_processo = row[0]
            tribunal = row[1]
            tipo_documento = row[2]
            data_julgamento = row[3]
            relator = row[4]
            partes = row[5]
            conteudo_bruto = row[6]
            resumo_extrativo = row[7]
            tema_principal = row[8]
            qualidade_texto = row[9]
            confianca_global = row[10]
            palavras_chave = row[11]
            entidades_nomeadas = row[12]
            direitos_trabalhistas = row[13]
            valores_monetarios = row[14]
            # Novos campos NLP avançados
            base_legal = row[15] if len(row) > 15 else None
            resumo_estruturado = row[16] if len(row) > 16 else None
            
            # Gerar resumo inteligente
            resumo_parts = []
            
            # Cabeçalho básico
            resumo_parts.append(f"Processo {numero_processo} ({tribunal})")
            
            if tipo_documento:
                resumo_parts.append(f"- {tipo_documento}")
            
            # Tema principal ou assunto
            if tema_principal and tema_principal != "Não identificado":
                resumo_parts.append(f"sobre {tema_principal}")
            elif resumo_extrativo:
                # Extrair primeira frase do resumo como tema
                primeira_frase = resumo_extrativo.split('.')[0][:100] + "..."
                resumo_parts.append(f"versando sobre {primeira_frase}")
            
            # Analisar resultado da decisão usando o analisador inteligente
            # Usar análise em tempo real
            from ...nlp.resultado_analyzer import ResultadoAnalyzer
            
            analyzer = ResultadoAnalyzer()
            resultado_analise = analyzer.analisar_resultado(resumo_extrativo, direitos_trabalhistas)
            resultado_principal = resultado_analise.resultado_principal
            
            resumo_parts.append(f". **RESULTADO: {resultado_principal}**")
            
            # Direitos principais
            principais_direitos = []
            if direitos_trabalhistas:
                import json
                try:
                    direitos_data = json.loads(direitos_trabalhistas)
                    if isinstance(direitos_data, list):
                        for direito in direitos_data[:3]:  # Máximo 3 direitos
                            if isinstance(direito, dict) and 'description' in direito:
                                principais_direitos.append(direito['description'])
                except:
                    pass
            
            if principais_direitos:
                resumo_parts.append(f" Direitos envolvidos: {', '.join(principais_direitos)}")
            
            # Valores monetários
            valor_total = "Valor não especificado"
            if valores_monetarios:
                try:
                    valores_data = json.loads(valores_monetarios)
                    if isinstance(valores_data, list) and valores_data:
                        # Pegar o primeiro valor encontrado
                        primeiro_valor = valores_data[0]
                        if isinstance(primeiro_valor, dict) and 'text' in primeiro_valor:
                            valor_total = primeiro_valor['text']
                        elif len(valores_data) > 1:
                            valor_total = f"{primeiro_valor['text']} (entre outros)"
                except:
                    pass
            
            if valor_total != "Valor não especificado":
                resumo_parts.append(f". Valor: {valor_total}")
            
            # Informações complementares
            if data_julgamento:
                resumo_parts.append(f". Julgado em {data_julgamento}")
            
            if relator:
                resumo_parts.append(f". Relator: {relator}")
            
            # Qualidade da análise
            qualidade_analise = "Baixa"
            if qualidade_texto:
                if qualidade_texto >= 0.7:
                    qualidade_analise = "Alta"
                elif qualidade_texto >= 0.5:
                    qualidade_analise = "Média"
            
            # Confiança em percentual
            confianca_percentual = "Não disponível"
            if confianca_global:
                confianca_percentual = f"{int(confianca_global * 100)}%"
            
            # Resumo das partes
            partes_resumo = "Partes não identificadas"
            if partes:
                # Formatação simples das partes
                partes_clean = partes.replace('\n', ' ').replace('\r', ' ')
                if len(partes_clean) > 100:
                    partes_resumo = partes_clean[:100] + "..."
                else:
                    partes_resumo = partes_clean
            
            # Montar resumo final
            resumo_final = ''.join(resumo_parts)
            
            # Adicionar contexto do resumo extrativo se disponível
            if resumo_extrativo and len(resumo_extrativo) > 50:
                resumo_final += f"\n\nResumo da decisão: {resumo_extrativo[:300]}..."
            
            # Adicionar referências legislativas se disponíveis
            if base_legal:
                resumo_final += f"\n\nReferências legais: {base_legal}"
            
            response_data = {
                'processo': numero_processo,
                'tribunal': tribunal,
                'tipo_documento': tipo_documento,
                'resumo_rapido': resumo_final,
                'resultado_principal': resultado_principal,
                'principais_direitos': principais_direitos,
                'valor_total': valor_total,
                'qualidade_analise': qualidade_analise,
                'confianca_percentual': confianca_percentual,
                'data_julgamento': data_julgamento,
                'relator': relator,
                'partes_resumo': partes_resumo
            }
            
            logger.info(f"Resumo rápido gerado para processo {processo_id}")
            return response_data
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo rápido: {e}")
            acoes_ns.abort(500, f"Erro interno: {str(e)}")


@acoes_ns.route('/resumos')
class AcoesResumosBatchResource(Resource):
    """Obter resumos rápidos de múltiplas ações"""
    
    @acoes_ns.doc('obter_resumos_batch')
    @acoes_ns.expect(acoes_ns.parser()
                    .add_argument('page', type=int, default=1, help='Página')
                    .add_argument('per_page', type=int, default=10, help='Itens por página (max: 20)')
                    .add_argument('tribunal', type=str, help='Filtrar por tribunal')
                    .add_argument('tema', type=str, help='Filtrar por tema'))
    def get(self):
        """Obter resumos rápidos de múltiplas ações com paginação"""
        try:
            # Parâmetros
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 10, type=int), 20)
            tribunal = request.args.get('tribunal')
            tema = request.args.get('tema')
            
            logger.info(f"Gerando resumos em lote - página {page}")
            
            # Obter banco de dados
            db = get_database()
            
            # Construir filtros
            where_conditions = ["r.resumo_extrativo IS NOT NULL"]
            params = []
            
            if tribunal:
                where_conditions.append("p.tribunal LIKE ?")
                params.append(f"%{tribunal}%")
            
            if tema:
                where_conditions.append("r.tema_principal LIKE ?")
                params.append(f"%{tema}%")
            
            where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Paginação
            offset = (page - 1) * per_page
            
            # Query
            query = f"""
                SELECT p.id, p.numero_processo, p.tribunal, p.tipo_documento,
                       r.tema_principal, r.qualidade_texto, r.confianca_global
                FROM processos_judiciais p
                INNER JOIN resultados_nlp r ON p.id = r.processo_id
                {where_clause}
                ORDER BY p.data_coleta DESC
                LIMIT {per_page} OFFSET {offset}
            """
            
            # Contar total
            count_query = f"""
                SELECT COUNT(*)
                FROM processos_judiciais p
                INNER JOIN resultados_nlp r ON p.id = r.processo_id
                {where_clause}
            """
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Buscar processos
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Contar total
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
            
            # Gerar resumos para cada processo
            resumos = []
            for row in rows:
                processo_id = row[0]
                numero_processo = row[1]
                tribunal = row[2]
                tipo_documento = row[3]
                tema_principal = row[4]
                qualidade_texto = row[5]
                confianca_global = row[6]
                
                # Resumo simplificado para lote
                qualidade = "Alta" if qualidade_texto and qualidade_texto >= 0.7 else "Média" if qualidade_texto and qualidade_texto >= 0.5 else "Baixa"
                confianca = f"{int(confianca_global * 100)}%" if confianca_global else "N/A"
                
                resumo_simples = {
                    'id': processo_id,
                    'processo': numero_processo,
                    'tribunal': tribunal,
                    'tipo_documento': tipo_documento,
                    'tema_principal': tema_principal or "Não identificado",
                    'qualidade_analise': qualidade,
                    'confianca_percentual': confianca,
                    'link_resumo_completo': f"/api/acoes/{processo_id}/resumo"
                }
                
                resumos.append(resumo_simples)
            
            # Metadados de paginação
            total_pages = math.ceil(total / per_page)
            
            response_data = {
                'data': resumos,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'total_found': total
            }
            
            logger.info(f"Gerados {len(resumos)} resumos em lote")
            return response_data
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumos em lote: {e}")
            acoes_ns.abort(500, f"Erro interno: {str(e)}") 