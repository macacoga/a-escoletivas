"""
Módulo para criação de resumos estruturados focando no resultado principal
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

from .resultado_analyzer import ResultadoAnalyzer
from ..utils.logging import LoggerMixin, log_execution_time


@dataclass
class StructuredSummary:
    """Representa um resumo estruturado"""
    resultado_principal: str
    resultado_detalhado: Dict[str, Any]
    pedidos_principais: List[str]
    decisao_resumo: str
    fundamentacao_principal: str
    valores_envolvidos: List[Dict[str, Any]]
    confidence_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'resultado_principal': self.resultado_principal,
            'resultado_detalhado': self.resultado_detalhado,
            'pedidos_principais': self.pedidos_principais,
            'decisao_resumo': self.decisao_resumo,
            'fundamentacao_principal': self.fundamentacao_principal,
            'valores_envolvidos': self.valores_envolvidos,
            'confidence_score': self.confidence_score
        }


class StructuredSummarizer(LoggerMixin):
    """
    Classe para criação de resumos estruturados de decisões judiciais
    """
    
    def __init__(self):
        super().__init__()
        
        # Inicializar analisador de resultado
        self.resultado_analyzer = ResultadoAnalyzer()
        
        # Padrões para identificar seções
        self.section_patterns = {
            'pedidos': [
                r'(?:PEDIDOS?|REQUER|PLEITEIA|SOLICITA)[\s\S]*?(?=FUNDAMENTAÇÃO|RELATÓRIO|DECISÃO|VOTO|$)',
                r'(?:^|\n)(?:PEDIDOS?|REQUER|PLEITEIA|SOLICITA)[\s\:]+(.+?)(?=\n\n|\n[A-Z]{3,}|$)',
                r'(?:pede|requer|pleiteia|solicita)[\s\S]*?(?=\n\n|fundamentação|relatório|decisão)'
            ],
            'fundamentacao': [
                r'(?:FUNDAMENTAÇÃO|FUNDAMENTOS|RAZÕES)[\s\S]*?(?=DECISÃO|DISPOSITIVO|VOTO|$)',
                r'(?:^|\n)(?:FUNDAMENTAÇÃO|FUNDAMENTOS|RAZÕES)[\s\:]+(.+?)(?=\n\n|\nDECISÃO|\nDISPOSITIVO|$)',
                r'(?:fundamenta|baseia-se|considera)[\s\S]*?(?=\n\n|decisão|dispositivo)'
            ],
            'decisao': [
                r'(?:DECISÃO|DISPOSITIVO|VOTO|ACORDAM)[\s\S]*?(?=$)',
                r'(?:^|\n)(?:DECISÃO|DISPOSITIVO|VOTO|ACORDAM)[\s\:]+(.+?)(?=$)',
                r'(?:decide|julga|determina)[\s\S]*?(?=$)'
            ],
            'valores': [
                r'R\$\s*\d+(?:[.,]\d{3})*(?:[.,]\d{2})?',
                r'\d+(?:[.,]\d{3})*(?:[.,]\d{2})?\s*reais?',
                r'valor\s+de\s+R\$\s*\d+(?:[.,]\d{3})*(?:[.,]\d{2})?',
                r'quantia\s+de\s+R\$\s*\d+(?:[.,]\d{3})*(?:[.,]\d{2})?',
                r'importância\s+de\s+R\$\s*\d+(?:[.,]\d{3})*(?:[.,]\d{2})?'
            ]
        }
        
        # Padrões para identificar tipos de pedidos
        self.pedido_patterns = {
            'horas_extras': r'horas?\s+extras?',
            'adicional_noturno': r'adicional\s+noturno',
            'insalubridade': r'insalubridade',
            'periculosidade': r'periculosidade',
            'fgts': r'FGTS|Fundo\s+de\s+Garantia',
            'danos_morais': r'danos?\s+morais?',
            'equiparacao_salarial': r'equiparação\s+salarial',
            'diferenca_salarial': r'diferença\s+salarial',
            'verbas_rescisórias': r'verbas?\s+rescisórias?',
            'aviso_previo': r'aviso\s+prévio',
            'ferias': r'férias?\s+(?:proporcionais?|vencidas?)',
            'decimo_terceiro': r'décimo\s+terceiro|13[º°]\s+salário'
        }
        
        self.logger.info("StructuredSummarizer inicializado")
    
    @log_execution_time
    def create_structured_summary(self, text: str, parts_data: Optional[Dict] = None, 
                                 legal_refs: Optional[Dict] = None) -> StructuredSummary:
        """
        Cria resumo estruturado do texto
        
        Args:
            text: Texto da decisão judicial
            parts_data: Dados das partes do processo
            legal_refs: Referências legislativas
            
        Returns:
            Resumo estruturado
        """
        if not text:
            return self._create_empty_summary()
        
        try:
            # Analisar resultado principal
            resultado_analysis = self.resultado_analyzer.analyze_resultado(text)
            
            # Extrair seções
            sections = self._extract_sections(text)
            
            # Identificar pedidos principais
            pedidos = self._extract_main_requests(text, sections.get('pedidos', ''))
            
            # Extrair valores
            valores = self._extract_monetary_values(text)
            
            # Criar resumo da decisão
            decisao_resumo = self._create_decision_summary(
                sections.get('decisao', ''), 
                resultado_analysis
            )
            
            # Extrair fundamentação principal
            fundamentacao = self._extract_main_reasoning(sections.get('fundamentacao', ''))
            
            # Calcular confiança
            confidence = self._calculate_summary_confidence(
                resultado_analysis, pedidos, valores, sections
            )
            
            summary = StructuredSummary(
                resultado_principal=resultado_analysis['resultado'],
                resultado_detalhado=resultado_analysis,
                pedidos_principais=pedidos,
                decisao_resumo=decisao_resumo,
                fundamentacao_principal=fundamentacao,
                valores_envolvidos=valores,
                confidence_score=confidence
            )
            
            self.log_operation(
                "structured_summary_created",
                resultado=resultado_analysis['resultado'],
                pedidos_count=len(pedidos),
                valores_count=len(valores),
                confidence=confidence
            )
            
            return summary
            
        except Exception as e:
            self.log_error(e, "create_structured_summary")
            return self._create_empty_summary()
    
    def _create_empty_summary(self) -> StructuredSummary:
        """Cria resumo vazio"""
        return StructuredSummary(
            resultado_principal="Resultado não identificado",
            resultado_detalhado={'resultado': 'Resultado não identificado', 'confidence': 0.0},
            pedidos_principais=[],
            decisao_resumo="Decisão não identificada",
            fundamentacao_principal="Fundamentação não identificada",
            valores_envolvidos=[],
            confidence_score=0.0
        )
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extrai seções principais do texto"""
        sections = {}
        
        for section_name, patterns in self.section_patterns.items():
            if section_name == 'valores':
                continue  # Valores são tratados separadamente
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match:
                    if len(match.groups()) > 0:
                        sections[section_name] = match.group(1).strip()
                    else:
                        sections[section_name] = match.group(0).strip()
                    break
        
        return sections
    
    def _extract_main_requests(self, text: str, pedidos_section: str) -> List[str]:
        """Extrai pedidos principais"""
        pedidos = []
        
        # Usar seção de pedidos se disponível, senão usar texto completo
        search_text = pedidos_section if pedidos_section else text
        
        for pedido_type, pattern in self.pedido_patterns.items():
            if re.search(pattern, search_text, re.IGNORECASE):
                pedidos.append(pedido_type.replace('_', ' ').title())
        
        # Se não encontrou pedidos específicos, tentar extrair de forma mais genérica
        if not pedidos:
            # Procurar por verbos de pedido
            generic_patterns = [
                r'(?:pede|requer|pleiteia|solicita)\s+(.+?)(?=\.|;|\n)',
                r'(?:condenar|determinar|reconhecer)\s+(.+?)(?=\.|;|\n)',
                r'(?:pagamento|indenização)\s+(?:de|por)\s+(.+?)(?=\.|;|\n)'
            ]
            
            for pattern in generic_patterns:
                matches = re.finditer(pattern, search_text, re.IGNORECASE)
                for match in matches:
                    pedido = match.group(1).strip()
                    if len(pedido) > 10 and len(pedido) < 100:  # Filtrar pedidos muito curtos ou longos
                        pedidos.append(pedido)
        
        return pedidos[:5]  # Limitar a 5 pedidos principais
    
    def _extract_monetary_values(self, text: str) -> List[Dict[str, Any]]:
        """Extrai valores monetários"""
        valores = []
        
        for pattern in self.section_patterns['valores']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                valor_text = match.group(0)
                
                # Extrair contexto
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                
                # Tentar extrair valor numérico
                numeric_value = self._extract_numeric_value(valor_text)
                
                valores.append({
                    'text': valor_text,
                    'numeric_value': numeric_value,
                    'context': context,
                    'position': match.start()
                })
        
        # Remover duplicatas e ordenar por posição
        unique_valores = []
        seen_values = set()
        
        for valor in sorted(valores, key=lambda x: x['position']):
            value_key = valor['text'].lower().replace(' ', '')
            if value_key not in seen_values:
                seen_values.add(value_key)
                unique_valores.append(valor)
        
        return unique_valores[:10]  # Limitar a 10 valores
    
    def _extract_numeric_value(self, value_text: str) -> Optional[float]:
        """Extrai valor numérico de texto monetário"""
        # Remover símbolos e texto
        numeric_text = re.sub(r'[^\d,.]', '', value_text)
        
        # Tentar converter para float
        try:
            # Assumir formato brasileiro (vírgula como decimal)
            if ',' in numeric_text:
                # Se tem ponto e vírgula, ponto é separador de milhares
                if '.' in numeric_text and ',' in numeric_text:
                    numeric_text = numeric_text.replace('.', '').replace(',', '.')
                else:
                    # Se só tem vírgula, pode ser decimal
                    parts = numeric_text.split(',')
                    if len(parts) == 2 and len(parts[1]) == 2:
                        numeric_text = numeric_text.replace(',', '.')
            
            return float(numeric_text)
        except ValueError:
            return None
    
    def _create_decision_summary(self, decisao_text: str, resultado_analysis: Dict) -> str:
        """Cria resumo da decisão"""
        if not decisao_text:
            return f"Decisão: {resultado_analysis['resultado']}"
        
        # Extrair frases principais da decisão
        sentences = re.split(r'[.!?]+', decisao_text)
        important_sentences = []
        
        # Procurar por frases com palavras-chave de decisão
        decision_keywords = [
            'julgo', 'decido', 'determino', 'condeno', 'reconheço', 
            'defiro', 'indefiro', 'procedente', 'improcedente', 
            'parcialmente procedente', 'extingo'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Filtrar frases muito curtas
                for keyword in decision_keywords:
                    if keyword in sentence.lower():
                        important_sentences.append(sentence)
                        break
        
        if important_sentences:
            # Pegar as 2 frases mais importantes
            summary = '. '.join(important_sentences[:2])
            if len(summary) > 200:
                summary = summary[:200] + '...'
            return summary
        
        # Se não encontrou frases específicas, usar o resultado da análise
        return f"Decisão: {resultado_analysis['resultado']}"
    
    def _extract_main_reasoning(self, fundamentacao_text: str) -> str:
        """Extrai fundamentação principal"""
        if not fundamentacao_text:
            return "Fundamentação não identificada"
        
        # Extrair primeiras frases da fundamentação
        sentences = re.split(r'[.!?]+', fundamentacao_text)
        
        # Procurar por frases com fundamentação legal
        legal_keywords = [
            'conforme', 'segundo', 'de acordo com', 'previsto', 
            'estabelece', 'determina', 'artigo', 'lei', 'jurisprudência'
        ]
        
        important_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 30:  # Filtrar frases muito curtas
                for keyword in legal_keywords:
                    if keyword in sentence.lower():
                        important_sentences.append(sentence)
                        break
        
        if important_sentences:
            # Pegar as 2 frases mais importantes
            summary = '. '.join(important_sentences[:2])
            if len(summary) > 300:
                summary = summary[:300] + '...'
            return summary
        
        # Se não encontrou frases específicas, pegar início da fundamentação
        if len(fundamentacao_text) > 300:
            return fundamentacao_text[:300] + '...'
        
        return fundamentacao_text
    
    def _calculate_summary_confidence(self, resultado_analysis: Dict, pedidos: List, 
                                    valores: List, sections: Dict) -> float:
        """Calcula confiança do resumo"""
        confidence = 0.0
        
        # Confiança do resultado (peso 40%)
        resultado_conf = resultado_analysis.get('confidence', 0.0)
        confidence += resultado_conf * 0.4
        
        # Confiança dos pedidos (peso 20%)
        if pedidos:
            pedidos_conf = min(len(pedidos) / 5.0, 1.0)  # Máximo 5 pedidos
            confidence += pedidos_conf * 0.2
        
        # Confiança dos valores (peso 15%)
        if valores:
            valores_conf = min(len(valores) / 3.0, 1.0)  # Máximo 3 valores principais
            confidence += valores_conf * 0.15
        
        # Confiança das seções (peso 25%)
        sections_found = len([s for s in sections.values() if s])
        sections_conf = min(sections_found / 3.0, 1.0)  # Máximo 3 seções
        confidence += sections_conf * 0.25
        
        return min(confidence, 1.0)
    
    def format_summary_for_display(self, summary: StructuredSummary) -> str:
        """Formata resumo para exibição"""
        lines = []
        
        # Resultado principal
        lines.append(f"📋 Resultado: {summary.resultado_principal}")
        
        # Pedidos principais
        if summary.pedidos_principais:
            pedidos_str = ", ".join(summary.pedidos_principais)
            lines.append(f"⚖️ Pedidos: {pedidos_str}")
        
        # Valores envolvidos
        if summary.valores_envolvidos:
            valores_str = ", ".join([v['text'] for v in summary.valores_envolvidos[:3]])
            lines.append(f"💰 Valores: {valores_str}")
        
        # Decisão resumo
        if summary.decisao_resumo and summary.decisao_resumo != "Decisão não identificada":
            lines.append(f"🏛️ Decisão: {summary.decisao_resumo}")
        
        # Confiança
        conf_percent = int(summary.confidence_score * 100)
        lines.append(f"📊 Confiança: {conf_percent}%")
        
        return "\n".join(lines)
    
    def get_summary_statistics(self, summaries: List[StructuredSummary]) -> Dict[str, Any]:
        """Calcula estatísticas de um conjunto de resumos"""
        if not summaries:
            return {}
        
        # Resultados mais comuns
        resultados = [s.resultado_principal for s in summaries]
        resultado_counts = {}
        for resultado in resultados:
            resultado_counts[resultado] = resultado_counts.get(resultado, 0) + 1
        
        # Pedidos mais comuns
        all_pedidos = []
        for s in summaries:
            all_pedidos.extend(s.pedidos_principais)
        
        pedido_counts = {}
        for pedido in all_pedidos:
            pedido_counts[pedido] = pedido_counts.get(pedido, 0) + 1
        
        # Confiança média
        avg_confidence = sum(s.confidence_score for s in summaries) / len(summaries)
        
        return {
            'total_summaries': len(summaries),
            'average_confidence': avg_confidence,
            'most_common_results': sorted(resultado_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'most_common_requests': sorted(pedido_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'summaries_with_values': len([s for s in summaries if s.valores_envolvidos]),
            'high_confidence_summaries': len([s for s in summaries if s.confidence_score > 0.7])
        } 