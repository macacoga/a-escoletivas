"""
Endpoints da API para estatísticas
"""

from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
from collections import Counter, defaultdict

from ...database.manager import DatabaseManager
from ...utils.logging import get_logger
from ..app import get_database


# Configurar namespace
stats_ns = Namespace('stats', description='Endpoints para estatísticas')

# Modelos para documentação da API
stats_geral_model = stats_ns.model('EstatisticasGerais', {
    'total_processos': fields.Integer(description='Total de processos'),
    'processos_processados': fields.Integer(description='Processos processados'),
    'resultados_nlp': fields.Integer(description='Resultados NLP'),
    'tribunais_unicos': fields.Integer(description='Tribunais únicos'),
    'ultima_coleta': fields.String(description='Última coleta'),
    'qualidade_media': fields.Float(description='Qualidade média'),
    'confianca_media': fields.Float(description='Confiança média'),
    'tempo_processamento_medio': fields.Float(description='Tempo médio de processamento'),
    'data_analise': fields.String(description='Data da análise')
})

logger = get_logger("API.Stats")


@stats_ns.route('/geral')
class EstatisticasGeraisResource(Resource):
    """Estatísticas gerais do sistema"""
    
    @stats_ns.doc('estatisticas_gerais')
    @stats_ns.marshal_with(stats_geral_model)
    def get(self):
        """Obter estatísticas gerais do sistema"""
        try:
            logger.info("Gerando estatísticas gerais")
            
            # Obter banco de dados
            db = get_database()
            
            # Queries para estatísticas básicas
            queries = {
                'total_processos': "SELECT COUNT(*) FROM processos_judiciais",
                'processos_processados': "SELECT COUNT(*) FROM processos_judiciais WHERE processado_nlp = 1",
                'resultados_nlp': "SELECT COUNT(*) FROM resultados_nlp",
                'tribunais_unicos': "SELECT COUNT(DISTINCT tribunal) FROM processos_judiciais WHERE tribunal IS NOT NULL",
                'ultima_coleta': "SELECT MAX(data_coleta) FROM processos_judiciais",
                'qualidade_media': "SELECT AVG(qualidade_texto) FROM resultados_nlp WHERE qualidade_texto IS NOT NULL",
                'confianca_media': "SELECT AVG(confianca_global) FROM resultados_nlp WHERE confianca_global IS NOT NULL",
                'tempo_processamento_medio': "SELECT AVG(tempo_processamento) FROM resultados_nlp WHERE tempo_processamento IS NOT NULL"
            }
            
            # Executar queries
            stats = {}
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                for nome, query in queries.items():
                    cursor.execute(query)
                    result = cursor.fetchone()
                    stats[nome] = result[0] if result and result[0] is not None else 0
            
            # Formatar resposta
            response_data = {
                'total_processos': stats['total_processos'],
                'processos_processados': stats['processos_processados'],
                'resultados_nlp': stats['resultados_nlp'],
                'tribunais_unicos': stats['tribunais_unicos'],
                'ultima_coleta': stats['ultima_coleta'],
                'qualidade_media': round(stats['qualidade_media'], 3) if stats['qualidade_media'] else None,
                'confianca_media': round(stats['confianca_media'], 3) if stats['confianca_media'] else None,
                'tempo_processamento_medio': round(stats['tempo_processamento_medio'], 3) if stats['tempo_processamento_medio'] else None,
                'data_analise': datetime.now().isoformat()
            }
            
            logger.info("Estatísticas gerais geradas com sucesso")
            return response_data
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas gerais: {e}")
            stats_ns.abort(500, f"Erro interno: {str(e)}")


