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
            "resultado_principal": self.resultado_principal,
            "resultado_detalhado": self.resultado_detalhado,
            "pedidos_principais": self.pedidos_principais,
            "decisao_resumo": self.decisao_resumo,
            "fundamentacao_principal": self.fundamentacao_principal,
            "valores_envolvidos": self.valores_envolvidos,
            "confidence_score": self.confidence_score,
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
            # --- Seção de Pedidos (Geralmente no final da Petição Inicial ou Recurso) ---
            "pedidos": [
                # Padrões para cabeçalhos explícitos da seção de Pedidos
                # Captura o cabeçalho e todo o texto até a próxima seção principal ou o fim do documento.
                # Usa (?i) para case-insensitive. (?s) para DOTALL ('.' casa com newline).
                r"(?is)(?:^|\b)(?:PEDIDOS?|REQUERIMENTO|DA\s+CONCLUSÃO|DO\s+PEDIDO)[\s\r\n\:]*(.*?)(?=^FUNDAMENTAÇÃO|^DO\s+DIREITO|^RELATÓRIO|^DA\s+DECISÃO|^DISPOSITIVO|^VOTO|^EMENTA|^\s*[A-Z]{4,}|Z\s*.\s*Z|$)",
                # Padrões para frases que introduzem ou sumarizam pedidos no corpo do texto
                # Útil para identificar a parte do texto onde os pedidos são formalizados mesmo sem um cabeçalho explícito.
                r"(?is)(?:o\s+reclamante\s+requer|diante\s+do\s+exposto,\s+requer|pelo\s+exposto,\s+pede|em\s+face\s+do\s+exposto,\s+solicita)\s*(.*?)(?=(?:^|\b)(?:FUNDAMENTAÇÃO|RELATÓRIO|DECISÃO|VOTO)|$)",
                # Termos que indicam a ação de pedir/solicitar, geralmente seguido dos itens
                r"(?is)(?:pede|requer|pleiteia|solicita|postula)\s+o\s+reclamante(?:\s+a\s+condenação)?\s*[\s\S]*?(?=\n\n|\b(?:fundamentação|relatório|decisão|voto)\b|$)",
            ],
            # --- Seção de Fundamentação (Argumentos Jurídicos e Fáticos) ---
            "fundamentacao": [
                # Padrões para cabeçalhos explícitos da seção de Fundamentação
                r"(?is)(?:^|\b)(?:FUNDAMENTAÇÃO|FUNDAMENTOS|RAZÕES\s+DO\s+DIREITO|DO\s+DIREITO|MÉRITO|DO\s+MÉRITO|II\s*[-–]\s*(?:DA\s+)?FUNDAMENTAÇÃO|II\s*[-–]\s*(?:DO\s+)?MÉRITO)[\s\r\n\:]*(.*?)(?=^DISPOSITIVO|^DA\s+DECISÃO|^VOTO|^ACORDAM|^CONCLUSÃO|^EMENTA|^RELATÓRIO|^\s*[A-Z]{4,}|Z\s*.\s*Z|$)",
                # Padrões para frases que indicam a parte da argumentação no corpo do texto
                r"(?is)(?:passo\s+a\s+analisar|analisando\s+o\s+mérito|da\s+análise\s+dos\s+autos|da\s+prova\s+produzida|sustenta\s+a\s+parte)\s*(.*?)(?=(?:^|\b)(?:DECISÃO|DISPOSITIVO|VOTO|ACORDAM)|$)",
                # Termos que indicam o início da argumentação jurídica
                r"(?is)(?:fundamenta|baseia-se|considera|entende|conforme\s+o\s+disposto)\s*[\s\S]*?(?=\n\n|\b(?:decisão|dispositivo|voto)\b|$)",
            ],
            # --- Seção de Decisão/Dispositivo (Onde a sentença ou acórdão é proferido) ---
            "decisao": [
                # Padrões para cabeçalhos explícitos da seção de Decisão/Dispositivo
                r"(?is)(?:^|\b)(?:DECISÃO|DISPOSITIVO|VOTO|ACORDAM|ANTE\s+O\s+EXPOSTO|PELO\s+EXPOSTO|ISTO\s+POSTO|III\s*[-–]\s*DISPOSITIVO|CONCLUSÃO)[\s\r\n\:]*(.*?)(?=$|Z\s*.\s*Z)",
                # Padrões para frases que expressam o ato de julgar ou decidir no corpo do texto
                r"(?is)(?:decide|julga|determina|condena|homologa|concede|defere|indefere|acolhe|rejeita|extingue|pronuncia)\s*(?:o\s+juiz|o\s+tribunal|o\s+relator)?\s*(.*?)(?=(?:^|\b)(?:RELATÓRIO|FUNDAMENTAÇÃO|EMENTA)|$)",  # Adicionado verbos e objetos de julgamento
                # Termos que indicam a sentença final de forma mais direta
                r"(?is)(?:sentença\s*:\s*|acórdão\s*:\s*|decisão\s*:\s*)[\s\S]*?(?=$)",
            ],
            # --- Padrões para Valores Monetários (Se for para extrair valores, não seções) ---
            # Estes são padrões para *entidades*, não para *seções*.
            # Se o objetivo é apenas encontrar valores em qualquer lugar, eles ficariam em um 'entity_patterns' separado.
            # Se a ideia é encontrar uma 'seção' que 'fale de valores', a lógica seria diferente.
            # Assumindo que você quer *extrair* os valores em si.
            "valores": [
                r"(?i)R\$\s*(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)",  # Ex: R$ 1.234,56 ou R$ 1234,56 ou R$ 1.000
                r"(?i)(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)\s*reais?",  # Ex: 5.000,00 reais, 100 reais
                r"(?i)(?:valor|quantia|importância|montante|importe)(?:\s+total)?\s+(?:de|em)?\s*R\$\s*(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)",
                r"(?i)(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)\s*(?:mil|milhões?|bilhões?)(?:\s+de\s+reais?)?",  # Ex: 5 mil reais, 10 milhões, 2,5 bilhões de reais
            ],
        }

        # Padrões para identificar tipos de pedidos
        self.pedido_patterns = {
            "horas_extras": r"(?i)\b(?:horas?\s+extras?|sobrejornada|trabalho\s+extraordinário|labor\s+extraordinário|jornada\s+extraordinária|excesso\s+de\s+jornada|banco\s+de\s+horas|acordo\s+de\s+compensação)\b",
            "adicional_noturno": r"(?i)\b(?:adicional\s+noturno|trabalho\s+noturno|labor\s+noturno|jornada\s+noturna|hora\s+noturna\s+reduzida)\b",
            "insalubridade": r"(?i)\b(?:insalubridade|adicional\s+de\s+insalubridade|trabalho\s+insalubre|condições\s+insalubres)\b",
            "periculosidade": r"(?i)\b(?:periculosidade|adicional\s+de\s+periculosidade|trabalho\s+perigoso|atividade\s+perigosa|risco\s+de\s+vida)\b",
            "fgts": r"(?i)\b(?:FGTS|Fundo\s+de\s+Garantia(?:s)?(?:em\s+Tempo\s+de\s+Serviço)?|depósito[s]?\s+de\s+FGTS|saque\s+de\s+FGTS|multa\s+do\s+FGTS)\b",
            "danos_morais": r"(?i)\b(?:danos?\s+morais?|indenização\s+por\s+danos?\s+morais?|dano\s+moral|reparação\s+moral|compensação\s+moral|abalo\s+moral|sofrimento\s+moral)\b",
            "equiparacao_salarial": r"(?i)\b(?:equiparação\s+salarial|isonomia\s+salarial|igualdade\s+salarial|paridade\s+salarial|mesmo\s+salário\s+para\s+mesma\s+função|paradigma)\b",
            "diferenca_salarial": r"(?i)\b(?:diferença[s]?\s+salarial(?:is)?|dissídio\s+salarial|reajuste\s+salarial|salário\s+inferior|subsalário|piso\s+salarial)\b",
            "verbas_rescisorias": r"(?i)\b(?:verbas?\s+rescisória(?:s)?|acerto\s+rescisório|pagamento\s+da\s+rescisão|saldo\s+de\s+salário|aviso\s+prévio|13[º°]\s+salário\s+proporcional|férias?\s+proporcionais?\s+e\s+\d+\/\d+)\b",  # Combina alguns itens
            "aviso_previo": r"(?i)\b(?:aviso\s+prévio|pré[\-\s]?aviso|aviso\s+de\s+dispensa|aviso\s+prévio\s+indenizado|aviso\s+prévio\s+trabalhado)\b",
            "ferias": r"(?i)\b(?:férias?|período\s+de\s+férias|férias?\s+proporcionais?|férias?\s+vencidas?|férias?\s+em\s+dobro|abono\s+pecuniário|descanso\s+anual)\b",
            "decimo_terceiro": r"(?i)\b(?:décimo\s+terceiro|13[º°]\s+salário|gratificação\s+natalina|gratificação\s+de\s+natal|parcela\s+do\s+13[º°])\b",
            "registro_ctps_vinculo": r"(?i)\b(?:registro\s+em\s+CTPS|anotação\s+em\s+carteira|vínculo\s+empregatício|reconhecimento\s+de\s+vínculo|relação\s+de\s+emprego)\b",  # Novo
            "rescisao_indireta": r"(?i)\b(?:rescisão\s+indireta|justa\s+causa\s+do\s+empregador|dispensa\s+indireta|falta\s+grave\s+do\s+empregador)\b",  # Novo
            "salario_familia": r"(?i)\b(?:salário[\-\s]?família|abono\s+família|benefício\s+família|auxílio\s+família)\b",  # Novo
            "seguro_desemprego": r"(?i)\b(?:seguro\s+desemprego|guias?\s+do\s+seguro\s+desemprego|liberação\s+do\s+seguro\s+desemprego)\b",  # Novo
            "reintegracao": r"(?i)\b(?:reintegração|readmissão|retorno\s+ao\s+posto\s+de\s+trabalho|estabilidade\s+provisória)\b",  # Novo
            "danos_materiais": r"(?i)\b(?:danos?\s+materiais?|lucros\s+cessantes|danos?\s+emergentes|reparação\s+material|custos\s+com\s+tratamento)\b",  # Novo
            "assediomoral_sexual": r"(?i)\b(?:assédio\s+moral|assédio\s+sexual|violência\s+psicológica|constrangimento\s+no\s+trabalho|ambiente\s+hostil|perseguição)\b",  # Novo
            "acidente_doenca_trabalho": r"(?i)\b(?:acidente\s+de\s+trabalho|doença\s+ocupacional|doença\s+do\s+trabalho|moléstia\s+profissional|estabilidade\s+acidentária|incapacidade\s+laborativa)\b",  # Novo
            "multas_clt": r"(?i)\b(?:multa\s+do\s+art(?:igo)?\s*467|multa\s+do\s+art(?:igo)?\s*477|multas?\s+da\s+CLT|multas?\s+rescisórias?)\b",  # Novo
        }

        self.logger.info("StructuredSummarizer inicializado")

    @log_execution_time
    def create_structured_summary(
        self,
        text: str,
        parts_data: Optional[Dict] = None,
        legal_refs: Optional[Dict] = None,
    ) -> StructuredSummary:
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
            resultado_analysis_obj = self.resultado_analyzer.analisar_resultado(text)
            resultado_analysis = {
                "resultado": resultado_analysis_obj.resultado_principal,
                "confidence": resultado_analysis_obj.confianca,
                "evidencias": resultado_analysis_obj.evidencias,
                "metodo": resultado_analysis_obj.metodo_usado,
                "detalhes": resultado_analysis_obj.detalhes,
            }

            # Extrair seções
            sections = self._extract_sections(text)

            # Identificar pedidos principais
            pedidos = self._extract_main_requests(text, sections.get("pedidos", ""))

            # Extrair valores
            valores = self._extract_monetary_values(text)

            # Criar resumo da decisão
            decisao_resumo = self._create_decision_summary(
                sections.get("decisao", ""), resultado_analysis
            )

            # Extrair fundamentação principal
            fundamentacao = self._extract_main_reasoning(
                sections.get("fundamentacao", "")
            )

            # Calcular confiança
            confidence = self._calculate_summary_confidence(
                resultado_analysis, pedidos, valores, sections
            )

            summary = StructuredSummary(
                resultado_principal=resultado_analysis["resultado"],
                resultado_detalhado=resultado_analysis,
                pedidos_principais=pedidos,
                decisao_resumo=decisao_resumo,
                fundamentacao_principal=fundamentacao,
                valores_envolvidos=valores,
                confidence_score=confidence,
            )

            self.log_operation(
                "structured_summary_created",
                resultado=resultado_analysis["resultado"],
                pedidos_count=len(pedidos),
                valores_count=len(valores),
                confidence=confidence,
            )

            return summary

        except Exception as e:
            self.log_error(e, "create_structured_summary")
            return self._create_empty_summary()

    def _create_empty_summary(self) -> StructuredSummary:
        """Cria resumo vazio"""
        return StructuredSummary(
            resultado_principal="Resultado não identificado",
            resultado_detalhado={
                "resultado": "Resultado não identificado",
                "confidence": 0.0,
            },
            pedidos_principais=[],
            decisao_resumo="Decisão não identificada",
            fundamentacao_principal="Fundamentação não identificada",
            valores_envolvidos=[],
            confidence_score=0.0,
        )

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extrai seções principais do texto"""
        sections = {}

        for section_name, patterns in self.section_patterns.items():
            if section_name == "valores":
                continue  # Valores são tratados separadamente

            for pattern in patterns:
                match = re.search(
                    pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL
                )
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
                pedidos.append(pedido_type.replace("_", " ").title())

        # Se não encontrou pedidos específicos, tentar extrair de forma mais genérica
        if not pedidos:
            # Procurar por verbos de pedido
            generic_patterns = [
                # Captura o que é pedido após verbos de solicitação.
                # Ex: "pede o pagamento de horas extras." -> "o pagamento de horas extras"
                # "requer a reintegração ao cargo." -> "a reintegração ao cargo"
                r"(?i)(?:pede|requer|pleiteia|solicita|postula)\s+(.+?)(?=\.|;|,|\n|E\s+ainda|Por\s+fim|Diante\s+do\s+exposto)",
                # Captura o que é alvo de uma condenação, determinação ou reconhecimento.
                # Ex: "condenar o reclamado ao pagamento de verbas." -> "o reclamado ao pagamento de verbas"
                # "determinar a anotação na CTPS." -> "a anotação na CTPS"
                r"(?i)(?:condenar|determinar|reconhecer|declarar|conceder|deferir|acolher|restabelecer|liberar)\s+(.+?)(?=\.|;|,|\n|E\s+ainda|Por\s+fim|Diante\s+do\s+exposto)",
                # Captura o que é objeto de pagamento ou indenização.
                # Ex: "pagamento de horas extras e reflexos." -> "horas extras e reflexos"
                # "indenização por danos morais." -> "danos morais"
                r"(?i)(?:pagamento|indenização|reparação|restituição)\s+(?:de|por|a\s+título\s+de)\s+(.+?)(?=\.|;|,|\n|E\s+ainda|Por\s+fim|Diante\s+do\s+exposto)",
                # Captura frases que indicam uma solicitação direta do réu.
                # Ex: "que o réu seja condenado a..." -> "o réu seja condenado a..."
                r"(?i)que\s+(?:o|a)\s*(?:reclamado|réu|empresa)\s+seja\s+(?:condenado|obrigado|compelido)\s+a\s+(.+?)(?=\.|;|,|\n|E\s+ainda|Por\s+fim|Diante\s+do\s+exposto)",
                # Captura a listagem de pedidos em formato de item (ex: I - Horas extras; II - Adicional)
                r"(?i)(?:\d+\.?\s*[-–]?\s*|\b(?:alínea|item)\s+[a-z\d]\b)\s*(.+?)(?=\.|;|,|\n(?=\d+\.?\s*[-–]?\s*|\b(?:alínea|item)\s+[a-z\d]\b)|E\s+ainda|Por\s+fim|Diante\s+do\s+exposto|$)",
            ]

            for pattern in generic_patterns:
                matches = re.finditer(pattern, search_text, re.IGNORECASE)
                for match in matches:
                    pedido = match.group(1).strip()
                    if (
                        len(pedido) > 10 and len(pedido) < 100
                    ):  # Filtrar pedidos muito curtos ou longos
                        pedidos.append(pedido)

        return pedidos[:5]  # Limitar a 5 pedidos principais

    def _extract_monetary_values(self, text: str) -> List[Dict[str, Any]]:
        """Extrai valores monetários"""
        valores = []

        for pattern in self.section_patterns["valores"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                valor_text = match.group(0)

                # Extrair contexto
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()

                # Tentar extrair valor numérico
                numeric_value = self._extract_numeric_value(valor_text)

                valores.append(
                    {
                        "text": valor_text,
                        "numeric_value": numeric_value,
                        "context": context,
                        "position": match.start(),
                    }
                )

        # Remover duplicatas e ordenar por posição
        unique_valores = []
        seen_values = set()

        for valor in sorted(valores, key=lambda x: x["position"]):
            value_key = valor["text"].lower().replace(" ", "")
            if value_key not in seen_values:
                seen_values.add(value_key)
                unique_valores.append(valor)

        return unique_valores[:10]  # Limitar a 10 valores

    def _extract_numeric_value(self, value_text: str) -> Optional[float]:
        """Extrai valor numérico de texto monetário"""
        # Remover símbolos e texto
        numeric_text = re.sub(r"[^\d,.]", "", value_text)

        # Tentar converter para float
        try:
            # Assumir formato brasileiro (vírgula como decimal)
            if "," in numeric_text:
                # Se tem ponto e vírgula, ponto é separador de milhares
                if "." in numeric_text and "," in numeric_text:
                    numeric_text = numeric_text.replace(".", "").replace(",", ".")
                else:
                    # Se só tem vírgula, pode ser decimal
                    parts = numeric_text.split(",")
                    if len(parts) == 2 and len(parts[1]) == 2:
                        numeric_text = numeric_text.replace(",", ".")

            return float(numeric_text)
        except ValueError:
            return None

    def _create_decision_summary(
        self, decisao_text: str, resultado_analysis: Dict
    ) -> str:
        """Cria resumo da decisão"""
        if not decisao_text:
            return f"Decisão: {resultado_analysis['resultado']}"

        # Extrair frases principais da decisão
        sentences = re.split(r"[.!?]+", decisao_text)
        important_sentences = []

        # Procurar por frases com palavras-chave de decisão
        decision_keywords = [
            "julgo",
            "julga",
            "julgou",
            "decido",
            "decide",
            "decidiu",
            "determino",
            "determina",
            "determinou",
            "condeno",
            "condena",
            "condenou",
            "reconheço",
            "reconhece",
            "reconheceu",
            "defiro",
            "defere",
            "deferiu",
            "indefiro",
            "indefere",
            "indeferiu",
            "acolho",
            "acolhe",
            "acolheu",
            "rejeito",
            "rejeita",
            "rejeitou",
            "procedente",
            "procedência",
            "improcedente",
            "improcedência",
            "parcialmente procedente",
            "parcialmente",
            "extingo",
            "extingue",
            "extinguiu",
            "homologo",
            "homologa",
            "homologou",
            "concedo",
            "concede",
            "concedeu",
            "arbitro",
            "arbitra",
            "arbitrou",
            "declaro",
            "declara",
            "declarou",
            "mantenho",
            "mantém",
            "manteve",
            "reformo",
            "reforma",
            "reformou",
            "dou provimento",
            "dá provimento",
            "nego provimento",
            "nega provimento",
            "provido",
            "desprovido",
            "improvido",
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
            summary = ". ".join(important_sentences[:2])
            if len(summary) > 200:
                summary = summary[:200] + "..."
            return summary

        # Se não encontrou frases específicas, usar o resultado da análise
        return f"Decisão: {resultado_analysis['resultado']}"

    def _extract_main_reasoning(self, fundamentacao_text: str) -> str:
        """Extrai fundamentação principal"""
        if not fundamentacao_text:
            return "Fundamentação não identificada"

        # Extrair primeiras frases da fundamentação
        sentences = re.split(r"[.!?]+", fundamentacao_text)

        # Procurar por frases com fundamentação legal
        legal_keywords = [
            "conforme",
            "segundo",
            "de acordo com",
            "nos termos de",
            "em conformidade com",
            "previsto em",
            "disposto em",
            "estabelece",
            "determina",
            "dispõe",
            "preceitua",
            "artigo",
            "art.",
            "parágrafo",
            "§",
            "inciso",
            "alínea",
            "lei",
            "legislação",
            "decreto",
            "súmula",
            "orientação jurisprudencial",
            "oj",
            "jurisprudência",
            "precedente",
            "doutrina",
            "norma",
            "resolução",
            "provimento",
            "clt",
            "cf",
            "constituição",
            "código civil",
            "cpc",
            "código de processo civil",
            "código penal",
            "cdc",
            "código de defesa do consumidor",
            "adct",
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
            summary = ". ".join(important_sentences[:2])
            if len(summary) > 300:
                summary = summary[:300] + "..."
            return summary

        # Se não encontrou frases específicas, pegar início da fundamentação
        if len(fundamentacao_text) > 300:
            return fundamentacao_text[:300] + "..."

        return fundamentacao_text

    def _calculate_summary_confidence(
        self, resultado_analysis: Dict, pedidos: List, valores: List, sections: Dict
    ) -> float:
        """Calcula confiança do resumo"""
        confidence = 0.0

        # Confiança do resultado (peso 40%)
        resultado_conf = resultado_analysis.get("confidence", 0.0)
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
            valores_str = ", ".join([v["text"] for v in summary.valores_envolvidos[:3]])
            lines.append(f"💰 Valores: {valores_str}")

        # Decisão resumo
        if (
            summary.decisao_resumo
            and summary.decisao_resumo != "Decisão não identificada"
        ):
            lines.append(f"🏛️ Decisão: {summary.decisao_resumo}")

        # Confiança
        conf_percent = int(summary.confidence_score * 100)
        lines.append(f"📊 Confiança: {conf_percent}%")

        return "\n".join(lines)

    def get_summary_statistics(
        self, summaries: List[StructuredSummary]
    ) -> Dict[str, Any]:
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
            "total_summaries": len(summaries),
            "average_confidence": avg_confidence,
            "most_common_results": sorted(
                resultado_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "most_common_requests": sorted(
                pedido_counts.items(), key=lambda x: x[1], reverse=True
            )[:10],
            "summaries_with_values": len(
                [s for s in summaries if s.valores_envolvidos]
            ),
            "high_confidence_summaries": len(
                [s for s in summaries if s.confidence_score > 0.7]
            ),
        }
