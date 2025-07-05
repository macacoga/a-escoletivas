"""
Endpoints da API para tópicos e temas
"""

from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from typing import Dict, Any, List
from collections import Counter
import json
from datetime import datetime

from ...database.manager import DatabaseManager
from ...utils.logging import get_logger
from ..app import get_database


# Configurar namespace
topicos_ns = Namespace('topicos', description='Endpoints para tópicos e temas')

# Modelos para documentação da API
topico_model = topicos_ns.model('Topico', {
    'nome': fields.String(required=True, description='Nome do tópico'),
    'descricao': fields.String(required=True, description='Descrição do tópico'),
    'frequencia': fields.Integer(required=True, description='Frequência de ocorrência'),
    'porcentagem': fields.Float(required=True, description='Porcentagem do total'),
    'exemplos': fields.List(fields.String(), description='Exemplos de menções')
})

topicos_resposta_model = topicos_ns.model('TopicosResposta', {
    'temas_principais': fields.List(fields.Nested(topico_model), description='Temas principais'),
    'direitos_trabalhistas': fields.List(fields.Nested(topico_model), description='Direitos trabalhistas'),
    'tribunais': fields.List(fields.Nested(topico_model), description='Tribunais'),
    'total_processos_analisados': fields.Integer(description='Total de processos analisados'),
    'data_analise': fields.String(description='Data da análise')
})

logger = get_logger("API.Topicos")


