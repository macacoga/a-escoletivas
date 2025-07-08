"""
Módulo de análise de direitos trabalhistas em decisões judiciais
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter, defaultdict
import json

from ..utils.logging import LoggerMixin, log_execution_time


@dataclass
class WorkerRight:
    """Representa um direito trabalhista identificado"""

    type: str
    description: str
    mentions: List[str]
    context_sentences: List[str]
    decision_outcome: Optional[str] = None  # 'granted', 'denied', 'partially_granted'
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte direito trabalhista para dicionário"""
        return {
            "type": self.type,
            "description": self.description,
            "mentions": self.mentions,
            "context_sentences": self.context_sentences,
            "decision_outcome": self.decision_outcome,
            "confidence": self.confidence,
        }


class RightsAnalyzer(LoggerMixin):
    """
    Analisador especializado em direitos trabalhistas
    """

    def __init__(self):
        super().__init__()

        # Vocabulário de direitos trabalhistas
        self.rights_vocabulary = {
            "horas_extras": {
                "keywords": [
                    "horas extras",
                    "hora extra",
                    "sobrejornada",
                    "trabalho extraordinário",
                    "labor extraordinário",
                    "jornada extraordinária",
                    "além da jornada",
                    "excesso de jornada",
                    "prestação de serviços além",
                    "prorrogação de jornada",
                    "banco de horas",
                    "acordo de compensação de horas",
                ],
                "description": "Remuneração adicional devida por trabalho prestado além da jornada normal.",
                "legal_basis": [
                    "Art. 59 CLT",
                    "Art. 7º, XVI CF",
                    "Súmula 340 TST",
                    "OJ 394 SDI-1 TST",
                ],
            },
            "adicional_noturno": {
                "keywords": [
                    "adicional noturno",
                    "trabalho noturno",
                    "labor noturno",
                    "serviço noturno",
                    "jornada noturna",
                    "período noturno",
                    "hora noturna reduzida",
                ],
                "description": "Acrescente salarial para o trabalho executado no período noturno (geralmente das 22h às 5h em ambiente urbano).",
                "legal_basis": ["Art. 73 CLT", "Art. 7º, IX CF", "Súmula 60 TST"],
            },
            "insalubridade": {
                "keywords": [
                    "insalubridade",
                    "adicional de insalubridade",
                    "trabalho insalubre",
                    "condições insalubres",
                    "agentes insalubres",
                    "ambiente insalubre",
                    "grau de insalubridade",
                    "exposição a agentes nocivos",
                ],
                "description": "Adicional pago ao empregado que trabalha em condições nocivas à saúde, acima dos limites de tolerância.",
                "legal_basis": [
                    "Art. 189-192 CLT",
                    "NR-15",
                    "Súmula 80 TST",
                    "OJ 47 SDI-1 TST",
                ],
            },
            "periculosidade": {
                "keywords": [
                    "periculosidade",
                    "adicional de periculosidade",
                    "trabalho perigoso",
                    "atividade perigosa",
                    "condições perigosas",
                    "risco de vida",
                    "inflamáveis",
                    "explosivos",
                    "eletricidade",
                    "roubos ou outras espécies de violência física",
                ],
                "description": "Adicional devido ao empregado que exerce atividades ou operações perigosas, que impliquem contato permanente com risco de morte.",
                "legal_basis": ["Art. 193 CLT", "NR-16", "Súmula 364 TST"],
            },
            "vale_transporte": {
                "keywords": [
                    "vale transporte",
                    "vale-transporte",
                    "auxílio transporte",
                    "auxílio-transporte",
                    "benefício transporte",
                    "passagem",
                    "custo de deslocamento",
                ],
                "description": "Benefício para custear o deslocamento do empregado residência-trabalho e vice-versa.",
                "legal_basis": ["Lei 7.418/85", "Decreto 95.247/87"],
            },
            "vale_alimentacao": {
                "keywords": [
                    "vale alimentação",
                    "vale-alimentação",
                    "vale refeição",
                    "vale-refeição",
                    "auxílio alimentação",
                    "auxílio-alimentação",
                    "ticket alimentação",
                    "tíquete alimentação",
                    "benefício alimentação",
                    "cestas básicas",
                    "PAT",
                    "programa de alimentação do trabalhador",
                ],
                "description": "Benefício para a aquisição de alimentos, seja in natura ou refeições prontas.",
                "legal_basis": [
                    "Lei 6.321/76",
                    "PAT (Programa de Alimentação do Trabalhador)",
                    "Art. 458 CLT",
                ],
            },
            "equiparacao_salarial": {
                "keywords": [
                    "equiparação salarial",
                    "isonomia salarial",
                    "igualdade salarial",
                    "mesmo salário",
                    "paridade salarial",
                    "trabalho igual salário igual",
                    "paradigma",
                    "empregado modelo",
                    "identidade de funções",
                    "mesma localidade",
                    "mesmo empregador",
                ],
                "description": "Direito de empregados que exercem as mesmas funções, para o mesmo empregador, na mesma localidade, receberem salários idênticos.",
                "legal_basis": ["Art. 461 CLT", "Art. 7º, XXX CF", "Súmula 6 TST"],
            },
            "decimo_terceiro": {
                "keywords": [
                    "décimo terceiro",
                    "13º salário",
                    "gratificação natalina",
                    "décimo terceiro salário",
                    "gratificação de natal",
                    "primeira parcela",
                    "segunda parcela",
                    "cálculo décimo terceiro",
                ],
                "description": "Gratificação anual paga a todo trabalhador, correspondente a 1/12 da remuneração por mês de serviço.",
                "legal_basis": ["Lei 4.090/62", "Lei 4.749/65", "Art. 7º, VIII CF"],
            },
            "ferias": {
                "keywords": [
                    "férias",
                    "período de férias",
                    "férias proporcionais",
                    "férias vencidas",
                    "férias em dobro",
                    "férias não gozadas",
                    "descanso anual",
                    "período aquisitivo",
                    "período concessivo",
                    "abono pecuniário",
                ],
                "description": "Período de descanso remunerado concedido ao empregado após cada período de 12 meses de trabalho (período aquisitivo).",
                "legal_basis": [
                    "Art. 129-153 CLT",
                    "Art. 7º, XVII CF",
                    "Súmula 81 TST",
                    "Súmula 450 TST",
                ],
            },
            "aviso_previo": {
                "keywords": [
                    "aviso prévio",
                    "pré-aviso",
                    "aviso-prévio",
                    "aviso de dispensa",
                    "comunicação prévia",
                    "antecedência da dispensa",
                    "aviso prévio trabalhado",
                    "aviso prévio indenizado",
                    "redução de jornada no aviso",
                    "dispensa sem justa causa",
                ],
                "description": "Comunicação antecipada da rescisão do contrato de trabalho por uma das partes, com prazo mínimo estabelecido em lei.",
                "legal_basis": [
                    "Art. 487-491 CLT",
                    "Art. 7º, XXI CF",
                    "Lei 12.506/2011",
                ],
            },
            "fgts": {
                "keywords": [
                    "FGTS",
                    "Fundo de Garantia",
                    "fundo garantia tempo serviço",
                    "depósitos FGTS",
                    "saque FGTS",
                    "multa FGTS",
                    "liberação FGTS",
                    "código de saque",
                    "chave de conectividade",
                ],
                "description": "Fundo de proteção ao trabalhador em caso de demissão sem justa causa, constituído por depósitos mensais do empregador.",
                "legal_basis": [
                    "Lei 8.036/90",
                    "Art. 7º, III CF",
                    "Lei 13.467/2017 (reforma trabalhista)",
                ],
            },
            "estabilidade": {
                "keywords": [
                    "estabilidade",
                    "garantia no emprego",
                    "estabilidade provisória",
                    "proteção contra despedida",
                    "reintegração",
                    "readmissão",
                    "gestante",
                    "acidente de trabalho",
                    "cipeiro",
                    "dirigente sindical",
                ],
                "description": "Direito de o empregado permanecer no emprego por determinado período, impedindo a dispensa arbitrária ou sem justa causa.",
                "legal_basis": [
                    "Art. 10, II ADCT (gestante)",
                    "Art. 118 Lei 8.213/91 (acidente de trabalho)",
                    "Art. 165 CLT",
                    "Art. 7º, I CF",
                ],
            },
            "indenizacao_danos_morais": {
                "keywords": [
                    "danos morais",
                    "indenização por danos morais",
                    "dano moral",
                    "indenização moral",
                    "reparação moral",
                    "compensação moral",
                    "lesão moral",
                    "ofensa moral",
                    "constrangimento",
                    "humilhação",
                    "assédio moral",
                    "atingimento à honra",
                    "dignidade",
                ],
                "description": "Compensação financeira por lesões a direitos da personalidade do empregado, como honra, imagem, intimidade ou dignidade, decorrentes da relação de trabalho.",
                "legal_basis": [
                    "Art. 5º, V e X CF",
                    "Art. 927 CC",
                    "Art. 223-A a 223-G CLT",
                ],
            },
            "rescisao_indireta": {
                "keywords": [
                    "rescisão indireta",
                    "rescisão por justa causa do empregador",
                    "dispensa indireta",
                    "falta grave do empregador",
                    "descumprimento de obrigações",
                    "salários atrasados",
                    "assédio",
                ],
                "description": 'Modalidade de rescisão contratual onde o empregado "demite" o empregador por justa causa, devido a faltas graves cometidas por este.',
                "legal_basis": ["Art. 483 CLT"],
            },
            "salario_familia": {
                "keywords": [
                    "salário família",
                    "salário-família",
                    "abono família",
                    "benefício família",
                    "auxílio família",
                    "dependente",
                ],
                "description": "Benefício previdenciário pago aos trabalhadores de baixa renda com filhos menores de 14 anos ou inválidos.",
                "legal_basis": ["Lei 8.213/91", "Art. 7º, XII CF", "Decreto 3.048/99"],
            },
            "reclamacao_trabalhista": {
                "keywords": [
                    "reclamação trabalhista",
                    "processo trabalhista",
                    "ação trabalhista",
                    "demanda trabalhista",
                    "ajuizamento de ação",
                    "processo judicial",
                    "dissídio individual",
                ],
                "description": "Ação judicial proposta pelo empregado ou empregador na Justiça do Trabalho para dirimir conflitos decorrentes da relação de trabalho.",
                "legal_basis": ["Art. 837 e ss. CLT"],
            },
            "audiencia": {
                "keywords": [
                    "audiência",
                    "audiência de conciliação",
                    "audiência de instrução",
                    "audiência una",
                    "preposto",
                    "testemunha",
                    "depoimento",
                    "alegacões finais",
                ],
                "description": "Sessão formal em que as partes e o juiz se reúnem para tentar conciliação, produzir provas e ouvir depoimentos.",
                "legal_basis": ["Art. 843 e ss. CLT"],
            },
            "sentenca": {
                "keywords": [
                    "sentença",
                    "decisão judicial",
                    "primeira instância",
                    "mérito",
                    "improcedência",
                    "procedência",
                    "homologação de acordo",
                ],
                "description": "Decisão proferida pelo juiz de primeira instância que encerra o processo naquele grau de jurisdição.",
                "legal_basis": ["Art. 852 e ss. CLT", "Art. 203, § 1º CPC"],
            },
            "acordao": {
                "keywords": [
                    "acórdão",
                    "decisão de segunda instância",
                    "recurso ordinário",
                    "turma",
                    "colegiado",
                    "julgamento",
                    "ementa",
                    "voto",
                ],
                "description": "Decisão proferida por órgão colegiado (Turma ou Seção) de um Tribunal, como o TRT ou TST, em grau de recurso.",
                "legal_basis": ["Art. 893 e ss. CLT", "Art. 204 CPC"],
            },
            "recurso_ordinario": {
                "keywords": [
                    "recurso ordinário",
                    "RO",
                    "recorrer",
                    "apelação trabalhista",
                    "segunda instância",
                ],
                "description": "Recurso cabível contra sentenças proferidas em primeira instância na Justiça do Trabalho.",
                "legal_basis": ["Art. 895 CLT"],
            },
            "recurso_revista": {
                "keywords": [
                    "recurso de revista",
                    "RR",
                    "TST",
                    "Tribunal Superior do Trabalho",
                    "divergência jurisprudencial",
                    "violação de lei",
                    "violação de CF",
                ],
                "description": "Recurso de natureza extraordinária, cabível para o TST, visando uniformizar a jurisprudência ou garantir a correta aplicação da lei federal e da Constituição.",
                "legal_basis": ["Art. 896 CLT"],
            },
            "execucao_trabalhista": {
                "keywords": [
                    "execução trabalhista",
                    "fase de execução",
                    "cumprimento de sentença",
                    "cálculos de liquidação",
                    "penhora",
                    "leilão",
                    "expropriação de bens",
                ],
                "description": "Fase processual em que se busca o cumprimento forçado de uma decisão judicial transitada em julgado (ou de um acordo não cumprido), com a satisfação do crédito do trabalhador.",
                "legal_basis": ["Art. 876 e ss. CLT"],
            },
            "transito_em_julgado": {
                "keywords": [
                    "trânsito em julgado",
                    "decisão final",
                    "coisa julgada",
                    "irrecorribilidade",
                    "preclusão máxima",
                ],
                "description": "Momento em que uma decisão judicial se torna definitiva e não pode mais ser objeto de recurso, tornando-se imutável.",
                "legal_basis": ["Art. 502 CPC"],
            },
            "prescricao": {
                "keywords": [
                    "prescrição",
                    "prazo prescricional",
                    "perda do direito de ação",
                    "prescrição bienal",
                    "prescrição quinquenal",
                    "extinção da pretensão",
                ],
                "description": "Perda do direito de ajuizar uma ação ou de exigir um direito em razão do decurso de determinado prazo legal.",
                "legal_basis": ["Art. 7º, XXIX CF", "Art. 11 CLT"],
            },
            "decadencia": {
                "keywords": [
                    "decadência",
                    "prazo decadencial",
                    "perda do direito material",
                ],
                "description": "Perda do próprio direito material pelo não exercício no prazo legal, independentemente de provocação judicial.",
                "legal_basis": ["Art. 11, § 2º CLT", "Art. 207 e ss. CC"],
            },
            "dano_material": {
                "keywords": [
                    "dano material",
                    "prejuízo financeiro",
                    "lucros cessantes",
                    "danos emergentes",
                    "despesas médicas",
                    "perdas e danos",
                ],
                "description": "Prejuízo financeiro efetivamente sofrido ou o que se deixou de lucrar em razão de um ato ilícito ou descumprimento de contrato.",
                "legal_basis": ["Art. 402 e ss. CC"],
            },
            "assediomoral": {
                "keywords": [
                    "assédio moral",
                    "violência psicológica no trabalho",
                    "bullying no trabalho",
                    "constrangimento no trabalho",
                    "pressão psicológica",
                    "ambiente hostil",
                ],
                "description": "Exposição de trabalhadores e trabalhadoras a situações humilhantes e constrangedoras, de forma repetitiva e prolongada, durante a jornada de trabalho.",
                "legal_basis": [
                    "Art. 1º, III e IV, Art. 5º, V e X CF",
                    "Art. 483 CLT (hipótese de rescisão indireta)",
                ],
            },
        }

        # Padrões para identificar o resultado da decisão
        self.decision_patterns = {
            "granted": [
                # Verbos e suas variações no presente ou futuro
                r"(?:procedente|acolho|defiro|concedo|reconheço|confirmo|homologo)",
                r"(?:julgo(?:\s+totalmente)?\s+procedente)",  # "julgo procedente" ou "julgo totalmente procedente"
                # Frases que indicam direito ou obrigatoriedade
                r"(?:faz jus|tem direito|é devido|deve ser pago|cabe ao reclamante)",
                r"(?:condeno|deverá pagar|fica obrigado|arcará com)",
                r"(?:determino o pagamento de|determino a \w+ do reclamante)",  # Ex: "determino a reintegração do reclamante"
                r"(?:reconheço o vínculo empregatício|declaro a rescisão indireta)",
                r"(?:dou provimento ao recurso)",  # Para decisões de segunda instância que reformam a anterior
            ],
            "denied": [
                # Verbos e suas variações no presente ou futuro
                r"(?:improcedente|rejeito|indefiro|nego|não reconheço|declaro a improcedência)",
                r"(?:julgo(?:\s+totalmente)?\s+improcedente)",  # "julgo improcedente" ou "julgo totalmente improcedente"
                r"(?:absolvo|não procede)",  # "absolvo o reclamado", "a pretensão não procede"
                # Frases que indicam ausência de direito ou prova
                r"(?:não faz jus|não tem direito|não é devido|incabível)",
                r"(?:não comprovou|ausência de prova|ônus da prova não desincumbido)",
                r"(?:inviável|descabido|não há elementos)",
                r"(?:nego provimento ao recurso)",  # Para decisões de segunda instância que mantêm a anterior
                r"(?:mantenho a sentença)",  # Quando a segunda instância não altera a decisão
            ],
            "partially_granted": [
                # Verbos e suas variações no presente ou futuro
                r"(?:parcialmente procedente|em parte procedente|em parte acolho|em parte defiro)",
                r"(?:julgo\s+parcialmente\s+procedente)",
                r"(?:acolho\s+em\s+parte|defiro\s+em\s+parte)",
                r"(?:dou parcial provimento ao recurso)",  # Para decisões de segunda instância
                r"(?:rejeito alguns pedidos e acolho outros)",  # Variação para casos onde há uma mistura explícita
            ],
            "extinctive_with_merit": [  # Extinção com resolução do mérito (ex: prescrição, decadência)
                r"(?:extinção do processo com resolução do mérito)",
                r"(?:prescrição|decadência)",
                r"(?:pronuncio a prescrição)",
            ],
            "extinctive_without_merit": [  # Extinção sem resolução do mérito (ex: ausência de pressupostos processuais)
                r"(?:extinção do processo sem resolução do mérito)",
                r"(?:ausência de pressuposto processual|ilegitimidade de parte)",
                r"(?:determino a extinção do feito sem resolução do mérito)",
            ],
            "agreement": [  # Acordo homologado
                r"(?:homologo o acordo|acordo homologado|conciliação)",
                r"(?:partes transigiram|celebraram acordo)",
            ],
        }

    @log_execution_time
    def analyze_rights(self, text: str) -> List[WorkerRight]:
        """
        Analisa direitos trabalhistas mencionados no texto

        Args:
            text: Texto da decisão judicial

        Returns:
            Lista de direitos identificados
        """
        if not text:
            return []

        try:
            text_lower = text.lower()
            sentences = self._split_into_sentences(text)

            rights_found = []

            for right_type, right_config in self.rights_vocabulary.items():
                mentions = []
                context_sentences = []

                # Buscar keywords
                for keyword in right_config["keywords"]:
                    keyword_lower = keyword.lower()

                    # Encontrar todas as ocorrências
                    for match in re.finditer(re.escape(keyword_lower), text_lower):
                        mentions.append(text[match.start() : match.end()])

                        # Encontrar sentença que contém a menção
                        sentence = self._find_containing_sentence(
                            sentences, match.start(), match.end()
                        )
                        if sentence and sentence not in context_sentences:
                            context_sentences.append(sentence)

                if mentions:
                    # Analisar resultado da decisão para este direito
                    decision_outcome = self._analyze_decision_outcome(
                        context_sentences, right_type
                    )

                    # Calcular confiança baseada no número de menções e contexto
                    confidence = self._calculate_confidence(mentions, context_sentences)

                    worker_right = WorkerRight(
                        type=right_type,
                        description=right_config["description"],
                        mentions=list(set(mentions)),  # Remover duplicatas
                        context_sentences=context_sentences,
                        decision_outcome=decision_outcome,
                        confidence=confidence,
                    )

                    rights_found.append(worker_right)

            # Ordenar por confiança
            rights_found.sort(key=lambda x: x.confidence, reverse=True)

            self.log_operation(
                "rights_analyzed",
                text_length=len(text),
                rights_found=len(rights_found),
                granted_rights=len(
                    [r for r in rights_found if r.decision_outcome == "granted"]
                ),
                denied_rights=len(
                    [r for r in rights_found if r.decision_outcome == "denied"]
                ),
            )

            return rights_found

        except Exception as e:
            self.log_error(e, "analyze_rights", text_length=len(text))
            return []

    def _split_into_sentences(self, text: str) -> List[str]:
        """Divide texto em sentenças"""
        try:
            # Padrão para dividir sentenças
            sentence_pattern = r"[.!?]+\s+"
            sentences = re.split(sentence_pattern, text)

            # Limpar sentenças vazias
            sentences = [s.strip() for s in sentences if s.strip()]

            return sentences

        except Exception as e:
            self.log_error(e, "_split_into_sentences")
            return [text]

    def _find_containing_sentence(
        self, sentences: List[str], start: int, end: int
    ) -> Optional[str]:
        """Encontra a sentença que contém a posição especificada"""
        try:
            current_pos = 0

            for sentence in sentences:
                sentence_end = current_pos + len(sentence)

                if current_pos <= start < sentence_end:
                    return sentence

                current_pos = sentence_end + 1  # +1 para o espaço/pontuação

            return None

        except Exception as e:
            self.log_error(e, "_find_containing_sentence")
            return None

    def _analyze_decision_outcome(
        self, context_sentences: List[str], right_type: str
    ) -> Optional[str]:
        """Analisa o resultado da decisão para um direito específico"""
        try:
            if not context_sentences:
                return None

            context_text = " ".join(context_sentences).lower()

            # Verificar padrões de decisão
            for outcome, patterns in self.decision_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, context_text):
                        return outcome

            # Se não encontrou padrão claro, tentar heurísticas
            if any(
                word in context_text
                for word in ["condeno", "pagar", "devido", "procedente"]
            ):
                return "granted"
            elif any(
                word in context_text
                for word in ["improcedente", "não devido", "rejeito"]
            ):
                return "denied"
            elif any(
                word in context_text
                for word in ["parcialmente procedente", "em parte procedente"]
            ):
                return "partially_granted"
            elif any(
                word in context_text
                for word in ["extinção do processo", "prescrição", "decadência"]
            ):
                return "extinctive_with_merit"
            elif any(
                word in context_text
                for word in ["ausência de pressuposto processual", "ilegitimidade de parte"]
            ):
                return "extinctive_without_merit"
            elif any(
                word in context_text
                for word in ["acordo", "conciliação", "homologação"]
            ):
                return "agreement"

            return None

        except Exception as e:
            self.log_error(e, "_analyze_decision_outcome")
            return None

    def _calculate_confidence(
        self, mentions: List[str], context_sentences: List[str]
    ) -> float:
        """Calcula confiança na identificação do direito"""
        try:
            confidence = 0.0

            # Base: número de menções
            confidence += min(len(mentions) * 0.2, 0.6)

            # Contexto: qualidade das sentenças
            if context_sentences:
                avg_sentence_length = sum(
                    len(s.split()) for s in context_sentences
                ) / len(context_sentences)
                if avg_sentence_length > 10:  # Sentenças bem formadas
                    confidence += 0.2

            # Diversidade de menções
            unique_mentions = set(m.lower() for m in mentions)
            if len(unique_mentions) > 1:
                confidence += 0.1

            # Presença de termos jurídicos
            legal_terms = ["art", "artigo", "clt", "lei", "decreto", "súmula"]
            context_text = " ".join(context_sentences).lower()
            if any(term in context_text for term in legal_terms):
                confidence += 0.1

            return min(confidence, 1.0)

        except Exception as e:
            self.log_error(e, "_calculate_confidence")
            return 0.5

    def summarize_rights_analysis(self, rights: List[WorkerRight]) -> Dict[str, Any]:
        """
        Cria resumo da análise de direitos

        Args:
            rights: Lista de direitos analisados

        Returns:
            Resumo da análise
        """
        try:
            if not rights:
                return {}

            # Contadores
            outcome_counts = Counter(
                r.decision_outcome for r in rights if r.decision_outcome
            )
            type_counts = Counter(r.type for r in rights)

            # Estatísticas
            total_rights = len(rights)
            avg_confidence = sum(r.confidence for r in rights) / total_rights

            # Direitos por resultado
            rights_by_outcome = defaultdict(list)
            for right in rights:
                if right.decision_outcome:
                    rights_by_outcome[right.decision_outcome].append(right.description)

            # Top direitos por confiança
            top_rights = sorted(rights, key=lambda x: x.confidence, reverse=True)[:5]

            summary = {
                "total_rights_identified": total_rights,
                "average_confidence": round(avg_confidence, 2),
                "outcome_distribution": dict(outcome_counts),
                "rights_distribution": dict(type_counts),
                "rights_by_outcome": dict(rights_by_outcome),
                "top_confident_rights": [
                    {
                        "description": r.description,
                        "confidence": round(r.confidence, 2),
                        "outcome": r.decision_outcome,
                        "mentions_count": len(r.mentions),
                    }
                    for r in top_rights
                ],
                "legal_areas_covered": list(set(r.type.split("_")[0] for r in rights)),
            }

            self.log_operation(
                "rights_summary_created",
                total_rights=total_rights,
                granted=outcome_counts.get("granted", 0),
                denied=outcome_counts.get("denied", 0),
                partially_granted=outcome_counts.get("partially_granted", 0),
                extinctive_with_merit=outcome_counts.get("extinctive_with_merit", 0),
                extinctive_without_merit=outcome_counts.get("extinctive_without_merit", 0),
                agreement=outcome_counts.get("agreement", 0),
            )

            return summary

        except Exception as e:
            self.log_error(e, "summarize_rights_analysis")
            return {}

    def extract_legal_basis(
        self, text: str, rights: List[WorkerRight]
    ) -> Dict[str, List[str]]:
        """
        Extrai base legal mencionada para cada direito

        Args:
            text: Texto da decisão
            rights: Lista de direitos identificados

        Returns:
            Dicionário com base legal por direito
        """
        try:
            legal_basis_patterns = [
                r"art\.?\s*\d+[º°]?(?:\s*,\s*§\s*\d+[º°]?)?(?:\s*da\s+CLT|do\s+CC|da\s+CF)?",
                r"artigo\s+\d+[º°]?(?:\s*,\s*parágrafo\s*\d+[º°]?)?",
                r"Lei\s+n[º°]?\s*\d+[\.,/]\d+",
                r"Decreto\s+n[º°]?\s*\d+[\.,/]\d+",
                r"Súmula\s+n[º°]?\s*\d+",
                r"Orientação\s+Jurisprudencial\s+n[º°]?\s*\d+",
                r"Precedente\s+Normativo\s+n[º°]?\s*\d+",
            ]

            legal_references = {}
            text_lower = text.lower()

            for right in rights:
                right_legal_basis = []

                # Buscar base legal próxima às menções do direito
                for context_sentence in right.context_sentences:
                    sentence_lower = context_sentence.lower()

                    for pattern in legal_basis_patterns:
                        matches = re.findall(pattern, sentence_lower)
                        right_legal_basis.extend(matches)

                # Remover duplicatas e limpar
                right_legal_basis = list(set(right_legal_basis))

                if right_legal_basis:
                    legal_references[right.type] = right_legal_basis

            self.log_operation(
                "legal_basis_extracted",
                total_rights=len(rights),
                rights_with_legal_basis=len(legal_references),
            )

            return legal_references

        except Exception as e:
            self.log_error(e, "extract_legal_basis")
            return {}

    def rights_to_json(self, rights: List[WorkerRight]) -> str:
        """
        Converte lista de direitos para JSON

        Args:
            rights: Lista de direitos

        Returns:
            String JSON
        """
        try:
            rights_dict = []

            for right in rights:
                rights_dict.append(
                    {
                        "type": right.type,
                        "description": right.description,
                        "mentions": right.mentions,
                        "context_sentences": right.context_sentences,
                        "decision_outcome": right.decision_outcome,
                        "confidence": round(right.confidence, 2),
                    }
                )

            return json.dumps(rights_dict, ensure_ascii=False, indent=2)

        except Exception as e:
            self.log_error(e, "rights_to_json")
            return "[]"

    def create_rights_report(self, rights: List[WorkerRight]) -> str:
        """
        Cria relatório textual dos direitos identificados

        Args:
            rights: Lista de direitos

        Returns:
            Relatório em texto
        """
        try:
            if not rights:
                return "Nenhum direito trabalhista identificado."

            report_lines = []
            report_lines.append("RELATÓRIO DE DIREITOS TRABALHISTAS IDENTIFICADOS")
            report_lines.append("=" * 50)
            report_lines.append("")

            # Agrupar por resultado
            by_outcome = defaultdict(list)
            for right in rights:
                outcome = right.decision_outcome or "indefinido"
                by_outcome[outcome].append(right)

            outcome_labels = {
                "granted": "DIREITOS DEFERIDOS",
                "denied": "DIREITOS INDEFERIDOS",
                "partially_granted": "DIREITOS PARCIALMENTE DEFERIDOS",
                "indefinido": "DIREITOS SEM DECISÃO CLARA",
                "extinctive_with_merit": "DIREITOS EXTINTOS COM MERITO",
                "extinctive_without_merit": "DIREITOS EXTINTOS SEM MERITO",
                "agreement": "ACORDOS",
            }

            for outcome, outcome_rights in by_outcome.items():
                if not outcome_rights:
                    continue

                report_lines.append(f"\n{outcome_labels.get(outcome, outcome.upper())}")
                report_lines.append("-" * 30)

                for right in sorted(
                    outcome_rights, key=lambda x: x.confidence, reverse=True
                ):
                    report_lines.append(f"\n• {right.description}")
                    report_lines.append(f"  Confiança: {right.confidence:.1%}")
                    report_lines.append(f"  Menções: {len(right.mentions)}")

                    if right.mentions:
                        mentions_text = ", ".join(right.mentions[:3])  # Top 3
                        if len(right.mentions) > 3:
                            mentions_text += f" (+{len(right.mentions) - 3} outras)"
                        report_lines.append(f"  Termos: {mentions_text}")

            # Estatísticas finais
            report_lines.append(f"\n\nESTATÍSTICAS")
            report_lines.append("-" * 20)
            report_lines.append(f"Total de direitos identificados: {len(rights)}")
            report_lines.append(
                f"Confiança média: {sum(r.confidence for r in rights) / len(rights):.1%}"
            )

            granted_count = len([r for r in rights if r.decision_outcome == "granted"])
            denied_count = len([r for r in rights if r.decision_outcome == "denied"])

            if granted_count > 0:
                report_lines.append(f"Direitos deferidos: {granted_count}")
            if denied_count > 0:
                report_lines.append(f"Direitos indeferidos: {denied_count}")

            return "\n".join(report_lines)

        except Exception as e:
            self.log_error(e, "create_rights_report")
            return "Erro ao gerar relatório de direitos."
