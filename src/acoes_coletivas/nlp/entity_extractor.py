"""
Módulo de extração de entidades nomeadas (NER) para decisões judiciais
"""

import spacy
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
from collections import defaultdict, Counter

from ..utils.logging import LoggerMixin, log_execution_time
from ..config.settings import settings


@dataclass
class Entity:
    """Representa uma entidade extraída"""
    text: str
    label: str
    start: int
    end: int
    confidence: float = 0.0
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte entidade para dicionário"""
        return {
            'text': self.text,
            'label': self.label,
            'start': self.start,
            'end': self.end,
            'confidence': self.confidence,
            'description': self.description
        }


class EntityExtractor(LoggerMixin):
    """
    Classe para extração de entidades nomeadas de decisões judiciais
    """
    
    def __init__(self, model_name: str = "pt_core_news_sm"):
        super().__init__()
        
        self.model_name = model_name
        self.nlp = None
        
        # Configurações de entidades personalizadas
        self.custom_patterns = {
            # Números de processos
            'PROCESSO': [
                r'\b\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}\b',
                r'\b\d{4}\.\d{3}\.\d{3}\.\d{3}\.\d{1}\.\d{2}\.\d{4}\b'
            ],
            
            # Valores monetários
            'MONEY': [
                r'R\$\s*\d+(?:[.,]\d{3})*(?:[.,]\d{2})?',
                r'\d+(?:[.,]\d{3})*(?:[.,]\d{2})?\s*reais?',
                r'valor de\s+R\$\s*\d+(?:[.,]\d{3})*(?:[.,]\d{2})?'
            ],
            
            # Datas específicas
            'DATE': [
                r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b',
                r'\b(?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+\d{4}\b'
            ],
            
            # Leis e artigos
            'LAW': [
                r'(?:art\.?|artigo)\s*\d+(?:º|°)?(?:\s*,\s*(?:§|parágrafo)\s*\d+(?:º|°)?)?(?:\s*da\s+CLT|do\s+CC|da\s+CF)?',
                r'CLT\s*,?\s*art\.?\s*\d+',
                r'Lei\s+n[º°]?\s*\d+[\.,/]\d+',
                r'Súmula\s+n[º°]?\s*\d+'
            ],
            
            # Tribunais
            'COURT': [
                r'TST|TRT\s*\d+[ªº]?\s*Região|STF|STJ',
                r'Tribunal\s+(?:Superior\s+do\s+)?Trabalho',
                r'Supremo\s+Tribunal\s+Federal',
                r'Superior\s+Tribunal\s+de\s+Justiça',
                r'\d+[ªº]?\s*Vara\s+do\s+Trabalho'
            ],
            
            # Direitos trabalhistas
            'WORKER_RIGHT': [
                r'horas?\s+extras?',
                r'adicional\s+noturno',
                r'insalubridade',
                r'periculosidade',
                r'vale[\-\s]transporte',
                r'vale[\-\s]alimentação',
                r'vale[\-\s]refeição',
                r'equiparação\s+salarial',
                r'décimo\s+terceiro|13[º°]\s+salário',
                r'férias?\s+proporcionais?',
                r'aviso\s+prévio',
                r'multa\s+do\s+FGTS',
                r'estabilidade\s+provisória',
                r'indenização\s+por\s+danos?\s+morais?'
            ]
        }
        
        # Mapeamento de labels do spaCy para descrições
        self.label_descriptions = {
            'PER': 'Pessoa',
            'ORG': 'Organização',
            'LOC': 'Local',
            'MISC': 'Miscelânea',
            'MONEY': 'Valor monetário',
            'DATE': 'Data',
            'TIME': 'Horário',
            'PROCESSO': 'Número do processo',
            'LAW': 'Lei/Artigo',
            'COURT': 'Tribunal/Vara',
            'WORKER_RIGHT': 'Direito trabalhista'
        }
        
        # Carregar modelo
        self._load_model()
    
    def _load_model(self):
        """Carrega o modelo spaCy"""
        try:
            self.nlp = spacy.load(self.model_name)
            self.logger.info(f"Modelo spaCy carregado: {self.model_name}")
            
            # Adicionar patterns customizados
            self._add_custom_patterns()
            
        except IOError:
            self.logger.error(f"Modelo spaCy não encontrado: {self.model_name}")
            self.logger.info("Execute: python -m spacy download pt_core_news_sm")
            raise
        except Exception as e:
            self.log_error(e, "_load_model")
            raise
    
    def _add_custom_patterns(self):
        """Adiciona patterns customizados ao pipeline"""
        try:
            # Criar entity ruler
            if self.nlp and "entity_ruler" not in self.nlp.pipe_names:
                ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            else:
                ruler = self.nlp.get_pipe("entity_ruler") if self.nlp else None
            
            # Adicionar patterns
            patterns = []
            
            for label, regex_patterns in self.custom_patterns.items():
                for pattern in regex_patterns:
                    patterns.append({
                        "label": label,
                        "pattern": [{"TEXT": {"REGEX": pattern}}]
                    })
            
            if ruler:
                ruler.add_patterns(patterns)
            
            self.logger.info(f"Adicionados {len(patterns)} patterns customizados")
            
        except Exception as e:
            self.log_error(e, "_add_custom_patterns")
    
    @log_execution_time
    def extract_entities(self, text: str, include_custom: bool = True) -> List[Entity]:
        """
        Extrai entidades nomeadas do texto
        
        Args:
            text: Texto para análise
            include_custom: Se True, inclui entidades customizadas
            
        Returns:
            Lista de entidades extraídas
        """
        if not text or not self.nlp:
            return []
        
        try:
            # Processar texto com spaCy
            doc = self.nlp(text)
            
            entities = []
            
            # Extrair entidades do spaCy
            for ent in doc.ents:
                entity = Entity(
                    text=ent.text.strip(),
                    label=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=getattr(ent, 'confidence', 0.8),
                    description=self.label_descriptions.get(ent.label_, ent.label_)
                )
                entities.append(entity)
            
            # Extrair entidades customizadas com regex se solicitado
            if include_custom:
                custom_entities = self._extract_custom_entities(text)
                entities.extend(custom_entities)
            
            # Remover duplicatas e sobreposições
            entities = self._remove_overlapping_entities(entities)
            
            self.log_operation(
                "entities_extracted",
                text_length=len(text),
                entities_found=len(entities),
                entity_types=len(set(e.label for e in entities))
            )
            
            return entities
            
        except Exception as e:
            self.log_error(e, "extract_entities", text_length=len(text))
            return []
    
    def _extract_custom_entities(self, text: str) -> List[Entity]:
        """Extrai entidades usando regex customizados"""
        entities = []
        
        try:
            for label, patterns in self.custom_patterns.items():
                for pattern in patterns:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        entity = Entity(
                            text=match.group().strip(),
                            label=label,
                            start=match.start(),
                            end=match.end(),
                            confidence=0.9,  # Alta confiança para patterns específicos
                            description=self.label_descriptions.get(label, label)
                        )
                        entities.append(entity)
            
            return entities
            
        except Exception as e:
            self.log_error(e, "_extract_custom_entities")
            return []
    
    def _remove_overlapping_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove entidades sobrepostas, mantendo as de maior confiança"""
        if not entities:
            return []
        
        try:
            # Ordenar por posição
            sorted_entities = sorted(entities, key=lambda x: (x.start, x.end))
            
            filtered_entities = []
            
            for current in sorted_entities:
                # Verificar sobreposição com entidades já filtradas
                overlaps = False
                
                for existing in filtered_entities:
                    # Verificar se há sobreposição
                    if (current.start < existing.end and current.end > existing.start):
                        # Há sobreposição - manter a de maior confiança
                        if current.confidence > existing.confidence:
                            # Remover a entidade existente e adicionar a atual
                            filtered_entities.remove(existing)
                            filtered_entities.append(current)
                        overlaps = True
                        break
                
                if not overlaps:
                    filtered_entities.append(current)
            
            return filtered_entities
            
        except Exception as e:
            self.log_error(e, "_remove_overlapping_entities")
            return entities
    
    def analyze_entities_by_type(self, entities: List[Entity]) -> Dict[str, Any]:
        """
        Analisa entidades por tipo
        
        Args:
            entities: Lista de entidades
            
        Returns:
            Análise estatística das entidades
        """
        try:
            if not entities:
                return {}
            
            # Contar por tipo
            type_counts = Counter(e.label for e in entities)
            
            # Agrupar por tipo
            entities_by_type = defaultdict(list)
            for entity in entities:
                entities_by_type[entity.label].append(entity.text)
            
            # Calcular estatísticas
            analysis = {
                'total_entities': len(entities),
                'unique_types': len(type_counts),
                'type_distribution': dict(type_counts),
                'entities_by_type': {},
                'most_common_entities': {},
                'confidence_stats': {
                    'average': sum(e.confidence for e in entities) / len(entities),
                    'min': min(e.confidence for e in entities),
                    'max': max(e.confidence for e in entities)
                }
            }
            
            # Detalhes por tipo
            for entity_type, entity_list in entities_by_type.items():
                unique_entities = list(set(entity_list))
                entity_counts = Counter(entity_list)
                
                analysis['entities_by_type'][entity_type] = {
                    'count': len(entity_list),
                    'unique_count': len(unique_entities),
                    'entities': unique_entities[:10],  # Top 10
                    'most_common': entity_counts.most_common(5)
                }
            
            self.log_operation(
                "entities_analyzed",
                total_entities=analysis['total_entities'],
                unique_types=analysis['unique_types']
            )
            
            return analysis
            
        except Exception as e:
            self.log_error(e, "analyze_entities_by_type")
            return {}
    
    def extract_worker_rights(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrai especificamente direitos trabalhistas mencionados
        
        Args:
            text: Texto para análise
            
        Returns:
            Lista de direitos trabalhistas encontrados
        """
        try:
            rights_found = []
            
            # Dictionary de direitos trabalhistas com padrões
            worker_rights_patterns = {
                'horas_extras': [
                    r'hora[s]?\s+extra[s]?',
                    r'sobrejornada',
                    r'trabalho\s+extraordinário'
                ],
                'adicional_noturno': [
                    r'adicional\s+noturno',
                    r'trabalho\s+noturno'
                ],
                'insalubridade': [
                    r'insalubridade',
                    r'adicional\s+de\s+insalubridade'
                ],
                'periculosidade': [
                    r'periculosidade',
                    r'adicional\s+de\s+periculosidade'
                ],
                'vale_transporte': [
                    r'vale[\-\s]?transporte',
                    r'auxílio[\-\s]?transporte'
                ],
                'vale_alimentacao': [
                    r'vale[\-\s]?alimentação',
                    r'vale[\-\s]?refeição',
                    r'auxílio[\-\s]?alimentação'
                ],
                'equiparacao_salarial': [
                    r'equiparação\s+salarial',
                    r'isonomia\s+salarial'
                ],
                'decimo_terceiro': [
                    r'décimo\s+terceiro',
                    r'13[º°]\s+salário',
                    r'gratificação\s+natalina'
                ],
                'ferias': [
                    r'férias?\s+(?:proporcionais?|vencidas?|em\s+dobro)?',
                    r'período\s+de\s+férias'
                ],
                'aviso_previo': [
                    r'aviso\s+prévio',
                    r'pré[\-\s]?aviso'
                ],
                'fgts': [
                    r'FGTS',
                    r'Fundo\s+de\s+Garantia',
                    r'multa\s+do\s+FGTS'
                ],
                'estabilidade': [
                    r'estabilidade\s+(?:provisória|no\s+emprego)?',
                    r'garantia\s+no\s+emprego'
                ],
                'indenizacao': [
                    r'indenização\s+por\s+danos?\s+morais?',
                    r'danos?\s+morais?',
                    r'indenização\s+compensatória'
                ]
            }
            
            text_lower = text.lower()
            
            for right_type, patterns in worker_rights_patterns.items():
                matches = []
                
                for pattern in patterns:
                    for match in re.finditer(pattern, text_lower):
                        matches.append({
                            'text': text[match.start():match.end()],
                            'start': match.start(),
                            'end': match.end(),
                            'pattern': pattern
                        })
                
                if matches:
                    rights_found.append({
                        'type': right_type,
                        'description': right_type.replace('_', ' ').title(),
                        'matches': matches,
                        'count': len(matches)
                    })
            
            self.log_operation(
                "worker_rights_extracted",
                text_length=len(text),
                rights_types_found=len(rights_found),
                total_mentions=sum(r['count'] for r in rights_found)
            )
            
            return rights_found
            
        except Exception as e:
            self.log_error(e, "extract_worker_rights")
            return []
    
    def extract_monetary_values(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrai valores monetários do texto
        
        Args:
            text: Texto para análise
            
        Returns:
            Lista de valores monetários encontrados
        """
        try:
            monetary_patterns = [
                r'R\$\s*(\d+(?:[.,]\d{3})*(?:[.,]\d{2})?)',
                r'(\d+(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*reais?',
                r'valor\s+de\s+R\$\s*(\d+(?:[.,]\d{3})*(?:[.,]\d{2})?)',
                r'quantia\s+de\s+R\$\s*(\d+(?:[.,]\d{3})*(?:[.,]\d{2})?)',
                r'importância\s+de\s+R\$\s*(\d+(?:[.,]\d{3})*(?:[.,]\d{2})?)'
            ]
            
            values_found = []
            
            for pattern in monetary_patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    # Extrair o valor numérico
                    value_text = match.group(1) if match.groups() else match.group()
                    
                    # Limpar e converter valor
                    cleaned_value = re.sub(r'[^\d,.]', '', value_text)
                    
                    try:
                        # Converter para float (assumindo formato brasileiro)
                        if ',' in cleaned_value and '.' in cleaned_value:
                            # Formato: 1.234.567,89
                            numeric_value = float(cleaned_value.replace('.', '').replace(',', '.'))
                        elif ',' in cleaned_value:
                            # Formato: 1234,89
                            numeric_value = float(cleaned_value.replace(',', '.'))
                        else:
                            # Formato: 1234.89 ou 1234
                            numeric_value = float(cleaned_value)
                        
                        values_found.append({
                            'text': match.group(),
                            'value': numeric_value,
                            'start': match.start(),
                            'end': match.end(),
                            'formatted_value': f"R$ {numeric_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                        })
                        
                    except ValueError:
                        # Não foi possível converter, manter como texto
                        values_found.append({
                            'text': match.group(),
                            'value': None,
                            'start': match.start(),
                            'end': match.end(),
                            'raw_value': value_text
                        })
            
            # Remover duplicatas baseado na posição
            unique_values = []
            seen_positions = set()
            
            for value in values_found:
                position = (value['start'], value['end'])
                if position not in seen_positions:
                    unique_values.append(value)
                    seen_positions.add(position)
            
            self.log_operation(
                "monetary_values_extracted",
                text_length=len(text),
                values_found=len(unique_values),
                total_value=sum(v['value'] for v in unique_values if v.get('value'))
            )
            
            return unique_values
            
        except Exception as e:
            self.log_error(e, "extract_monetary_values")
            return []
    
    def batch_extract_entities(self, texts: List[str]) -> List[List[Entity]]:
        """
        Extrai entidades de uma lista de textos em lote
        
        Args:
            texts: Lista de textos
            
        Returns:
            Lista de listas de entidades
        """
        try:
            all_entities = []
            
            for i, text in enumerate(texts):
                if i % 50 == 0:
                    self.logger.info(f"Processando texto {i+1}/{len(texts)}")
                
                entities = self.extract_entities(text)
                all_entities.append(entities)
            
            self.log_operation(
                "batch_entity_extraction_completed",
                total_texts=len(texts),
                total_entities=sum(len(entities) for entities in all_entities)
            )
            
            return all_entities
            
        except Exception as e:
            self.log_error(e, "batch_extract_entities", total_texts=len(texts))
            raise
    
    def entities_to_json(self, entities: List[Entity]) -> str:
        """
        Converte lista de entidades para JSON
        
        Args:
            entities: Lista de entidades
            
        Returns:
            String JSON
        """
        try:
            entities_dict = []
            
            for entity in entities:
                entities_dict.append({
                    'text': entity.text,
                    'label': entity.label,
                    'start': entity.start,
                    'end': entity.end,
                    'confidence': entity.confidence,
                    'description': entity.description
                })
            
            return json.dumps(entities_dict, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.log_error(e, "entities_to_json")
            return "[]" 