@topicos_ns.route('')
class TopicosResource(Resource):
    """Listar tópicos mais frequentes"""
    
    @topicos_ns.doc('listar_topicos')
    @topicos_ns.expect(topicos_ns.parser()
                      .add_argument('limite', type=int, default=20, help='Limite de tópicos por categoria')
                      .add_argument('apenas_nlp', type=bool, default=True, help='Apenas processos com NLP'))
    @topicos_ns.marshal_with(topicos_resposta_model)
    def get(self):
        """Listar os tópicos mais frequentes encontrados nas decisões"""
        try:
            limite = request.args.get('limite', 20, type=int)
            apenas_nlp = request.args.get('apenas_nlp', True, type=bool)
            
            logger.info(f"Analisando tópicos - limite: {limite}, apenas NLP: {apenas_nlp}")
            
            # Obter banco de dados
            db = get_database()
            
            # Query para buscar dados
            if apenas_nlp:
                query = """
                    SELECT p.tribunal, 
                           r.tema_principal,
                           r.direitos_trabalhistas,
                           r.entidades_nomeadas
                    FROM processos_judiciais p
                    JOIN resultados_nlp r ON p.id = r.processo_id
                    WHERE r.tema_principal IS NOT NULL
                """
            else:
                query = """
                    SELECT p.tribunal, 
                           r.tema_principal,
                           r.direitos_trabalhistas,
                           r.entidades_nomeadas
                    FROM processos_judiciais p
                    LEFT JOIN resultados_nlp r ON p.id = r.processo_id
                """
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
            
            # Contadores para diferentes categorias
            tribunais_counter = Counter()
            temas_counter = Counter()
            direitos_counter = Counter()
            
            # Processar resultados
            total_processos = len(rows)
            
            for row in rows:
                tribunal, tema_principal, direitos_json, entidades_json = row
                
                # Contar tribunais
                if tribunal:
                    tribunais_counter[tribunal] += 1
                
                # Contar temas principais
                if tema_principal:
                    temas_counter[tema_principal] += 1
                
                # Contar direitos trabalhistas
                if direitos_json:
                    try:
                        direitos = json.loads(direitos_json)
                        if isinstance(direitos, list):
                            for direito in direitos:
                                if isinstance(direito, dict) and 'type' in direito:
                                    direitos_counter[direito['type']] += 1
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            # Converter contadores em listas formatadas
            def format_topicos(counter, descricoes_map, limite):
                topicos = []
                for nome, freq in counter.most_common(limite):
                    topicos.append({
                        'nome': nome,
                        'descricao': descricoes_map.get(nome, nome),
                        'frequencia': freq,
                        'porcentagem': round((freq / total_processos) * 100, 2) if total_processos > 0 else 0,
                        'exemplos': [nome]  # Simplificado - poderia buscar exemplos reais
                    })
                return topicos
            
            # Mapas de descrição para diferentes categorias
            tribunais_desc = {
                'TRT10': 'Tribunal Regional do Trabalho da 10ª Região',
                'TRT1': 'Tribunal Regional do Trabalho da 1ª Região',
                'TRT2': 'Tribunal Regional do Trabalho da 2ª Região',
                'TRT3': 'Tribunal Regional do Trabalho da 3ª Região',
                'TRT4': 'Tribunal Regional do Trabalho da 4ª Região',
                'TRT5': 'Tribunal Regional do Trabalho da 5ª Região',
                'TRT6': 'Tribunal Regional do Trabalho da 6ª Região',
                'TRT7': 'Tribunal Regional do Trabalho da 7ª Região',
                'TRT8': 'Tribunal Regional do Trabalho da 8ª Região',
                'TRT9': 'Tribunal Regional do Trabalho da 9ª Região',
                'TRT11': 'Tribunal Regional do Trabalho da 11ª Região',
                'TRT12': 'Tribunal Regional do Trabalho da 12ª Região',
                'TRT13': 'Tribunal Regional do Trabalho da 13ª Região',
                'TRT14': 'Tribunal Regional do Trabalho da 14ª Região',
                'TRT15': 'Tribunal Regional do Trabalho da 15ª Região',
                'TRT16': 'Tribunal Regional do Trabalho da 16ª Região',
                'TRT17': 'Tribunal Regional do Trabalho da 17ª Região',
                'TRT18': 'Tribunal Regional do Trabalho da 18ª Região',
                'TRT19': 'Tribunal Regional do Trabalho da 19ª Região',
                'TRT20': 'Tribunal Regional do Trabalho da 20ª Região',
                'TRT21': 'Tribunal Regional do Trabalho da 21ª Região',
                'TRT22': 'Tribunal Regional do Trabalho da 22ª Região',
                'TRT23': 'Tribunal Regional do Trabalho da 23ª Região',
                'TRT24': 'Tribunal Regional do Trabalho da 24ª Região',
                'TST': 'Tribunal Superior do Trabalho'
            }
            
            direitos_desc = {
                'overtime': 'Horas extras',
                'night_shift': 'Adicional noturno',
                'salary_equalization': 'Equiparação salarial',
                'unhealthy_conditions': 'Insalubridade',
                'dangerous_conditions': 'Periculosidade',
                'vacation_pay': 'Férias',
                'thirteenth_salary': '13º salário',
                'severance_pay': 'Verbas rescisórias',
                'profit_sharing': 'Participação nos lucros',
                'transportation_allowance': 'Vale transporte',
                'meal_allowance': 'Vale refeição',
                'union_stability': 'Estabilidade sindical',
                'workplace_harassment': 'Assédio moral',
                'workplace_accident': 'Acidente de trabalho',
                'occupational_disease': 'Doença ocupacional',
                'collective_bargaining': 'Negociação coletiva',
                'strike_right': 'Direito de greve',
                'union_representation': 'Representação sindical'
            }
            
            temas_desc = {
                'direitos_trabalhistas': 'Direitos trabalhistas',
                'acidente_trabalho': 'Acidente de trabalho',
                'assedio_moral': 'Assédio moral',
                'horas_extras': 'Horas extras',
                'adicional_noturno': 'Adicional noturno',
                'insalubridade': 'Insalubridade',
                'periculosidade': 'Periculosidade',
                'equiparacao_salarial': 'Equiparação salarial',
                'verbas_rescisórias': 'Verbas rescisórias',
                'negociacao_coletiva': 'Negociação coletiva',
                'greve': 'Direito de greve',
                'representacao_sindical': 'Representação sindical'
            }
            
            # Formatar resposta
            response_data = {
                'temas_principais': format_topicos(temas_counter, temas_desc, limite),
                'direitos_trabalhistas': format_topicos(direitos_counter, direitos_desc, limite),
                'tribunais': format_topicos(tribunais_counter, tribunais_desc, limite),
                'total_processos_analisados': total_processos,
                'data_analise': datetime.now().isoformat()
            }
            
            logger.info(f"Análise de tópicos concluída - {total_processos} processos analisados")
            return response_data
            
        except Exception as e:
            logger.error(f"Erro ao analisar tópicos: {e}")
            topicos_ns.abort(500, f"Erro interno: {str(e)}")


