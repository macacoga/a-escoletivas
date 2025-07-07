"""
Módulo de resumo extrativo para decisões judiciais
"""

import re
import math
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass

# Sumy imports
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer as SumyTokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.summarizers.lsa import LsaSummarizer

import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

from ..utils.logging import LoggerMixin, log_execution_time
from ..config.settings import settings


@dataclass
class SentenceScore:
    """Representa uma sentença com sua pontuação"""
    text: str
    score: float
    position: int
    length: int
    contains_keywords: bool = False
    is_legal_relevant: bool = False


class ExtractiveSummarizer(LoggerMixin):
    """
    Sumarizador extrativo especializado em decisões judiciais
    """
    
    def __init__(self):
        super().__init__()
        
        # Configurar tokenizer para português
        self.tokenizer = SumyTokenizer("portuguese")
        
        # Sumarizadores disponíveis
        self.summarizers = {
            'textrank': TextRankSummarizer(),
            'lexrank': LexRankSummarizer(),
            'luhn': LuhnSummarizer(),
            'lsa': LsaSummarizer()
        }
        
        # Palavras-chave importantes para contexto jurídico
        self.legal_keywords = {
            'decision_keywords': [
                'julgo', 'decido', 'determino', 'condeno', 'absolvo',
                'defiro', 'indefiro', 'acolho', 'rejeito', 'procedente',
                'improcedente', 'parcialmente procedente'
            ],
            'legal_terms': [
                'direito', 'lei', 'artigo', 'código', 'constituição',
                'jurisprudência', 'precedente', 'súmula', 'acórdão'
            ],
            'worker_rights': [
                'salário', 'horas extras', 'férias', 'FGTS', 'adicional',
                'indenização', 'rescisão', 'estabilidade', 'equiparação'
            ],
            'process_terms': [
                'autor', 'réu', 'reclamante', 'reclamado', 'empresa',
                'empregado', 'empregador', 'trabalhador'
            ]
        }
        
        # Padrões de sentenças importantes
        self.important_sentence_patterns = [
            r'(?:julgo|decido|determino|condeno)',
            r'(?:procedente|improcedente)',
            r'(?:defiro|indefiro|acolho|rejeito)',
            r'(?:reconheço|não reconheço)',
            r'(?:faz jus|tem direito|é devido)',
            r'(?:valor de|quantia de|importância de)',
            r'(?:fundamentação|ementa|dispositivo)'
        ]
    
    @log_execution_time
    def create_summary(self, 
                      text: str,
                      max_sentences: int = 10,
                      method: str = 'textrank',
                      include_context: bool = True) -> Dict[str, Any]:
        """
        Cria resumo extrativo do texto
        
        Args:
            text: Texto a ser sumarizado
            max_sentences: Número máximo de sentenças no resumo
            method: Método de sumarização ('textrank', 'lexrank', 'luhn', 'lsa', 'hybrid')
            include_context: Se True, inclui contexto adicional
            
        Returns:
            Dicionário com resumo e metadados
        """
        if not text or len(text.strip()) < 100:
            return self._empty_summary("Texto muito curto para sumarização")
        
        try:
            # Pré-processar texto
            processed_text = self._preprocess_for_summary(text)
            
            if method == 'hybrid':
                summary_result = self._create_hybrid_summary(processed_text, max_sentences)
            else:
                summary_result = self._create_single_method_summary(
                    processed_text, max_sentences, method
                )
            
            # Adicionar contexto se solicitado
            if include_context:
                summary_result['context'] = self._extract_context_info(text)
            
            # Calcular métricas
            summary_result['metrics'] = self._calculate_summary_metrics(
                text, summary_result['summary']
            )
            
            self.log_operation(
                "summary_created",
                original_length=len(text),
                summary_length=len(summary_result['summary']),
                compression_ratio=summary_result['metrics']['compression_ratio'],
                method=method
            )
            
            return summary_result
            
        except Exception as e:
            self.log_error(e, "create_summary", text_length=len(text), method=method)
            return self._empty_summary(f"Erro na sumarização: {str(e)}")
    
    def _preprocess_for_summary(self, text: str) -> str:
        """Pré-processa texto para sumarização"""
        try:
            # Remover múltiplos espaços
            text = re.sub(r'\s+', ' ', text)
            
            # Corrigir pontuação para melhor segmentação
            text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
            
            # Garantir que há espaço após pontos
            text = re.sub(r'\.([A-Z])', r'. \1', text)
            
            return text.strip()
            
        except Exception as e:
            self.log_error(e, "_preprocess_for_summary")
            return text
    
    def _create_single_method_summary(self, text: str, max_sentences: int, method: str) -> Dict[str, Any]:
        """Cria resumo usando um único método"""
        try:
            if method not in self.summarizers:
                method = 'textrank'
            
            # Criar parser
            parser = PlaintextParser.from_string(text, self.tokenizer)
            
            # Aplicar sumarizador
            summarizer = self.summarizers[method]
            summary_sentences = summarizer(parser.document, max_sentences)
            
            # Converter para texto
            summary_text = ' '.join(str(sentence) for sentence in summary_sentences)
            
            # Extrair sentenças originais
            original_sentences = [str(sentence) for sentence in summary_sentences]
            
            return {
                'summary': summary_text,
                'sentences': original_sentences,
                'method': method,
                'sentence_count': len(original_sentences)
            }
            
        except Exception as e:
            self.log_error(e, "_create_single_method_summary", method=method)
            return self._empty_summary(f"Erro no método {method}")
    
    def _create_hybrid_summary(self, text: str, max_sentences: int) -> Dict[str, Any]:
        """Cria resumo híbrido combinando múltiplos métodos"""
        try:
            # Dividir sentenças igualmente entre métodos
            sentences_per_method = max(1, max_sentences // len(self.summarizers))
            remaining_sentences = max_sentences % len(self.summarizers)
            
            all_sentences = []
            sentence_scores = defaultdict(float)
            
            # Aplicar cada método
            for i, (method_name, summarizer) in enumerate(self.summarizers.items()):
                try:
                    parser = PlaintextParser.from_string(text, self.tokenizer)
                    
                    # Ajustar número de sentenças
                    method_sentences = sentences_per_method
                    if i < remaining_sentences:
                        method_sentences += 1
                    
                    summary_sentences = summarizer(parser.document, method_sentences)
                    
                    # Pontuar sentenças
                    for sentence in summary_sentences:
                        sentence_text = str(sentence)
                        sentence_scores[sentence_text] += 1.0
                        
                        if sentence_text not in [s['text'] for s in all_sentences]:
                            all_sentences.append({
                                'text': sentence_text,
                                'methods': [method_name],
                                'score': 1.0
                            })
                        else:
                            # Encontrar e atualizar
                            for s in all_sentences:
                                if s['text'] == sentence_text:
                                    s['methods'].append(method_name)
                                    s['score'] += 1.0
                                    break
                
                except Exception as e:
                    self.logger.warning(f"Erro no método {method_name}: {e}")
                    continue
            
            # Aplicar scoring adicional baseado em importância jurídica
            for sentence_data in all_sentences:
                sentence_data['score'] += self._calculate_legal_importance(sentence_data['text'])
            
            # Ordenar por pontuação e selecionar top sentences
            all_sentences.sort(key=lambda x: x['score'], reverse=True)
            selected_sentences = all_sentences[:max_sentences]
            
            # Reordenar para manter ordem original no texto
            selected_sentences = self._reorder_by_original_position(text, selected_sentences)
            
            summary_text = ' '.join(s['text'] for s in selected_sentences)
            
            return {
                'summary': summary_text,
                'sentences': [s['text'] for s in selected_sentences],
                'method': 'hybrid',
                'sentence_count': len(selected_sentences),
                'method_distribution': self._analyze_method_distribution(selected_sentences)
            }
            
        except Exception as e:
            self.log_error(e, "_create_hybrid_summary")
            return self._empty_summary("Erro no resumo híbrido")
    
    def _calculate_legal_importance(self, sentence: str) -> float:
        """Calcula importância jurídica de uma sentença"""
        try:
            sentence_lower = sentence.lower()
            importance_score = 0.0
            
            # Verificar palavras-chave de decisão
            for keyword in self.legal_keywords['decision_keywords']:
                if keyword in sentence_lower:
                    importance_score += 1.0
            
            # Verificar termos jurídicos
            for keyword in self.legal_keywords['legal_terms']:
                if keyword in sentence_lower:
                    importance_score += 0.5
            
            # Verificar direitos trabalhistas
            for keyword in self.legal_keywords['worker_rights']:
                if keyword in sentence_lower:
                    importance_score += 0.7
            
            # Verificar padrões importantes
            for pattern in self.important_sentence_patterns:
                if re.search(pattern, sentence_lower):
                    importance_score += 0.8
            
            # Verificar presença de valores monetários
            if re.search(r'R\$\s*\d+', sentence):
                importance_score += 0.6
            
            # Verificar presença de artigos de lei
            if re.search(r'art\.?\s*\d+', sentence_lower):
                importance_score += 0.4
            
            return importance_score
            
        except Exception as e:
            self.log_error(e, "_calculate_legal_importance")
            return 0.0
    
    def _reorder_by_original_position(self, original_text: str, sentences: List[Dict]) -> List[Dict]:
        """Reordena sentenças pela posição original no texto"""
        try:
            for sentence_data in sentences:
                sentence_text = sentence_data['text']
                position = original_text.find(sentence_text)
                sentence_data['original_position'] = position if position != -1 else float('inf')
            
            # Ordenar por posição original
            sentences.sort(key=lambda x: x['original_position'])
            
            return sentences
            
        except Exception as e:
            self.log_error(e, "_reorder_by_original_position")
            return sentences
    
    def _analyze_method_distribution(self, sentences: List[Dict]) -> Dict[str, int]:
        """Analisa distribuição de métodos nas sentenças selecionadas"""
        try:
            method_count = defaultdict(int)
            
            for sentence_data in sentences:
                for method in sentence_data.get('methods', []):
                    method_count[method] += 1
            
            return dict(method_count)
            
        except Exception as e:
            self.log_error(e, "_analyze_method_distribution")
            return {}
    
    def _extract_context_info(self, text: str) -> Dict[str, Any]:
        """Extrai informações de contexto do texto"""
        try:
            context = {}
            
            # Identificar partes do processo
            parties_pattern = r'(?:autor|reclamante):\s*([^,\n]+)|(?:réu|reclamado):\s*([^,\n]+)'
            parties_matches = re.findall(parties_pattern, text, re.IGNORECASE)
            
            if parties_matches:
                context['parties'] = {
                    'plaintiff': [match[0] for match in parties_matches if match[0]],
                    'defendant': [match[1] for match in parties_matches if match[1]]
                }
            
            # Identificar números de processo
            process_pattern = r'\b\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}\b'
            process_numbers = re.findall(process_pattern, text)
            if process_numbers:
                context['process_numbers'] = list(set(process_numbers))
            
            # Identificar tribunal
            court_pattern = r'(TRT\s*\d+[ªº]?\s*Região|TST|STF|STJ)'
            courts = re.findall(court_pattern, text, re.IGNORECASE)
            if courts:
                context['courts'] = list(set(courts))
            
            # Identificar valores monetários
            money_pattern = r'R\$\s*\d+(?:[.,]\d{3})*(?:[.,]\d{2})?'
            monetary_values = re.findall(money_pattern, text)
            if monetary_values:
                context['monetary_values'] = list(set(monetary_values))
            
            return context
            
        except Exception as e:
            self.log_error(e, "_extract_context_info")
            return {}
    
    def _calculate_summary_metrics(self, original_text: str, summary: str) -> Dict[str, float]:
        """Calcula métricas do resumo"""
        try:
            original_words = len(original_text.split())
            summary_words = len(summary.split())
            
            original_sentences = len(re.split(r'[.!?]+', original_text))
            summary_sentences = len(re.split(r'[.!?]+', summary))
            
            compression_ratio = summary_words / original_words if original_words > 0 else 0
            sentence_ratio = summary_sentences / original_sentences if original_sentences > 0 else 0
            
            return {
                'original_words': original_words,
                'summary_words': summary_words,
                'original_sentences': original_sentences,
                'summary_sentences': summary_sentences,
                'compression_ratio': round(compression_ratio, 3),
                'sentence_ratio': round(sentence_ratio, 3)
            }
            
        except Exception as e:
            self.log_error(e, "_calculate_summary_metrics")
            return {}
    
    def _empty_summary(self, reason: str) -> Dict[str, Any]:
        """Retorna resumo vazio com motivo"""
        return {
            'summary': '',
            'sentences': [],
            'method': 'none',
            'sentence_count': 0,
            'error': reason,
            'metrics': {}
        }
    
    def create_structured_summary(self, text: str) -> Dict[str, Any]:
        """
        Cria resumo estruturado por seções
        
        Args:
            text: Texto da decisão
            
        Returns:
            Resumo estruturado por seções
        """
        try:
            sections = self._identify_sections(text)
            structured_summary = {}
            
            for section_name, section_text in sections.items():
                if len(section_text) > 100:  # Só sumarizar seções com conteúdo suficiente
                    section_summary = self.create_summary(
                        section_text, 
                        max_sentences=3,
                        method='textrank',
                        include_context=False
                    )
                    structured_summary[section_name] = section_summary['summary']
                else:
                    structured_summary[section_name] = section_text
            
            self.log_operation(
                "structured_summary_created",
                sections_identified=len(sections),
                sections_summarized=len(structured_summary)
            )
            
            return structured_summary
            
        except Exception as e:
            self.log_error(e, "create_structured_summary")
            return {}
    
    def _identify_sections(self, text: str) -> Dict[str, str]:
        """Identifica seções da decisão judicial"""
        try:
            sections = {}
            
            # Padrões para identificar seções
            section_patterns = {
                'relatório': r'(RELATÓRIO|RELATÓRIO:)(.*?)(?=FUNDAMENTAÇÃO|VOTO|EMENTA|$)',
                'fundamentação': r'(FUNDAMENTAÇÃO|VOTO|MÉRITO)(.*?)(?=DISPOSITIVO|CONCLUSÃO|$)',
                'dispositivo': r'(DISPOSITIVO|DECISÃO|ANTE O EXPOSTO)(.*?)(?=$)',
                'ementa': r'(EMENTA)(.*?)(?=RELATÓRIO|ACÓRDÃO|$)'
            }
            
            for section_name, pattern in section_patterns.items():
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    section_content = match.group(2).strip()
                    if section_content:
                        sections[section_name] = section_content
            
            # Se não encontrou seções específicas, tratar como texto único
            if not sections:
                sections['texto_completo'] = text
            
            return sections
            
        except Exception as e:
            self.log_error(e, "_identify_sections")
            return {'texto_completo': text}
    
    def batch_summarize(self, texts: List[str], **kwargs) -> List[Dict[str, Any]]:
        """
        Sumariza lista de textos em lote
        
        Args:
            texts: Lista de textos
            **kwargs: Argumentos para create_summary
            
        Returns:
            Lista de resumos
        """
        try:
            summaries = []
            
            for i, text in enumerate(texts):
                if i % 50 == 0:
                    self.logger.info(f"Sumarizando texto {i+1}/{len(texts)}")
                
                summary = self.create_summary(text, **kwargs)
                summaries.append(summary)
            
            self.log_operation(
                "batch_summarization_completed",
                total_texts=len(texts),
                successful_summaries=len([s for s in summaries if s.get('summary')])
            )
            
            return summaries
            
        except Exception as e:
            self.log_error(e, "batch_summarize", total_texts=len(texts))
            raise 