@stats_ns.route('/distribuicao')
class DistribuicaoResource(Resource):
    """Estatísticas de distribuição"""
    
    @stats_ns.doc('estatisticas_distribuicao')
    @stats_ns.expect(stats_ns.parser()
                    .add_argument('categoria', type=str, required=True, 
                                 help='Categoria: tribunal, qualidade, tema, direito')
                    .add_argument('limite', type=int, default=10, help='Limite de resultados'))
    def get(self):
        """Obter distribuição por categoria"""
        try:
            categoria = request.args.get('categoria', type=str)
            limite = request.args.get('limite', 10, type=int)
            
            if not categoria:
                stats_ns.abort(400, "Parâmetro 'categoria' é obrigatório")
            
            logger.info(f"Gerando distribuição por {categoria}")
            
            # Obter banco de dados
            db = get_database()
            
            # Definir queries por categoria
            if categoria == 'tribunal':
                query = """
                    SELECT tribunal, COUNT(*) as quantidade
                    FROM processos_judiciais 
                    WHERE tribunal IS NOT NULL
                    GROUP BY tribunal
                    ORDER BY quantidade DESC
                """
            elif categoria == 'qualidade':
                query = """
                    SELECT 
                        CASE 
                            WHEN qualidade_texto >= 0.8 THEN 'Excelente (0.8-1.0)'
                            WHEN qualidade_texto >= 0.6 THEN 'Boa (0.6-0.8)'
                            WHEN qualidade_texto >= 0.4 THEN 'Regular (0.4-0.6)'
                            WHEN qualidade_texto >= 0.2 THEN 'Baixa (0.2-0.4)'
                            ELSE 'Muito Baixa (0.0-0.2)'
                        END as faixa_qualidade,
                        COUNT(*) as quantidade
                    FROM resultados_nlp 
                    WHERE qualidade_texto IS NOT NULL
                    GROUP BY faixa_qualidade
                    ORDER BY quantidade DESC
                """
            elif categoria == 'tema':
                query = """
                    SELECT tema_principal, COUNT(*) as quantidade
                    FROM resultados_nlp 
                    WHERE tema_principal IS NOT NULL
                    GROUP BY tema_principal
                    ORDER BY quantidade DESC
                """
            elif categoria == 'direito':
                # Para direitos, precisamos processar JSON
                query = """
                    SELECT direitos_trabalhistas
                    FROM resultados_nlp 
                    WHERE direitos_trabalhistas IS NOT NULL
                      AND direitos_trabalhistas != ''
                      AND direitos_trabalhistas != '[]'
                """
            else:
                stats_ns.abort(400, f"Categoria '{categoria}' não é válida. Use: tribunal, qualidade, tema, direito")
            
            # Executar query
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
            
            # Processar resultados
            if categoria == 'direito':
                # Processar JSON para direitos
                direitos_counter = Counter()
                for row in rows:
                    direitos_json = row[0]
                    try:
                        direitos = json.loads(direitos_json)
                        if isinstance(direitos, list):
                            for direito in direitos:
                                if isinstance(direito, dict) and 'type' in direito:
                                    direitos_counter[direito['type']] += 1
                    except (json.JSONDecodeError, TypeError):
                        continue
                
                # Converter para lista de tuplas
                distribuicao = direitos_counter.most_common(limite)
            else:
                # Processar resultados diretos
                distribuicao = [(row[0], row[1]) for row in rows[:limite]]
            
            # Calcular total e porcentagens
            total = sum(count for _, count in distribuicao)
            
            # Formatar resposta
            items = []
            for nome, quantidade in distribuicao:
                porcentagem = (quantidade / total) * 100 if total > 0 else 0
                items.append({
                    'nome': nome,
                    'quantidade': quantidade,
                    'porcentagem': round(porcentagem, 2)
                })
            
            response_data = {
                'categoria': categoria,
                'items': items,
                'total': total,
                'limite_aplicado': limite,
                'data_analise': datetime.now().isoformat()
            }
            
            logger.info(f"Distribuição por {categoria} gerada - {len(items)} itens")
            return response_data
            
        except Exception as e:
            logger.error(f"Erro ao gerar distribuição: {e}")
            stats_ns.abort(500, f"Erro interno: {str(e)}")


