"""
Pipeline completo de processamento de linguagem natural para decisões judiciais
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
from datetime import datetime

from .text_preprocessor import TextPreprocessor
from .entity_extractor import EntityExtractor, Entity
from .rights_analyzer import RightsAnalyzer, WorkerRight
from .extractive_summarizer import ExtractiveSummarizer
from ..utils.logging import LoggerMixin, log_execution_time
from ..config.settings import settings


@dataclass
class NLPResults:
    """Resultados completos do processamento NLP"""
    processo_id: str
    original_text: str
    processed_text: str
    text_quality: Dict[str, Any]
    entities: List[Entity]
    worker_rights: List[WorkerRight]
    summary: Dict[str, Any]
    processing_time: float
    created_at: datetime
    confidence_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'processo_id': self.processo_id,
            'original_text_length': len(self.original_text),
            'processed_text_length': len(self.processed_text),
            'text_quality': self.text_quality,
            'entities': [
                {
                    'text': e.text,
                    'label': e.label,
                    'start': e.start,
                    'end': e.end,
                    'confidence': e.confidence,
                    'description': e.description
                }
                for e in self.entities
            ],
            'worker_rights': [
                {
                    'type': r.type,
                    'description': r.description,
                    'mentions': r.mentions,
                    'decision_outcome': r.decision_outcome,
                    'confidence': r.confidence
                }
                for r in self.worker_rights
            ],
            'summary': self.summary,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat(),
            'confidence_score': self.confidence_score
        }


class NLPPipeline(LoggerMixin):
    """
    Pipeline completo de processamento NLP para decisões judiciais
    """
    
    def __init__(self):
        super().__init__()
        
        # Inicializar componentes
        self.text_preprocessor = TextPreprocessor()
        self.entity_extractor = EntityExtractor()
        self.rights_analyzer = RightsAnalyzer()
        self.extractive_summarizer = ExtractiveSummarizer()
        
        # Configurações
        self.min_text_length = settings.nlp_min_text_length
        self.max_text_length = settings.nlp_max_text_length
        self.min_quality_score = 0.3
        
        self.logger.info("Pipeline NLP inicializado com sucesso")
    
    @log_execution_time
    def process_text(self, 
                    text: str, 
                    processo_id: str,
                    include_summary: bool = True,
                    include_entities: bool = True,
                    include_rights: bool = True,
                    summary_method: str = 'textrank') -> NLPResults:
        """
        Processa texto completo através do pipeline NLP
        
        Args:
            text: Texto da decisão judicial
            processo_id: ID do processo
            include_summary: Se True, inclui resumo
            include_entities: Se True, extrai entidades
            include_rights: Se True, analisa direitos
            summary_method: Método de sumarização
            
        Returns:
            Resultados completos do processamento
        """
        start_time = datetime.now()
        
        try:
            # Validar entrada
            if not text or not text.strip():
                raise ValueError("Texto vazio ou nulo")
            
            if len(text) < self.min_text_length:
                raise ValueError(f"Texto muito curto (min: {self.min_text_length} chars)")
            
            if len(text) > self.max_text_length:
                self.logger.warning(f"Texto muito longo ({len(text)} chars), truncando")
                text = text[:self.max_text_length]
            
            # Etapa 1: Pré-processamento
            self.logger.info(f"Iniciando pré-processamento do processo {processo_id}")
            processed_text = self.text_preprocessor.preprocess_text(
                text,
                remove_html=True,
                clean_encoding=True,
                normalize_spaces=True,
                remove_headers_footers=True,
                preserve_structure=True
            )
            
            # Validar qualidade do texto
            text_quality = self.text_preprocessor.validate_text_quality(processed_text)
            
            if text_quality['quality_score'] < self.min_quality_score:
                self.logger.warning(f"Texto de baixa qualidade: {text_quality['quality_score']:.2f}")
            
            # Etapa 2: Extração de entidades (se solicitado)
            entities = []
            if include_entities:
                self.logger.info(f"Extraindo entidades do processo {processo_id}")
                entities = self.entity_extractor.extract_entities(processed_text)
            
            # Etapa 3: Análise de direitos trabalhistas (se solicitado)
            worker_rights = []
            if include_rights:
                self.logger.info(f"Analisando direitos trabalhistas do processo {processo_id}")
                worker_rights = self.rights_analyzer.analyze_rights(processed_text)
            
            # Etapa 4: Resumo extrativo (se solicitado)
            summary = {}
            if include_summary:
                self.logger.info(f"Criando resumo do processo {processo_id}")
                summary = self.extractive_summarizer.create_summary(
                    processed_text,
                    max_sentences=settings.nlp_sentence_count,
                    method=summary_method,
                    include_context=True
                )
            
            # Calcular tempo de processamento
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Calcular score de confiança global
            confidence_score = self._calculate_global_confidence(
                text_quality, entities, worker_rights, summary
            )
            
            # Criar resultado
            results = NLPResults(
                processo_id=processo_id,
                original_text=text,
                processed_text=processed_text,
                text_quality=text_quality,
                entities=entities,
                worker_rights=worker_rights,
                summary=summary,
                processing_time=processing_time,
                created_at=datetime.now(),
                confidence_score=confidence_score
            )
            
            self.log_operation(
                "text_processing_completed",
                processo_id=processo_id,
                original_length=len(text),
                processed_length=len(processed_text),
                entities_found=len(entities),
                rights_found=len(worker_rights),
                processing_time=processing_time,
                confidence_score=confidence_score
            )
            
            return results
            
        except Exception as e:
            self.log_error(e, "process_text", processo_id=processo_id)
            raise
    
    def _calculate_global_confidence(self, 
                                   text_quality: Dict[str, Any],
                                   entities: List[Entity],
                                   worker_rights: List[WorkerRight],
                                   summary: Dict[str, Any]) -> float:
        """Calcula score de confiança global do processamento"""
        try:
            confidence_components = []
            
            # Componente 1: Qualidade do texto (peso 0.3)
            text_score = text_quality.get('quality_score', 0.5)
            confidence_components.append(text_score * 0.3)
            
            # Componente 2: Confiança das entidades (peso 0.2)
            if entities:
                entity_confidence = sum(e.confidence for e in entities) / len(entities)
                confidence_components.append(entity_confidence * 0.2)
            else:
                confidence_components.append(0.1)  # Penalizar falta de entidades
            
            # Componente 3: Confiança dos direitos (peso 0.3)
            if worker_rights:
                rights_confidence = sum(r.confidence for r in worker_rights) / len(worker_rights)
                confidence_components.append(rights_confidence * 0.3)
            else:
                confidence_components.append(0.1)  # Penalizar falta de direitos
            
            # Componente 4: Qualidade do resumo (peso 0.2)
            if summary and summary.get('summary'):
                summary_score = min(1.0, len(summary['summary'].split()) / 100)  # Assumindo 100 palavras como ideal
                confidence_components.append(summary_score * 0.2)
            else:
                confidence_components.append(0.1)
            
            return sum(confidence_components)
            
        except Exception as e:
            self.log_error(e, "_calculate_global_confidence")
            return 0.5
    
    def batch_process(self, 
                     texts_data: List[Dict[str, str]], 
                     **kwargs) -> List[NLPResults]:
        """
        Processa múltiplos textos em lote
        
        Args:
            texts_data: Lista de dicionários com 'text' e 'processo_id'
            **kwargs: Argumentos para process_text
            
        Returns:
            Lista de resultados
        """
        try:
            results = []
            total_texts = len(texts_data)
            
            for i, text_data in enumerate(texts_data):
                if i % 10 == 0:
                    self.logger.info(f"Processando texto {i+1}/{total_texts}")
                
                try:
                    result = self.process_text(
                        text_data['text'],
                        text_data['processo_id'],
                        **kwargs
                    )
                    results.append(result)
                    
                except Exception as e:
                    self.log_error(e, "batch_process_item", 
                                 processo_id=text_data.get('processo_id', 'unknown'))
                    continue
            
            self.log_operation(
                "batch_processing_completed",
                total_texts=total_texts,
                successful_processed=len(results),
                error_rate=(total_texts - len(results)) / total_texts if total_texts > 0 else 0
            )
            
            return results
            
        except Exception as e:
            self.log_error(e, "batch_process", total_texts=len(texts_data))
            raise
    
    def create_analysis_report(self, results: List[NLPResults]) -> Dict[str, Any]:
        """
        Cria relatório de análise dos resultados
        
        Args:
            results: Lista de resultados do processamento
            
        Returns:
            Relatório de análise
        """
        try:
            if not results:
                return {}
            
            # Estatísticas gerais
            total_processes = len(results)
            avg_processing_time = sum(r.processing_time for r in results) / total_processes
            avg_confidence = sum(r.confidence_score for r in results) / total_processes
            
            # Estatísticas de qualidade
            quality_scores = [r.text_quality.get('quality_score', 0) for r in results]
            avg_quality = sum(quality_scores) / len(quality_scores)
            
            # Estatísticas de entidades
            total_entities = sum(len(r.entities) for r in results)
            entity_types = {}
            for result in results:
                for entity in result.entities:
                    entity_types[entity.label] = entity_types.get(entity.label, 0) + 1
            
            # Estatísticas de direitos
            total_rights = sum(len(r.worker_rights) for r in results)
            rights_types = {}
            rights_outcomes = {'granted': 0, 'denied': 0, 'partially_granted': 0, 'unknown': 0}
            
            for result in results:
                for right in result.worker_rights:
                    rights_types[right.type] = rights_types.get(right.type, 0) + 1
                    outcome = right.decision_outcome or 'unknown'
                    rights_outcomes[outcome] = rights_outcomes.get(outcome, 0) + 1
            
            # Estatísticas de resumos
            successful_summaries = len([r for r in results if r.summary.get('summary')])
            avg_compression_ratio = 0
            if successful_summaries > 0:
                compression_ratios = [
                    r.summary.get('metrics', {}).get('compression_ratio', 0) 
                    for r in results if r.summary.get('metrics', {}).get('compression_ratio')
                ]
                if compression_ratios:
                    avg_compression_ratio = sum(compression_ratios) / len(compression_ratios)
            
            # Criar relatório
            report = {
                'general_stats': {
                    'total_processes': total_processes,
                    'avg_processing_time': round(avg_processing_time, 2),
                    'avg_confidence_score': round(avg_confidence, 2),
                    'avg_quality_score': round(avg_quality, 2)
                },
                'entity_stats': {
                    'total_entities': total_entities,
                    'avg_entities_per_process': round(total_entities / total_processes, 1),
                    'entity_type_distribution': dict(sorted(entity_types.items(), key=lambda x: x[1], reverse=True))
                },
                'rights_stats': {
                    'total_rights': total_rights,
                    'avg_rights_per_process': round(total_rights / total_processes, 1),
                    'rights_type_distribution': dict(sorted(rights_types.items(), key=lambda x: x[1], reverse=True)),
                    'outcome_distribution': rights_outcomes
                },
                'summary_stats': {
                    'successful_summaries': successful_summaries,
                    'success_rate': round(successful_summaries / total_processes, 2),
                    'avg_compression_ratio': round(avg_compression_ratio, 2)
                },
                'quality_distribution': {
                    'high_quality': len([s for s in quality_scores if s >= 0.8]),
                    'medium_quality': len([s for s in quality_scores if 0.5 <= s < 0.8]),
                    'low_quality': len([s for s in quality_scores if s < 0.5])
                }
            }
            
            self.log_operation(
                "analysis_report_created",
                total_processes=total_processes,
                avg_confidence=avg_confidence,
                total_entities=total_entities,
                total_rights=total_rights
            )
            
            return report
            
        except Exception as e:
            self.log_error(e, "create_analysis_report")
            return {}
    
    def export_results_to_json(self, results: List[NLPResults], filepath: str = None) -> str:
        """
        Exporta resultados para JSON
        
        Args:
            results: Lista de resultados
            filepath: Caminho para salvar arquivo (opcional)
            
        Returns:
            String JSON ou caminho do arquivo salvo
        """
        try:
            export_data = {
                'metadata': {
                    'total_processes': len(results),
                    'export_date': datetime.now().isoformat(),
                    'pipeline_version': '1.0.0'
                },
                'results': [result.to_dict() for result in results]
            }
            
            json_string = json.dumps(export_data, ensure_ascii=False, indent=2)
            
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(json_string)
                
                self.log_operation(
                    "results_exported",
                    filepath=filepath,
                    total_processes=len(results)
                )
                
                return filepath
            
            return json_string
            
        except Exception as e:
            self.log_error(e, "export_results_to_json")
            raise
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do pipeline
        
        Returns:
            Estatísticas dos componentes
        """
        try:
            stats = {
                'components': {
                    'text_preprocessor': type(self.text_preprocessor).__name__,
                    'entity_extractor': type(self.entity_extractor).__name__,
                    'rights_analyzer': type(self.rights_analyzer).__name__,
                    'extractive_summarizer': type(self.extractive_summarizer).__name__
                },
                'configuration': {
                    'min_text_length': self.min_text_length,
                    'max_text_length': self.max_text_length,
                    'min_quality_score': self.min_quality_score
                },
                'capabilities': {
                    'text_preprocessing': True,
                    'entity_extraction': True,
                    'rights_analysis': True,
                    'extractive_summarization': True,
                    'batch_processing': True
                }
            }
            
            return stats
            
        except Exception as e:
            self.log_error(e, "get_pipeline_stats")
            return {}
    
    def validate_pipeline(self) -> Dict[str, bool]:
        """
        Valida se todos os componentes do pipeline estão funcionando
        
        Returns:
            Status de validação de cada componente
        """
        validation_results = {}
        
        # Testar preprocessador
        try:
            test_text = "Este é um texto de teste para validação do pipeline."
            self.text_preprocessor.preprocess_text(test_text)
            validation_results['text_preprocessor'] = True
        except Exception as e:
            self.log_error(e, "validate_text_preprocessor")
            validation_results['text_preprocessor'] = False
        
        # Testar extrator de entidades
        try:
            test_text = "O Banco do Brasil deve pagar R$ 1.000,00 ao trabalhador."
            self.entity_extractor.extract_entities(test_text)
            validation_results['entity_extractor'] = True
        except Exception as e:
            self.log_error(e, "validate_entity_extractor")
            validation_results['entity_extractor'] = False
        
        # Testar analisador de direitos
        try:
            test_text = "O trabalhador tem direito a horas extras e adicional noturno."
            self.rights_analyzer.analyze_rights(test_text)
            validation_results['rights_analyzer'] = True
        except Exception as e:
            self.log_error(e, "validate_rights_analyzer")
            validation_results['rights_analyzer'] = False
        
        # Testar sumarizador
        try:
            test_text = "Esta é uma decisão judicial teste. O trabalhador pleiteou direitos trabalhistas. O juiz decidiu pela procedência do pedido."
            self.extractive_summarizer.create_summary(test_text)
            validation_results['extractive_summarizer'] = True
        except Exception as e:
            self.log_error(e, "validate_extractive_summarizer")
            validation_results['extractive_summarizer'] = False
        
        # Status geral
        all_valid = all(validation_results.values())
        validation_results['pipeline_valid'] = all_valid
        
        if all_valid:
            self.logger.info("Pipeline validado com sucesso - todos os componentes funcionando")
        else:
            failed_components = [comp for comp, status in validation_results.items() if not status]
            self.logger.error(f"Falha na validação dos componentes: {failed_components}")
        
        return validation_results 