"""
Módulo para extração e processamento de referências legislativas
"""

import re
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from collections import Counter

from ..utils.logging import LoggerMixin, log_execution_time


@dataclass
class LegalReference:
    """Representa uma referência legislativa"""

    text: str
    type: str  # 'lei', 'artigo', 'sumula', 'decreto', 'portaria', etc.
    number: Optional[str] = None
    article: Optional[str] = None
    paragraph: Optional[str] = None
    source: str = ""  # CLT, CF, CC, etc.
    confidence: float = 0.0
    context: str = ""  # Contexto onde foi encontrada

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "text": self.text,
            "type": self.type,
            "number": self.number,
            "article": self.article,
            "paragraph": self.paragraph,
            "source": self.source,
            "confidence": self.confidence,
            "context": self.context,
        }


class LegalReferencesExtractor(LoggerMixin):
    """
    Classe para extração de referências legislativas
    """

    def __init__(self):
        super().__init__()

        # Padrões para diferentes tipos de referências
        self.reference_patterns = {
            # Artigos de Códigos e Leis Consolidadas (CLT, CF, CC, CPC, CP, CDC, etc.)
            "artigo_generico": [
                # Ex: "Art. 59 da CLT", "Artigo 7º, XVI, da CF", "Art. 927 do Código Civil", "Art. 223-A da CLT"
                r"(?:art\.?|artigo)\s*(\d+)(?:º|°)?(?:-?([A-Z]))?(?:\s*,?\s*(?:§|parágrafo)\s*(\d+)(?:º|°)?)?(?:\s*,\s*inciso\s+([IVXLCDM]+))?(?:\s*,\s*alínea\s+([a-z]))?\s*(?:da|do)?\s*(?:(?:CLT|CF|Constituição\s+Federal|Constituição|CC|Código\s+Civil|CPC|Código\s+de\s+Processo\s+Civil|CP|Código\s+Penal|CDC|Código\s+de\s+Defesa\s+do\s+Consumidor|ADCT))",
                # Ex: "CLT, art. 59", "CF, artigo 7º"
                r"(?:CLT|CF|Constituição\s+Federal|Constituição|CC|Código\s+Civil|CPC|Código\s+de\s+Processo\s+Civil|CP|Código\s+Penal|CDC|Código\s+de\s+Defesa\s+do\s+Consumidor|ADCT)\s*,?\s*(?:art\.?|artigo)\s*(\d+)(?:º|°)?(?:-?([A-Z]))?(?:\s*,?\s*(?:§|parágrafo)\s*(\d+)(?:º|°)?)?(?:\s*,\s*inciso\s+([IVXLCDM]+))?(?:\s*,\s*alínea\s+([a-z]))?",
            ],
            # Leis Específicas (Ordinárias, Complementares, Decretos-Lei, etc.)
            "lei_decreto": [
                # Ex: "Lei nº 8.213/91", "Lei 13.467/2017", "Decreto nº 95.247/87", "Decreto-Lei 5.452/43"
                r"(?:Lei|Decreto|Decreto-Lei|Lei\s+Complementar|Medida\s+Provisória)\s+n[º°]?\s*(\d+(?:[.\s]?\d+)*)[\/\.]?(\d{2,4})",
                # Formato com ano primeiro, como em algumas referências antigas ou acadêmicas
                r"(?:Lei|Decreto)\s+(\d{2,4})[/\s](\d+(?:[.\s]?\d+)*)",  # Ex: "Lei 1991/8213" (menos comum)
            ],
            # Súmulas e Orientações Jurisprudenciais (OJs)
            "sumula_oj": [
                # Ex: "Súmula 340 do TST", "TST, Súmula nº 6", "OJ 394 da SDI-1 do TST"
                r"Súmula\s+n[º°]?\s*(\d+)(?:\s+do\s+)?(TST|STF|STJ|TRT)?",
                r"(?:TST|STF|STJ|TRT)\s*,?\s*Súmula\s+n[º°]?\s*(\d+)",
                r"OJ\s+n[º°]?\s*(\d+)(?:\s*da\s+SDI-?(\d))?(?:\s+do\s+)?(TST)?",  # Captura SDI-1, SDI-2, e TST opcional
            ],
            # Normas Regulamentadoras (NRs) - Segurança e Saúde no Trabalho
            "norma_regulamentadora": [
                # Ex: "NR 15", "NR-7"
                r"NR[\s-]?(\d+)(?:\s*,\s*Anexo\s+(\d+))?(?:\s*,\s*item\s+([\d\.]+))?"  # Captura anexo e item
            ],
            # Portarias e Instruções Normativas
            "portaria_instrucao_normativa": [
                # Ex: "Portaria MTE nº 3214/78", "IN RFB nº 1234/2023"
                r"(?:Portaria|Instrução\s+Normativa|IN)\s+(?:(?:MTE|MTb|RFB|TSE|CSJT)\s+)?n[º°]?\s*(\d+(?:[.\s]?\d+)*)[\/\.]?(\d{2,4})"
            ],
            # Precedentes Judiciais (genéricos)
            "precedente_judicial": [
                r"(?:Precedente\s+Normativo|PN)\s+n[º°]?\s*(\d+)",  # Precedente Normativo
                r"(?:Orientação\s+Jurisprudencial\s+Transitória|OJT)\s+n[º°]?\s*(\d+)",  # OJ Transitória
            ],
            # Resoluções e Provisões
            "resolucao_provisao": [
                r"(?:Resolução|Provimento)\s+n[º°]?\s*(\d+(?:[.\s]?\d+)*)[\/\.]?(\d{2,4})"
            ],
        }

        # Mapeamento de fontes
        self.source_mapping = {
            # Códigos e Legislação Principal
            "CLT": "Consolidação das Leis do Trabalho",
            "CF": "Constituição Federal",
            "CC": "Código Civil",
            "CPC": "Código de Processo Civil",  # Adicionado
            "CP": "Código Penal",  # Adicionado
            "CDC": "Código de Defesa do Consumidor",  # Adicionado
            "ADCT": "Ato das Disposições Constitucionais Transitórias",  # Adicionado
            "MP": "Medida Provisória",  # Adicionado (genérico)
            "LC": "Lei Complementar",  # Adicionado (genérico)
            # Tribunais Superiores
            "TST": "Tribunal Superior do Trabalho",
            "STF": "Supremo Tribunal Federal",
            "STJ": "Superior Tribunal de Justiça",
            "TRT": "Tribunal Regional do Trabalho",  # Adicionado (genérico para TRTs de todas as regiões)
            "CSJT": "Conselho Superior da Justiça do Trabalho",  # Adicionado
            "Poder Judiciário": "Poder Judiciário",  # Adicionado (para referências genéricas)
            # Órgãos e Entidades Governamentais/Judiciais
            "MTE": "Ministério do Trabalho e Emprego",
            "MTb": "Ministério do Trabalho",  # Mantido, apesar da mudança de nome, pode aparecer em textos antigos
            "MPT": "Ministério Público do Trabalho",  # Adicionado
            "RFB": "Receita Federal do Brasil",  # Adicionado (Pode aparecer em questões tributárias ligadas ao trabalho)
            "INSS": "Instituto Nacional do Seguro Social",  # Adicionado (crucial para previdência e acidentes)
            "CAIXA": "Caixa Econômica Federal",  # Adicionado (gestora do FGTS)
            "TSE": "Tribunal Superior Eleitoral",  # Adicionado (se houver alguma interface com direito político)
            "CADE": "Conselho Administrativo de Defesa Econômica",  # Adicionado (menos comum, mas possível em fusões/aquisições)
            # Outros Termos Específicos
            "OJ": "Orientação Jurisprudencial",  # Adicionado
            "SDI-1": "Seção de Dissídios Individuais I (TST)",  # Adicionado
            "SDI-2": "Seção de Dissídios Individuais II (TST)",  # Adicionado
            "SDC": "Seção de Dissídios Coletivos (TST)",  # Adicionado
            "PN": "Precedente Normativo",  # Adicionado
            "OJT": "Orientação Jurisprudencial Transitória",  # Adicionado
            "NR": "Norma Regulamentadora",  # Adicionado
            "PAT": "Programa de Alimentação do Trabalhador",  # Adicionado
        }

        self.logger.info("LegalReferencesExtractor inicializado")

    @log_execution_time
    def extract_references(
        self, text: str, existing_references: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Extrai referências legislativas do texto

        Args:
            text: Texto da decisão judicial
            existing_references: Referências já extraídas (do campo referencia_legislativa)

        Returns:
            Dicionário com referências extraídas e processadas
        """
        if not text:
            return {
                "references": [],
                "text_references": [],
                "combined_references": [],
                "summary": {},
            }

        try:
            # Extrair referências do texto
            text_references = self._extract_from_text(text)

            # Processar referências existentes
            processed_existing = self._process_existing_references(
                existing_references or []
            )

            # Combinar e deduplicar
            combined_references = self._combine_and_deduplicate(
                text_references, processed_existing
            )

            # Criar resumo
            summary = self._create_summary(combined_references)

            result = {
                "references": [ref.to_dict() for ref in combined_references],
                "text_references": [ref.to_dict() for ref in text_references],
                "existing_references": processed_existing,
                "combined_references": [ref.to_dict() for ref in combined_references],
                "summary": summary,
            }

            self.log_operation(
                "legal_references_extracted",
                text_refs_count=len(text_references),
                existing_refs_count=len(processed_existing),
                combined_refs_count=len(combined_references),
            )

            return result

        except Exception as e:
            self.log_error(e, "extract_references")
            return {
                "references": [],
                "text_references": [],
                "combined_references": [],
                "summary": {},
            }

    def _extract_from_text(self, text: str) -> List[LegalReference]:
        """Extrai referências do texto"""
        references = []

        for ref_type, patterns in self.reference_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)

                for match in matches:
                    # Extrair contexto (50 caracteres antes e depois)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()

                    # Criar referência baseada no tipo
                    ref = self._create_reference_from_match(match, ref_type, context)
                    if ref:
                        references.append(ref)

        return self._remove_duplicates(references)

    def _create_reference_from_match(
        self, match, ref_type: str, context: str
    ) -> Optional[LegalReference]:
        """Cria referência a partir de um match"""
        groups = match.groups()
        text = match.group(0)

        try:
            if ref_type.startswith("artigo_"):
                source = ref_type.split("_")[1].upper()
                article = groups[0] if groups else None
                paragraph = groups[1] if len(groups) > 1 else None

                return LegalReference(
                    text=text,
                    type="artigo",
                    article=article,
                    paragraph=paragraph,
                    source=source,
                    confidence=0.9,
                    context=context,
                )

            elif ref_type == "lei":
                number = groups[0] if groups else None
                year = groups[1] if len(groups) > 1 else None

                return LegalReference(
                    text=text,
                    type="lei",
                    number=f"{number}/{year}" if number and year else number,
                    source="Federal",
                    confidence=0.95,
                    context=context,
                )

            elif ref_type == "sumula":
                number = groups[0] if groups else None
                source = groups[1] if len(groups) > 1 else "TST"

                return LegalReference(
                    text=text,
                    type="sumula",
                    number=number,
                    source=source,
                    confidence=0.9,
                    context=context,
                )

            elif ref_type in ["decreto", "portaria", "instrucao_normativa"]:
                number = groups[0] if groups else None
                year = groups[1] if len(groups) > 1 else None

                return LegalReference(
                    text=text,
                    type=ref_type,
                    number=f"{number}/{year}" if number and year else number,
                    source="Federal",
                    confidence=0.8,
                    context=context,
                )

        except Exception as e:
            self.logger.debug(f"Erro ao criar referência: {e}")
            return None

        return None

    def _process_existing_references(self, existing_refs: List[Dict]) -> List[Dict]:
        """Processa referências existentes do campo referencia_legislativa"""
        processed = []

        for ref in existing_refs:
            if isinstance(ref, dict):
                # Já é um dicionário estruturado
                processed.append(ref)
            elif isinstance(ref, str):
                # É uma string, tentar extrair informações
                parsed = self._parse_reference_string(ref)
                if parsed:
                    processed.append(parsed)

        return processed

    def _parse_reference_string(self, ref_string: str) -> Optional[Dict]:
        """Tenta parsear uma string de referência"""
        # Implementação básica - pode ser expandida
        return {
            "text": ref_string,
            "type": "unknown",
            "source": "API",
            "confidence": 0.5,
        }

    def _combine_and_deduplicate(
        self, text_refs: List[LegalReference], existing_refs: List[Dict]
    ) -> List[LegalReference]:
        """Combina e remove duplicatas"""
        combined = list(text_refs)  # Começar com referências do texto

        # Adicionar referências existentes que não estão no texto
        for existing in existing_refs:
            existing_text = existing.get("text", "").lower()

            # Verificar se já existe uma referência similar
            found_similar = False
            for text_ref in text_refs:
                if self._are_similar_references(text_ref.text.lower(), existing_text):
                    found_similar = True
                    break

            if not found_similar:
                # Converter dict para LegalReference
                ref = LegalReference(
                    text=existing.get("text", ""),
                    type=existing.get("type", "unknown"),
                    number=existing.get("number"),
                    article=existing.get("article"),
                    paragraph=existing.get("paragraph"),
                    source=existing.get("source", "API"),
                    confidence=existing.get("confidence", 0.5),
                    context=existing.get("context", ""),
                )
                combined.append(ref)

        return self._remove_duplicates(combined)

    def _are_similar_references(self, text1: str, text2: str) -> bool:
        """Verifica se duas referências são similares"""
        if not text1 or not text2:
            return False

        # Normalizar textos
        text1 = re.sub(r"[^\w\d]", "", text1.lower())
        text2 = re.sub(r"[^\w\d]", "", text2.lower())

        # Verificar se são iguais ou se um contém o outro
        return text1 == text2 or text1 in text2 or text2 in text1

    def _remove_duplicates(
        self, references: List[LegalReference]
    ) -> List[LegalReference]:
        """Remove referências duplicadas"""
        seen = set()
        unique_refs = []

        for ref in references:
            # Criar chave única baseada no texto normalizado
            key = re.sub(r"[^\w\d]", "", ref.text.lower())

            if key not in seen:
                seen.add(key)
                unique_refs.append(ref)

        return unique_refs

    def _create_summary(self, references: List[LegalReference]) -> Dict[str, Any]:
        """Cria resumo das referências"""
        if not references:
            return {}

        # Contar por tipo
        types_count = Counter(ref.type for ref in references)

        # Contar por fonte
        sources_count = Counter(ref.source for ref in references)

        # Referências mais comuns
        most_common = []
        for ref in references:
            if ref.confidence > 0.8:
                most_common.append(
                    {
                        "text": ref.text,
                        "type": ref.type,
                        "source": ref.source,
                        "confidence": ref.confidence,
                    }
                )

        # Ordenar por confiança
        most_common.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "total_references": len(references),
            "types_distribution": dict(types_count),
            "sources_distribution": dict(sources_count),
            "most_reliable": most_common[:10],
            "has_clt_references": any(ref.source == "CLT" for ref in references),
            "has_cf_references": any(ref.source == "CF" for ref in references),
            "has_sumulas": any(ref.type == "sumula" for ref in references),
            "average_confidence": sum(ref.confidence for ref in references)
            / len(references),
        }

    def format_references_for_display(self, references_data: Dict[str, Any]) -> str:
        """Formata referências para exibição"""
        if not references_data or not references_data.get("references"):
            return "Nenhuma referência legislativa identificada"

        refs = references_data["references"]
        summary = references_data.get("summary", {})

        # Agrupar por tipo
        grouped = {}
        for ref in refs:
            ref_type = ref.get("type", "unknown")
            if ref_type not in grouped:
                grouped[ref_type] = []
            grouped[ref_type].append(ref)

        # Formatear saída
        result = []

        # Mostrar estatísticas
        total = summary.get("total_references", len(refs))
        result.append(f"Total: {total} referências")

        # Mostrar por tipo
        for ref_type, type_refs in grouped.items():
            if ref_type == "artigo":
                # Agrupar artigos por fonte
                by_source = {}
                for ref in type_refs:
                    source = ref.get("source", "Unknown")
                    if source not in by_source:
                        by_source[source] = []
                    by_source[source].append(ref)

                for source, source_refs in by_source.items():
                    articles = [ref.get("article", "N/A") for ref in source_refs]
                    result.append(f"{source}: Arts. {', '.join(articles)}")

            elif ref_type == "lei":
                laws = [ref.get("number", ref.get("text", "N/A")) for ref in type_refs]
                result.append(f"Leis: {', '.join(laws)}")

            elif ref_type == "sumula":
                sumulas = []
                for ref in type_refs:
                    number = ref.get("number", "N/A")
                    source = ref.get("source", "TST")
                    sumulas.append(f"{source} {number}")
                result.append(f"Súmulas: {', '.join(sumulas)}")

        return " | ".join(result)

    def get_clt_articles(self, references_data: Dict[str, Any]) -> List[str]:
        """Extrai apenas artigos da CLT"""
        if not references_data or not references_data.get("references"):
            return []

        clt_articles = []
        for ref in references_data["references"]:
            if ref.get("source") == "CLT" and ref.get("type") == "artigo":
                article = ref.get("article")
                if article:
                    clt_articles.append(article)

        return sorted(set(clt_articles), key=lambda x: int(x) if x.isdigit() else 999)

    def validate_references(self, references_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida a qualidade das referências extraídas"""
        if not references_data:
            return {"is_valid": False, "issues": ["Nenhuma referência fornecida"]}

        refs = references_data.get("references", [])

        validation = {
            "is_valid": True,
            "issues": [],
            "suggestions": [],
            "quality_score": 0.0,
        }

        if not refs:
            validation["is_valid"] = False
            validation["issues"].append("Nenhuma referência encontrada")
            return validation

        # Calcular score de qualidade
        total_confidence = sum(ref.get("confidence", 0) for ref in refs)
        validation["quality_score"] = total_confidence / len(refs)

        # Verificar se tem referências CLT (importante para direito do trabalho)
        has_clt = any(ref.get("source") == "CLT" for ref in refs)
        if not has_clt:
            validation["suggestions"].append(
                "Considere verificar se há referências à CLT"
            )

        # Verificar confiança baixa
        low_confidence = [ref for ref in refs if ref.get("confidence", 0) < 0.5]
        if low_confidence:
            validation["issues"].append(
                f"{len(low_confidence)} referências com baixa confiança"
            )

        return validation