@stats_ns.route('/timeline')
class TimelineResource(Resource):
    """Estatísticas temporais"""
    
    @stats_ns.doc('timeline_estatisticas')
    @stats_ns.expect(stats_ns.parser()
                    .add_argument('periodo', type=str, default='mes', 
                                 help='Período: dia, semana, mes, ano')
                    .add_argument('limite', type=int, default=12, help='Limite de períodos'))
    def get(self):
        """Obter estatísticas ao longo do tempo"""
        try:
            periodo = request.args.get('periodo', 'mes', type=str)
            limite = request.args.get('limite', 12, type=int)
            
            if periodo not in ['dia', 'semana', 'mes', 'ano']:
                stats_ns.abort(400, "Período deve ser: dia, semana, mes ou ano")
            
            logger.info(f"Gerando timeline por {periodo}")
            
            # Obter banco de dados
            db = get_database()
            
            # Definir formato de data baseado no período
            if periodo == 'dia':
                date_format = '%Y-%m-%d'
                sql_format = '%Y-%m-%d'
            elif periodo == 'semana':
                date_format = '%Y-W%W'
                sql_format = '%Y-W%W'
            elif periodo == 'mes':
                date_format = '%Y-%m'
                sql_format = '%Y-%m'
            else:  # ano
                date_format = '%Y'
                sql_format = '%Y'
            
            # Query para coleta de dados
            query = f"""
                SELECT strftime('{sql_format}', data_coleta) as periodo,
                       COUNT(*) as total_processos,
                       SUM(CASE WHEN processado_nlp = 1 THEN 1 ELSE 0 END) as processados_nlp
                FROM processos_judiciais
                WHERE data_coleta IS NOT NULL
                GROUP BY periodo
                ORDER BY periodo DESC
                LIMIT {limite}
            """
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
            
            # Processar resultados
            timeline = []
            for row in rows:
                periodo_str, total, processados = row
                
                # Calcular taxa de processamento
                taxa_processamento = (processados / total) * 100 if total > 0 else 0
                
                timeline.append({
                    'periodo': periodo_str,
                    'total_processos': total,
                    'processados_nlp': processados,
                    'taxa_processamento': round(taxa_processamento, 2)
                })
            
            # Reverter para ordem cronológica
            timeline.reverse()
            
            # Calcular totais e médias
            total_processos = sum(item['total_processos'] for item in timeline)
            total_processados = sum(item['processados_nlp'] for item in timeline)
            taxa_media = (total_processados / total_processos) * 100 if total_processos > 0 else 0
            
            response_data = {
                'timeline': timeline,
                'resumo': {
                    'total_processos': total_processos,
                    'total_processados': total_processados,
                    'taxa_processamento_media': round(taxa_media, 2),
                    'periodos_analisados': len(timeline)
                },
                'configuracao': {
                    'periodo': periodo,
                    'limite': limite
                },
                'data_analise': datetime.now().isoformat()
            }
            
            logger.info(f"Timeline gerada - {len(timeline)} períodos")
            return response_data
            
        except Exception as e:
            logger.error(f"Erro ao gerar timeline: {e}")
            stats_ns.abort(500, f"Erro interno: {str(e)}")