@topicos_ns.route('/direitos')
class DireitosResource(Resource):
    """Listar direitos trabalhistas específicos"""
    
    @topicos_ns.doc('listar_direitos')
    @topicos_ns.expect(topicos_ns.parser()
                      .add_argument('limite', type=int, default=20, help='Limite de direitos')
                      .add_argument('resultado', type=str, help='Filtrar por resultado (granted/denied/partially_granted)')
                      .add_argument('detalhado', type=bool, default=False, help='Incluir detalhes das decisões'))
    def get(self):
        """Listar direitos trabalhistas com estatísticas detalhadas"""
        try:
            limite = request.args.get('limite', 20, type=int)
            resultado = request.args.get('resultado', None, type=str)
            detalhado = request.args.get('detalhado', False, type=bool)
            
            logger.info(f"Analisando direitos trabalhistas - limite: {limite}, resultado: {resultado}")
            
            # Obter banco de dados
            db = get_database()
            
            # Query para buscar dados
            query = """
                SELECT p.numero_processo,
                       p.tribunal,
                       p.partes,
                       r.direitos_trabalhistas,
                       r.qualidade_texto,
                       r.confianca_global
                FROM processos_judiciais p
                JOIN resultados_nlp r ON p.id = r.processo_id
                WHERE r.direitos_trabalhistas IS NOT NULL
                  AND r.direitos_trabalhistas != ''
                  AND r.direitos_trabalhistas != '[]'
            """
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
            
            # Processar direitos
            direitos_stats = {}
            
            for row in rows:
                numero_processo, tribunal, partes, direitos_json, qualidade, confianca = row
                
                try:
                    direitos = json.loads(direitos_json)
                    if not isinstance(direitos, list):
                        continue
                    
                    for direito in direitos:
                        if not isinstance(direito, dict) or 'type' not in direito:
                            continue
                        
                        tipo = direito['type']
                        outcome = direito.get('decision_outcome', 'unknown')
                        confidence = direito.get('confidence', 0.0)
                        
                        # Filtrar por resultado se especificado
                        if resultado and outcome != resultado:
                            continue
                        
                        # Inicializar estatísticas se necessário
                        if tipo not in direitos_stats:
                            direitos_stats[tipo] = {
                                'total': 0,
                                'granted': 0,
                                'denied': 0,
                                'partially_granted': 0,
                                'unknown': 0,
                                'confidence_sum': 0.0,
                                'quality_sum': 0.0,
                                'casos': []
                            }
                        
                        # Atualizar estatísticas
                        stats = direitos_stats[tipo]
                        stats['total'] += 1
                        stats[outcome] += 1
                        stats['confidence_sum'] += confidence
                        stats['quality_sum'] += qualidade or 0.0
                        
                        # Adicionar caso se modo detalhado
                        if detalhado:
                            stats['casos'].append({
                                'numero_processo': numero_processo,
                                'tribunal': tribunal,
                                'partes': partes,
                                'outcome': outcome,
                                'confidence': confidence,
                                'mentions': direito.get('mentions', [])
                            })
                
                except (json.JSONDecodeError, TypeError):
                    continue
            
            # Formatar resposta
            direitos_formatados = []
            
            for tipo, stats in direitos_stats.items():
                if stats['total'] == 0:
                    continue
                
                # Calcular métricas
                taxa_sucesso = ((stats['granted'] + stats['partially_granted']) / stats['total']) * 100
                confianca_media = stats['confidence_sum'] / stats['total']
                qualidade_media = stats['quality_sum'] / stats['total']
                
                direito_info = {
                    'tipo': tipo,
                    'descricao': get_direito_description(tipo),
                    'total_casos': stats['total'],
                    'resultados': {
                        'granted': stats['granted'],
                        'denied': stats['denied'],
                        'partially_granted': stats['partially_granted'],
                        'unknown': stats['unknown']
                    },
                    'taxa_sucesso': round(taxa_sucesso, 2),
                    'confianca_media': round(confianca_media, 3),
                    'qualidade_media': round(qualidade_media, 3)
                }
                
                # Adicionar casos detalhados se solicitado
                if detalhado:
                    direito_info['casos'] = stats['casos'][:5]  # Limitar a 5 casos por direito
                
                direitos_formatados.append(direito_info)
            
            # Ordenar por total de casos
            direitos_formatados.sort(key=lambda x: x['total_casos'], reverse=True)
            
            # Limitar resultados
            if limite > 0:
                direitos_formatados = direitos_formatados[:limite]
            
            response_data = {
                'direitos_trabalhistas': direitos_formatados,
                'total_tipos': len(direitos_formatados),
                'total_casos': sum(d['total_casos'] for d in direitos_formatados),
                'filtros': {
                    'resultado': resultado,
                    'detalhado': detalhado
                },
                'data_analise': datetime.now().isoformat()
            }
            
            logger.info(f"Análise de direitos concluída - {len(direitos_formatados)} tipos, {response_data['total_casos']} casos")
            return response_data
            
        except Exception as e:
            logger.error(f"Erro ao analisar direitos: {e}")
            topicos_ns.abort(500, f"Erro interno: {str(e)}")


