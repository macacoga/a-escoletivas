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
            "text": self.text,
            "label": self.label,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "description": self.description,
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
            "PROCESSO": [
                # Novo formato CNJ (7 dígitos - 2 dígitos . 4 dígitos . 1 dígito . 2 dígitos . 4 dígitos)
                r"\b\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}\b",
                # Formato antigo/livre (com ou sem pontos/hífens)
                r"\b\d{4}[.\s]?\d{3}[.\s]?\d{3}[.\s]?\d{3}[.\s]?\d{1}[.\s]?\d{2}[.\s]?\d{4}\b",
                # Variações para "Processo n." ou "Autos n."
                r"(?:Processo|Autos)\s+n[º°]?\s*\b\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}\b",
            ],
            # Valores monetários
            "MONEY": [
                # R$ com ou sem espaço, com separador de milhar (ponto ou vírgula) e decimal (vírgula ou ponto)
                r"R\$\s*\d{1,3}(?:\.?\d{3})*(?:,\d{2})?",  # Ex: R$ 1.234,56 ou R$ 1234,56
                r"R\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?",  # Ex: R$ 1,234.56 (menos comum no BR, mas pode aparecer)
                # Valores numéricos seguidos por "reais" (plural e singular) ou "milhões", "bilhões"
                r"\d{1,3}(?:\.?\d{3})*(?:,\d{2})?\s*(?:reais?|milhões?|bilhões?)",
                # Expressões como "valor de R$"
                r"(?:valor|montante)\s+(?:de|em)\s+R\$\s*\d{1,3}(?:\.?\d{3})*(?:,\d{2})?",
                # Formatos que incluem "mil" ou abreviações
                r"\d+(?:\s*mil)?(?:\s*e\s*\d{1,3})?\s*reais",  # Ex: "duzentos mil reais", "cem e vinte reais"
            ],
            # Datas específicas
            "DATE": [
                # Formatos DD/MM/AAAA, DD.MM.AAAA, DD-MM-AAAA (com 2 ou 4 dígitos no ano)
                r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b",
                # Formato extenso: "dia de mês de ano" (com flexibilidade no dia)
                r"\b\d{1,2}\s+de\s+(?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+\d{4}\b",
                # Apenas mês e ano: "mês de ano"
                r"\b(?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+\d{4}\b",
                # "dia do mês" (menos comum para extração de data completa, mas pode ser útil)
                r"\b\d{1,2}\s+de\s+(?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b",
                # Períodos como "ano de XXXX"
                r"\b(?:ano)\s+de\s+\d{4}\b",
            ],
            # Leis e artigos
            "LAW": [
                # Artigos (com ou sem 'caput', parágrafos, incisos, alíneas)
                r"(?:art\.?|artigo)\s*\d+(?:º|°)?(?:\s*,?\s*caput)?(?:\s*,?\s*(?:§|parágrafo)\s*\d+(?:º|°)?)?(?:\s*,\s*inciso\s+[IVXLCDM]+)?(?:\s*,\s*alínea\s+[a-z])?(?:\s+da\s+(?:CLT|CF|CC|CP|CPC|CDC|LSA|Lei\s+\d+|DL\s+\d+|Súmula\s+\d+))?",
                # Referências diretas a códigos e leis
                r"\bCLT\b|Consolidação das Leis do Trabalho",
                r"\bCF\b|Constituição Federal",
                r"\bCC\b|Código Civil",
                r"\bCPC\b|Código de Processo Civil",
                r"\bLei\s+n[º°]?\s*\d+(?:\.\d{3})*(?:[\.,]\d{2,4})?",  # Ex: Lei nº 8.213/91, Lei 13.467/2017
                r"\bDecreto\s+n[º°]?\s*\d+(?:\.\d{3})*(?:[\.,]\d{2,4})?",
                # Súmulas e OJs (Orientações Jurisprudenciais)
                r"\bSúmula\s+(?:n[º°]?\s*\d+|TST\s+n[º°]?\s*\d+)",
                r"\bOJ\s+\d+(?:/\s*SDI-?\d+)?",  # Ex: OJ 394 SDI-1
                # Jurisprudência em geral
                r"(?:jurisprudência|precedente)\s*(?:do\s+TST|do\s+STF|do\s+STJ|do\s+TRT)?",
            ],
            # Tribunais e Varas
            "COURT": [
                r"\bTST\b|\bTRT\s*\d{1,2}[ªº]?\s*Região\b|\bSTF\b|\bSTJ\b",
                r"(?:Tribunal\s+Superior\s+do\s+Trabalho|Superior\s+Tribunal\s+de\s+Justiça|Supremo\s+Tribunal\s+Federal)",
                r"\d{1,2}[ªº]?\s*Vara\s+(?:do\s+Trabalho|Cível|Federal)",  # Mais genérico para varas
                r"\bMinistério\s+Público\s+do\s+Trabalho\b|\bMPT\b",
                r"\bJustiça\s+do\s+Trabalho\b",
            ],
            # Direitos trabalhistas (aqui podemos usar o vocabulário anterior para uma integração)
            "WORKER_RIGHT": [
                # Para evitar duplicação, você pode gerar esses padrões a partir de `self.rights_vocabulary`
                # Exemplo: `[keyword for right_info in self.rights_vocabulary.values() for keyword in right_info['keywords']]`
                # Mas para manter a estrutura original, vamos expandir manualmente as mais comuns:
                r"horas?\s+extras?",
                "hora\s+extra",
                "sobrejornada",
                "trabalho\s+extraordinário",
                r"adicional\s+noturno",
                "trabalho\s+noturno",
                r"insalubridade",
                "adicional\s+de\s+insalubridade",
                r"periculosidade",
                "adicional\s+de\s+periculosidade",
                r"vale[\-\s]transporte",
                "auxílio[\-\s]transporte",
                r"vale[\-\s]alimentação",
                "vale[\-\s]refeição",
                "auxílio[\-\s]alimentação",
                r"equiparação\s+salarial",
                "isonomia\s+salarial",
                r"décimo\s+terceiro",
                "13[º°]\s+salário",
                "gratificação\s+natalina",
                r"férias?",
                "férias\s+proporcionais?",
                "férias\s+vencidas?",
                "férias\s+em\s+dobro",
                r"aviso\s+prévio",
                "pré[\-\s]aviso",
                r"FGTS",
                "Fundo\s+de\s+Garantia",
                "multa\s+do\s+FGTS",
                r"estabilidade",
                "estabilidade\s+provisória",
                "garantia\s+no\s+emprego",
                r"indenização\s+por\s+danos?\s+morais?",
                "dano\s+moral",
                r"rescisão\s+indireta",
                "justa\s+causa\s+do\s+empregador",
                r"salário[\-\s]família",
                r"vínculo\s+empregatício",
                "reconhecimento\s+de\s+vínculo",
                r"verbas\s+rescisórias",
                "rescisão\s+contratual",
                "dispensa\s+sem\s+justa\s+causa",
                r"salário\s+mínimo",
                "piso\s+salarial",
                r"assédio\s+moral",
                "assédio\s+sexual",
                r"acidente\s+de\s+trabalho",
                "doença\s+ocupacional",
                r"horas\s+in\s+itinere",  # Um exemplo de direito mais específico
            ],
            # Partes do processo
            "PARTY": [
                r"\b(?:reclamante|reclamada|autor|réu|exequente|executado|embargante|embargado|litigante)\b",
                r"\b(?:parte|as\s+partes)\b",
            ],
            # Tipos de ação/documentos jurídicos
            "ACTION_TYPE": [
                r"(?:reclamação\s+trabalhista|ação\s+trabalhista|processo\s+trabalhista)",
                r"(?:sentença|acórdão|decisão\s+judicial)",
                r"(?:recurso\s+ordinário|recurso\s+de\s+revista|embargos\s+de\s+declaração|agravo\s+de\s+instrumento)",
                r"(?:contestação|manifestação|petição|impugnação)",
            ],
        }

        # Mapeamento de labels do spaCy para descrições
        self.label_descriptions = {
            "PER": "Pessoa",
            "ORG": "Organização",
            "LOC": "Local",
            "MISC": "Miscelânea",
            "MONEY": "Valor monetário",
            "DATE": "Data",
            "TIME": "Horário",
            "PROCESSO": "Número do processo",
            "LAW": "Lei/Artigo",
            "COURT": "Tribunal/Vara",
            "WORKER_RIGHT": "Direito trabalhista",
            "PARTY": "Parte",
            "ACTION_TYPE": "Tipo de ação",
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
                    patterns.append(
                        {"label": label, "pattern": [{"TEXT": {"REGEX": pattern}}]}
                    )

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
                    confidence=getattr(ent, "confidence", 0.8),
                    description=self.label_descriptions.get(ent.label_, ent.label_),
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
                entity_types=len(set(e.label for e in entities)),
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
                            description=self.label_descriptions.get(label, label),
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
                    if current.start < existing.end and current.end > existing.start:
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
                "total_entities": len(entities),
                "unique_types": len(type_counts),
                "type_distribution": dict(type_counts),
                "entities_by_type": {},
                "most_common_entities": {},
                "confidence_stats": {
                    "average": sum(e.confidence for e in entities) / len(entities),
                    "min": min(e.confidence for e in entities),
                    "max": max(e.confidence for e in entities),
                },
            }

            # Detalhes por tipo
            for entity_type, entity_list in entities_by_type.items():
                unique_entities = list(set(entity_list))
                entity_counts = Counter(entity_list)

                analysis["entities_by_type"][entity_type] = {
                    "count": len(entity_list),
                    "unique_count": len(unique_entities),
                    "entities": unique_entities[:10],  # Top 10
                    "most_common": entity_counts.most_common(5),
                }

            self.log_operation(
                "entities_analyzed",
                total_entities=analysis["total_entities"],
                unique_types=analysis["unique_types"],
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
                "horas_extras": [
                    r"hora[s]?\s+extra[s]?",
                    r"sobrejornada",
                    r"trabalho\s+extraordinário",
                    r"labor\s+extraordinário",  # Adicionado
                    r"jornada\s+extraordinária",  # Adicionado
                    r"excesso\s+de\s+jornada",  # Adicionado
                    r"prorrogação\s+de\s+jornada",  # Adicionado
                    r"banco\s+de\s+horas",  # Adicionado (muitas vezes ligado a horas extras)
                    r"acordo\s+de\s+compensação",  # Adicionado (também ligado a horas extras)
                ],
                "adicional_noturno": [
                    r"adicional\s+noturno",
                    r"trabalho\s+noturno",
                    r"labor\s+noturno",  # Adicionado
                    r"serviço\s+noturno",  # Adicionado
                    r"jornada\s+noturna",  # Adicionado
                    r"hora\s+noturna\s+reduzida",  # Adicionado (conceito importante)
                ],
                "insalubridade": [
                    r"insalubridade",
                    r"adicional\s+de\s+insalubridade",
                    r"trabalho\s+insalubre",  # Adicionado
                    r"condições\s+insalubres",  # Adicionado
                    r"agentes\s+insalubres",  # Adicionado
                    r"ambiente\s+insalubre",  # Adicionado
                    r"grau\s+de\s+insalubridade",  # Adicionado
                ],
                "periculosidade": [
                    r"periculosidade",
                    r"adicional\s+de\s+periculosidade",
                    r"trabalho\s+perigoso",  # Adicionado
                    r"atividade\s+perigosa",  # Adicionado
                    r"condições\s+perigosas",  # Adicionado
                    r"risco\s+de\s+vida",  # Adicionado (comum em laudos)
                ],
                "vale_transporte": [
                    r"vale[\-\s]?transporte",
                    r"auxílio[\-\s]?transporte",
                    r"benefício\s+transporte",  # Adicionado
                    r"passagem",  # Pode ser um indicador, dependendo do contexto
                    r"custo\s+de\s+deslocamento",  # Adicionado
                ],
                "vale_alimentacao": [
                    r"vale[\-\s]?alimentação",
                    r"vale[\-\s]?refeição",
                    r"auxílio[\-\s]?alimentação",
                    r"auxílio[\-\s]?refeição",  # Adicionado
                    r"ticket\s+alimentação",  # Adicionado
                    r"tíquete\s+alimentação",  # Adicionado (com acento)
                    r"benefício\s+alimentação",  # Adicionado
                    r"cesta[s]?\s+básica[s]?",  # Adicionado
                    r"PAT\b",  # Programa de Alimentação do Trabalhador, muitas vezes citado
                ],
                "equiparacao_salarial": [
                    r"equiparação\s+salarial",
                    r"isonomia\s+salarial",
                    r"igualdade\s+salarial",  # Adicionado
                    r"mesmo\s+salário",  # Adicionado
                    r"paridade\s+salarial",  # Adicionado
                    r"trabalho\s+igual\s+salário\s+igual",  # Adicionado (frase comum)
                    r"empregado\s+paradigma",  # Adicionado (termo técnico)
                ],
                "decimo_terceiro": [
                    r"décimo\s+terceiro",
                    r"13[º°]\s+salário",
                    r"gratificação\s+natalina",
                    r"gratificação\s+de\s+natal",  # Adicionado
                    r"parcela\s+do\s+13[º°]",  # Adicionado
                ],
                "ferias": [
                    r"férias(?:s)?",  # Captura "férias" e "ferias" (sem acento)
                    r"férias?\s+(?:proporcionais?|vencidas?|em\s+dobro|não\s+gozadas)?",  # Mantido, excelente.
                    r"período\s+de\s+férias",
                    r"abono\s+pecuniário",  # Adicionado (venda de férias)
                    r"período\s+aquisitivo",  # Adicionado (relacionado a férias)
                    r"período\s+concessivo",  # Adicionado (relacionado a férias)
                    r"descanso\s+anual",  # Adicionado (sinônimo)
                ],
                "aviso_previo": [
                    r"aviso\s+prévio",
                    r"pré[\-\s]?aviso",
                    r"aviso\s+de\s+dispensa",  # Adicionado
                    r"comunicação\s+prévia",  # Adicionado
                    r"aviso\s+trabalhado",  # Adicionado (modalidade)
                    r"aviso\s+indenizado",  # Adicionado (modalidade)
                ],
                "fgts": [
                    r"FGTS\b",  # Adicionado \b para evitar falso positivo em palavras como "FGTSoft"
                    r"Fundo\s+de\s+Garantia(?:s)?(?:em\s+Tempo\s+de\s+Serviço)?",  # Mais completo
                    r"multa\s+do\s+FGTS",
                    r"depósito[s]?\s+do\s+FGTS",  # Adicionado
                    r"saque\s+do\s+FGTS",  # Adicionado
                    r"guia\s+do\s+FGTS",  # Adicionado
                ],
                "estabilidade": [
                    r"estabilidade(?:s)?(?:is)?",  # Captura estabilidade e variações
                    r"estabilidade\s+(?:provisória|no\s+emprego|gestante|acidentária|cipeiro|sindical)?",  # Mais específica
                    r"garantia\s+no\s+emprego",
                    r"reintegração",  # Adicionado (consequência da estabilidade)
                    r"readmissão",  # Adicionado (consequência da estabilidade)
                    r"proteção\s+contra\s+despedida",  # Adicionado
                ],
                "indenizacao": [
                    r"indenização(?:ões)?",  # Para capturar plural
                    r"indenização\s+por\s+danos?\s+morais?",
                    r"danos?\s+morais?",
                    r"indenização\s+compensatória",
                    r"reparação\s+(?:de|por)\s+dano[s]?\s+moral",  # Adicionado
                    r"dano\s+existencial",  # Adicionado (tipo específico de dano)
                    r"perdas\s+e\s+danos",  # Adicionado (abrangente)
                    r"lucros\s+cessantes",  # Adicionado (tipo de dano material)
                    r"danos\s+emergentes",  # Adicionado (tipo de dano material)
                ],
                # Novos direitos ou conceitos importantes:
                "rescisao_indireta": [  # Adicionado como categoria própria
                    r"rescisão\s+indireta",
                    r"rescisão\s+por\s+justa\s+causa\s+do\s+empregador",
                    r"dispensa\s+indireta",
                    r"falta\s+grave\s+do\s+empregador",
                ],
                "salario_familia": [  # Adicionado como categoria própria
                    r"salário[\-\s]?família",
                    r"abono\s+família",
                    r"benefício\s+família",
                    r"auxílio\s+família",
                ],
                "vinculo_empregaticio": [  # Adicionado como categoria própria
                    r"vínculo\s+empregatício",
                    r"reconhecimento\s+de\s+vínculo",
                    r"relação\s+de\s+emprego",
                ],
                "verbas_rescisorias": [  # Adicionado como categoria própria
                    r"verbas\s+rescisórias",
                    r"rescisão\s+contratual",
                    r"acerto\s+rescisório",
                    r"pagamento\s+da\s+rescisão",
                    r"saldo\s+de\s+salário",  # Pode ser um indicador de verba rescisória
                ],
                "assediomoral": [  # Adicionado como categoria própria
                    r"assédio\s+moral",
                    r"violência\s+psicológica\s+no\s+trabalho",
                    r"bullying\s+no\s+trabalho",
                    r"constrangimento\s+no\s+ambiente\s+de\s+trabalho",
                    r"ambiente\s+hostil",
                ],
                "acidente_trabalho_doenca_ocupacional": [  # Agrupado e aprimorado
                    r"acidente\s+de\s+trabalho",
                    r"doença\s+ocupacional",
                    r"moléstia\s+profissional",
                    r"doença\s+do\s+trabalho",
                    r"doença\s+profissional",
                    r"incapacidade\s+(?:laborativa|permanente|temporária)",
                ],
                "salario_atraso_reducao": [  # Adicionado para problemas com o salário
                    r"salário[s]?\s+atrasado[s]?",
                    r"atraso\s+de\s+salário[s]?",
                    r"redução\s+salarial",
                    r"salário\s+não\s+pago",
                ],
                "descontos_indevidos": [  # Adicionado
                    r"desconto[s]?\s+indevido[s]?",
                    r"desconto[s]?\s+ilegal",
                    r"desconto[s]?\s+abusivo[s]?",
                ],
                "intervalo_intrajornada": [  # Adicionado
                    r"intervalo\s+intrajornada",
                    r"intervalo\s+para\s+refeição\s+e\s+descanso",
                    r"supressão\s+de\s+intervalo",
                ],
                "feriado_trabalhado": [  # Adicionado
                    r"feriado[s]?\s+trabalhado[s]?",
                    r"trabalho\s+em\s+feriado",
                ],
                "descanso_semanal_remunerado": [  # Adicionado
                    r"descanso\s+semanal\s+remunerado",
                    r"DSR\b",
                    r"repouso\s+semanal\s+remunerado",
                ],
                "cesta_basica_beneficios_nao_salariais": [  # Adicionado para outros benefícios
                    r"cesta\s+básica",
                    r"plano\s+de\s+saúde",
                    r"seguro\s+de\s+vida",
                    r"participação\s+nos\s+lucros\s+e\s+resultados",
                    r"PLR\b",
                ],
            }
            text_lower = text.lower()

            for right_type, patterns in worker_rights_patterns.items():
                matches = []

                for pattern in patterns:
                    for match in re.finditer(pattern, text_lower):
                        matches.append(
                            {
                                "text": text[match.start() : match.end()],
                                "start": match.start(),
                                "end": match.end(),
                                "pattern": pattern,
                            }
                        )

                if matches:
                    rights_found.append(
                        {
                            "type": right_type,
                            "description": right_type.replace("_", " ").title(),
                            "matches": matches,
                            "count": len(matches),
                        }
                    )

            self.log_operation(
                "worker_rights_extracted",
                text_length=len(text),
                rights_types_found=len(rights_found),
                total_mentions=sum(r["count"] for r in rights_found),
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
                # R$ com ou sem espaço, com separador de milhar (ponto ou vírgula) e decimal (vírgula ou ponto)
                # Prioriza o padrão brasileiro (milhar com ponto ou vazio, decimal com vírgula)
                r"R\$\s*(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)",  # Ex: R$ 1.234,56 ou R$ 1234,56 ou R$ 1.000 ou R$ 50,00
                # R$ com ponto como decimal (menos comum no BR, mas pode aparecer)
                r"R\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",  # Ex: R$ 1,234.56
                # Valores numéricos seguidos por "reais" (plural e singular)
                r"(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)\s*reais?",  # Ex: 5.000,00 reais, 100 reais
                # Valores numéricos seguidos por "mil", "milhões", "bilhões" e opcionalmente "de reais"
                r"(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)\s*(?:mil|milhões?|bilhões?)(?:\s+de\s+reais?)?",  # Ex: 5 mil reais, 10 milhões, 2,5 bilhões de reais
                # Expressões como "valor de R$", "quantia de R$", "importância de R$"
                r"(?:valor|quantia|importância|montante|importe)(?:\s+total)?\s+(?:de|em)\s+R\$\s*(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)",  # Adicionado 'montante', 'importe', 'total', e 'em'
                # Valores por extenso (mais complexo, mas muito útil)
                # Captura números escritos por extenso, seguidos de "reais"
                # Adicionei alguns exemplos básicos, mas uma cobertura completa exigiria uma lista extensa
                # ou uma abordagem mais sofisticada de NLP (e.g., usando num2words)
                r"(?:cem|duzentos|trezentos|quatrocentos|quinhentos|seiscentos|setecentos|oitocentos|novecentos)?\s*(?:e\s*)?(?:dez|onze|doze|treze|quatorze|quinze|dezesseis|dezessete|dezoito|dezenove|vinte|trinta|quarenta|cinquenta|sessenta|setenta|oitenta|noventa)?\s*(?:e\s*)?(?:um|dois|três|quatro|cinco|seis|sete|oito|nove)?\s*(?:mil|milhões|bilhões)?\s*reais",  # Simplificado para exemplo, idealmente seria mais robusto
                r"(?:hum|dois|três|quatro|cinco|seis|sete|oito|nove|dez|cem)\s*reais",
                # Valores precedidos por "o importe de", "a quantia de"
                r"(?:o\s+importe|a\s+quantia)\s+de\s+(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)",
            ]

            values_found = []

            for pattern in monetary_patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    # Extrair o valor numérico
                    value_text = match.group(1) if match.groups() else match.group()

                    # Limpar e converter valor
                    cleaned_value = re.sub(r"[^\d,.]", "", value_text)

                    try:
                        # Converter para float (assumindo formato brasileiro)
                        if "," in cleaned_value and "." in cleaned_value:
                            # Formato: 1.234.567,89
                            numeric_value = float(
                                cleaned_value.replace(".", "").replace(",", ".")
                            )
                        elif "," in cleaned_value:
                            # Formato: 1234,89
                            numeric_value = float(cleaned_value.replace(",", "."))
                        else:
                            # Formato: 1234.89 ou 1234
                            numeric_value = float(cleaned_value)

                        values_found.append(
                            {
                                "text": match.group(),
                                "value": numeric_value,
                                "start": match.start(),
                                "end": match.end(),
                                "formatted_value": f"R$ {numeric_value:,.2f}".replace(
                                    ",", "X"
                                )
                                .replace(".", ",")
                                .replace("X", "."),
                            }
                        )

                    except ValueError:
                        # Não foi possível converter, manter como texto
                        values_found.append(
                            {
                                "text": match.group(),
                                "value": None,
                                "start": match.start(),
                                "end": match.end(),
                                "raw_value": value_text,
                            }
                        )

            # Remover duplicatas baseado na posição
            unique_values = []
            seen_positions = set()

            for value in values_found:
                position = (value["start"], value["end"])
                if position not in seen_positions:
                    unique_values.append(value)
                    seen_positions.add(position)

            self.log_operation(
                "monetary_values_extracted",
                text_length=len(text),
                values_found=len(unique_values),
                total_value=sum(v["value"] for v in unique_values if v.get("value")),
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
                total_entities=sum(len(entities) for entities in all_entities),
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
                entities_dict.append(
                    {
                        "text": entity.text,
                        "label": entity.label,
                        "start": entity.start,
                        "end": entity.end,
                        "confidence": entity.confidence,
                        "description": entity.description,
                    }
                )

            return json.dumps(entities_dict, ensure_ascii=False, indent=2)

        except Exception as e:
            self.log_error(e, "entities_to_json")
            return "[]"