@stats_ns.route('/qualidade')
class QualidadeResource(Resource):
    """Estatísticas de qualidade do processamento NLP"""
    
    @stats_ns.doc('qualidade_nlp')
    def get(self):
        """Obter estatísticas de qualidade do processamento NLP"""
        try:
            logger.info("Gerando estatísticas de qualidade NLP")
            
            # Obter banco de dados
            db = get_database()
            
            # Query para dados de qualidade
            query = """
                SELECT 
                    qualidade_texto,
                    confianca_global,
                    tempo_processamento,
                    metodo_sumarizacao,
                    CASE 
                        WHEN resumo_extrativo IS NOT NULL AND resumo_extrativo != '' THEN 1 
                        ELSE 0 
                    END as tem_resumo,
                    CASE 
                        WHEN tema_principal IS NOT NULL AND tema_principal != '' THEN 1 
                        ELSE 0 
                    END as tem_tema,
                    CASE 
                        WHEN direitos_trabalhistas IS NOT NULL AND direitos_trabalhistas != '[]' THEN 1 
                        ELSE 0 
                    END as tem_direitos,
                    CASE 
                        WHEN entidades_nomeadas IS NOT NULL AND entidades_nomeadas != '[]' THEN 1 
                        ELSE 0 
                    END as tem_entidades
                FROM resultados_nlp
                WHERE qualidade_texto IS NOT NULL
            """
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
            
            if not rows:
                return {
                    'message': 'Nenhum resultado de NLP encontrado',
                    'data_analise': datetime.now().isoformat()
                }
            
            # Processar estatísticas
            qualidades = []
            confiancas = []
            tempos = []
            metodos = Counter()
            
            taxa_resumo = 0
            taxa_tema = 0
            taxa_direitos = 0
            taxa_entidades = 0
            
            for row in rows:
                qualidade, confianca, tempo, metodo, tem_resumo, tem_tema, tem_direitos, tem_entidades = row
                
                if qualidade is not None:
                    qualidades.append(qualidade)
                if confianca is not None:
                    confiancas.append(confianca)
                if tempo is not None:
                    tempos.append(tempo)
                if metodo:
                    metodos[metodo] += 1
                
                taxa_resumo += tem_resumo
                taxa_tema += tem_tema
                taxa_direitos += tem_direitos
                taxa_entidades += tem_entidades
            
            total_resultados = len(rows)
            
            # Calcular estatísticas
            def calcular_stats(valores):
                if not valores:
                    return None
                
                valores_sorted = sorted(valores)
                n = len(valores)
                
                return {
                    'media': round(sum(valores) / n, 3),
                    'mediana': valores_sorted[n // 2] if n % 2 == 1 else (valores_sorted[n // 2 - 1] + valores_sorted[n // 2]) / 2,
                    'minimo': min(valores),
                    'maximo': max(valores),
                    'desvio_padrao': round((sum((x - sum(valores) / n) ** 2 for x in valores) / n) ** 0.5, 3)
                }
            
            # Distribuição por faixas de qualidade
            faixas_qualidade = {
                'excelente': sum(1 for q in qualidades if q >= 0.8),
                'boa': sum(1 for q in qualidades if 0.6 <= q < 0.8),
                'regular': sum(1 for q in qualidades if 0.4 <= q < 0.6),
                'baixa': sum(1 for q in qualidades if 0.2 <= q < 0.4),
                'muito_baixa': sum(1 for q in qualidades if q < 0.2)
            }
            
            response_data = {
                'total_resultados': total_resultados,
                'qualidade_texto': calcular_stats(qualidades),
                'confianca_global': calcular_stats(confiancas),
                'tempo_processamento': calcular_stats(tempos),
                'distribuicao_qualidade': {
                    nome: {
                        'quantidade': quantidade,
                        'porcentagem': round((quantidade / len(qualidades)) * 100, 2)
                    }
                    for nome, quantidade in faixas_qualidade.items()
                },
                'metodos_sumarizacao': [
                    {
                        'metodo': metodo,
                        'quantidade': quantidade,
                        'porcentagem': round((quantidade / total_resultados) * 100, 2)
                    }
                    for metodo, quantidade in metodos.most_common()
                ],
                'taxa_sucesso': {
                    'resumo': round((taxa_resumo / total_resultados) * 100, 2),
                    'tema': round((taxa_tema / total_resultados) * 100, 2),
                    'direitos': round((taxa_direitos / total_resultados) * 100, 2),
                    'entidades': round((taxa_entidades / total_resultados) * 100, 2)
                },
                'data_analise': datetime.now().isoformat()
            }
            
            logger.info(f"Estatísticas de qualidade geradas - {total_resultados} resultados")
            return response_data
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas de qualidade: {e}")
            stats_ns.abort(500, f"Erro interno: {str(e)}") 