def get_direito_description(tipo: str) -> str:
    """Obter descrição amigável para um tipo de direito"""
    descriptions = {
        'overtime': 'Horas extras - Pagamento de horas trabalhadas além da jornada normal',
        'night_shift': 'Adicional noturno - Remuneração adicional para trabalho noturno',
        'salary_equalization': 'Equiparação salarial - Igualdade de remuneração para função similar',
        'unhealthy_conditions': 'Insalubridade - Adicional por trabalho em condições insalubres',
        'dangerous_conditions': 'Periculosidade - Adicional por trabalho em condições perigosas',
        'vacation_pay': 'Férias - Direito ao período de descanso remunerado',
        'thirteenth_salary': '13º salário - Gratificação natalina',
        'severance_pay': 'Verbas rescisórias - Pagamentos devidos na rescisão do contrato',
        'profit_sharing': 'Participação nos lucros - Distribuição de resultados da empresa',
        'transportation_allowance': 'Vale transporte - Auxílio para deslocamento ao trabalho',
        'meal_allowance': 'Vale refeição - Auxílio para alimentação',
        'union_stability': 'Estabilidade sindical - Proteção contra demissão por atividade sindical',
        'workplace_harassment': 'Assédio moral - Proteção contra práticas abusivas no trabalho',
        'workplace_accident': 'Acidente de trabalho - Direitos em caso de acidentes laborais',
        'occupational_disease': 'Doença ocupacional - Direitos relacionados a doenças do trabalho',
        'collective_bargaining': 'Negociação coletiva - Acordos entre sindicatos e empresas',
        'strike_right': 'Direito de greve - Exercício do direito de paralisação',
        'union_representation': 'Representação sindical - Atuação dos sindicatos'
    }
    return descriptions.get(tipo, tipo.replace('_', ' ').title()) 