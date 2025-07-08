"""
Módulo de pré-processamento de texto para decisões judiciais
"""

import re
import html
import unicodedata
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import bleach
import html2text
from unidecode import unidecode

from ..utils.logging import LoggerMixin, log_execution_time


class TextPreprocessor(LoggerMixin):
    """
    Classe para pré-processamento de texto de decisões judiciais
    """

    def __init__(self):
        super().__init__()

        # Padrões de regex para limpeza
        self.patterns = {
            # Normaliza múltiplos espaços, tabs, quebras de linha e retornos de carro para um único espaço.
            # Isso é fundamental para a uniformidade do texto.
            "normalize_whitespace": re.compile(r"\s+", re.MULTILINE),
            # Remove quebras de linha que não estão seguidas por um novo parágrafo (ex: fim de linha em meio a frase)
            # Apenas se houver um espaço ou uma letra minúscula após a quebra de linha (sugere continuação da frase)
            "remove_mid_sentence_newlines": re.compile(
                r"(?<!\n)\n(?![\n\sA-ZÁÉÍÓÚÀÈÌÒÙÃÕÇ])"
            ),
            # Números de processos:
            # Aprimorado para capturar o formato CNJ e variações mais antigas/comuns,
            # incluindo possíveis espaços em vez de pontos ou hífens.
            "process_numbers": re.compile(
                r"\b\d{7}[-.\s]?\d{2}[-.\s]?\d{4}[-.\s]?\d{1}[-.\s]?\d{2}[-.\s]?\d{4}\b"
            ),
            # Datas:
            # Aprimorado para capturar diversos formatos de datas, incluindo meses por extenso e anos com 2 ou 4 dígitos.
            # Ex: 01/01/2023, 1-JAN-23, 15.12.1999, 5 de janeiro de 2023
            "dates": re.compile(
                r"\b(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}\s+de\s+(?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+\d{4})\b",
                re.IGNORECASE,
            ),
            # # Valores monetários:
            # # Mais robusto para R$ e valores em reais, lidando com diferentes separadores (ponto/vírgula)
            # # e incluindo palavras como "mil", "milhões", etc.
            "monetary_values": re.compile(
                r"R\$\s*\d{1,3}(?:\.?\d{3})*(?:,\d{2})?|\d{1,3}(?:\.?\d{3})*(?:,\d{2})?\s*reais?|\d{1,3}(?:\.?\d{3})*(?:,\d{2})?\s*(?:mil|milhões?|bilhões?)(?:\s+de\s+reais?)?",
                re.IGNORECASE,
            ),
            # Cabeçalhos, rodapés e informações de formatação/documento:
            # Ampliado para incluir mais termos comuns em cabeçalhos/rodapés e informações de página.
            # Usa re.IGNORECASE para ser insensível a maiúsculas/minúsculas.
            "document_metadata": re.compile(
                r"(?:PODER\s+JUDICIÁRIO|JUSTIÇA\s+DO\s+TRABALHO|TRIBUNAL|VARA|JUIZ|JUIZA|GABINETE|DESEMBARGADOR|RELATOR|PRESIDENTE|MINISTRO|PÁGINA\s+\d+\s+de\s+\d+|FLS?\.\s*\d+|DOC\.\s*\d+|ID\s*\d+|AUTOS\s+N[º°]?|PROCESSO\s+N[º°]?|ACÓRDÃO|SENTENÇA|DESPACHO|DECISÃO\s+MONOCRÁTICA)\b",
                re.IGNORECASE,
            ),
            # Caracteres especiais e símbolos não textuais:
            # Mais específico para remover caracteres que não são letras, números, ou pontuação básica.
            # Exclui acentos (UNICODE) e pontuações comuns, mas remove outros símbolos (@, #, $, %, ^, &, *, {, }, |, <, >).
            "non_alphanumeric_symbols": re.compile(
                r'[^\w\s.,;:!?()\[\]{}\-"\'áéíóúàèìòùãõçÁÉÍÓÚÀÈÌÒÙÃÕÇ]', re.UNICODE
            ),
            # Linhas irrelevantes: linhas que contêm apenas números, traços, asteriscos, etc.
            # Aprimorado para ser mais abrangente e capturar linhas de separação ou numeração de página isoladas.
            "useless_lines": re.compile(r"^\s*[\d\s\-_=*#@\.]+\s*$", re.MULTILINE),
            # Texto em maiúsculas excessivo (potenciais cabeçalhos, títulos ou blocos de formatação):
            # Aprimorado para capturar sequências maiores de letras maiúsculas que não formam palavras normais,
            # sugerindo que são partes estruturais ou formatadas a serem tratadas separadamente ou removidas.
            "excessive_caps_blocks": re.compile(
                r"\b[A-Z\s]{10,}\b|\b[A-Z]{3,}\b(?:\s+[A-Z]{3,})+\b"
            ),
            # Referências a páginas ou numerações de parágrafos/itens que podem ser irrelevantes após extração de conteúdo
            "page_and_item_numbers": re.compile(
                r"\b(?:fls?\.?\s*\d+|\s*\d+\.\d+\s*|\s*\d+\.\s*)\b"
            ),  # Ex: fls. 123, 1.2.3, 1.
        }

        # Termos comuns a serem preservados
        self.preserve_terms = {
            "legal_entities_and_codes": [
                "CLT",
                "CF",
                "CC",
                "CPC",
                "CP",
                "CDC",
                "ADCT",
                "MP",
                "LC",  # Legal Codes & Legislation Types
                "TST",
                "TRT",
                "STF",
                "STJ",
                "CSJT",  # Courts & Councils
                "Poder Judiciário",
                "Ministério Público do Trabalho",
                "MPT",  # Judicial/Government Bodies
                "RFB",
                "INSS",
                "CAIXA",
                "TSE",  # Related Public Entities
                "OJ",
                "SDI",
                "SDC",
                "PN",
                "OJT",
                "NR",
                "PAT",  # Specific Legal/Normative References
                "PIS",
                "PASEP",
                "CNPJ",
                "CPF",
                "FGTS",  # Financial/Identification Codes
                "BACEN",
                "CVM",
                "Súmula",
                "Art.",
                "Artigo",
                "Lei",
                "Decreto",  # General Legal Terminology
                "Processo",
                "Autos",
                "Sentença",
                "Acórdão",
                "Recurso",
                "Embargos",
                "Agravo",  # Processual Terms
            ],
            "worker_rights_and_related_terms": [
                "salário",
                "salários",
                "salário mínimo",
                "piso salarial",
                "reajuste salarial",
                "horas extras",
                "sobrejornada",
                "trabalho extraordinário",
                "banco de horas",
                "férias",
                "décimo terceiro",
                "13º salário",
                "gratificação natalina",
                "adicional noturno",
                "insalubridade",
                "periculosidade",
                "vale transporte",
                "auxílio transporte",
                "vale alimentação",
                "vale refeição",
                "cesta básica",
                "equiparação salarial",
                "isonomia salarial",
                "estabilidade",
                "estabilidade provisória",
                "reintegração",
                "readmissão",
                "indenização",
                "danos morais",
                "danos materiais",
                "lucros cessantes",
                "dano existencial",
                "rescisão",
                "rescisão indireta",
                "justa causa",
                "sem justa causa",
                "verbas rescisórias",
                "aviso prévio",
                "pré-aviso",
                "vínculo empregatício",
                "relação de emprego",
                "registro em CTPS",
                "anotação em carteira",
                "seguro desemprego",
                "salário família",
                "assédio moral",
                "assédio sexual",
                "violência psicológica",
                "acidente de trabalho",
                "doença ocupacional",
                "moléstia profissional",
                "incapacidade laborativa",
                "multas",
                "multa do Art. 467",
                "multa do Art. 477",
                "intervalo intrajornada",
                "descanso semanal remunerado",
                "DSR",
                "contribuição previdenciária",
                "imposto de renda",
                "terceirização",
                "pejotização",  # Modern labor terms
                "cláusula",
                "convenção coletiva",
                "acordo coletivo",
                "dissídio coletivo",  # Collective labor law
                "execução",
                "liquidação",
                "cálculos",
                "homologação",
                "audiência",
                "perícia",  # Processual aspects related to rights
                "custas",
                "honorários advocatícios",
                "juros",
                "correção monetária",  # Financial/procedural costs
            ],
            # Add other categories as needed, e.g., "common_court_phrases"
        }

        # Configurar html2text
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True
        self.html_converter.ignore_emphasis = True
        self.html_converter.body_width = 0  # Sem quebra de linha

    @log_execution_time
    def preprocess_text(
        self,
        text: str,
        remove_html: bool = True,
        clean_encoding: bool = True,
        normalize_spaces: bool = True,
        remove_headers_footers: bool = True,
        preserve_structure: bool = False,
    ) -> str:
        """
        Pré-processa texto de decisão judicial

        Args:
            text: Texto a ser processado
            remove_html: Remove tags HTML
            clean_encoding: Limpa problemas de encoding
            normalize_spaces: Normaliza espaços
            remove_headers_footers: Remove cabeçalhos/rodapés
            preserve_structure: Preserva estrutura básica do texto

        Returns:
            Texto pré-processado
        """
        if not text or not isinstance(text, str):
            return ""

        original_length = len(text)
        processed_text = text

        try:
            # 1. Decodificar HTML entities
            processed_text = html.unescape(processed_text)

            # 2. Remover HTML tags
            if remove_html:
                processed_text = self._remove_html_tags(processed_text)

            # 3. Limpar encoding
            if clean_encoding:
                processed_text = self._clean_encoding(processed_text)

            # 4. Remover cabeçalhos e rodapés
            if remove_headers_footers:
                processed_text = self._remove_headers_footers(processed_text)

            # 5. Normalizar espaços
            if normalize_spaces:
                processed_text = self._normalize_spaces(processed_text)

            # 6. Limpeza final
            processed_text = self._final_cleanup(processed_text, preserve_structure)

            # Log métricas
            self.log_metrics(
                {
                    "original_length": original_length,
                    "processed_length": len(processed_text),
                    "reduction_ratio": (
                        (original_length - len(processed_text)) / original_length
                        if original_length > 0
                        else 0
                    ),
                },
                "text_preprocessing",
            )

            return processed_text.strip()

        except Exception as e:
            self.log_error(e, "preprocess_text", text_length=len(text))
            return text  # Retorna texto original em caso de erro

    def _remove_html_tags(self, text: str) -> str:
        """Remove tags HTML e converte para texto plano"""
        try:
            # Detectar se é HTML complexo
            if self._is_complex_html(text):
                self.logger.info("HTML complexo detectado, aplicando limpeza avançada")
                return self._clean_complex_html(text)

            # Usar BeautifulSoup para HTML simples
            soup = BeautifulSoup(text, "html.parser")

            # Remover scripts e styles
            for script in soup(["script", "style"]):
                script.decompose()

            # Remover elementos problemáticos
            for element in soup(["img", "svg", "canvas", "video", "audio"]):
                element.decompose()

            # Extrair texto
            text_content = soup.get_text()

            # Usar html2text como backup
            if not text_content or len(text_content) < len(text) * 0.1:
                text_content = self.html_converter.handle(text)

            return text_content

        except Exception as e:
            self.log_error(e, "_remove_html_tags")
            # Fallback: usar bleach para remover tags
            return bleach.clean(text, tags=[], strip=True)

    def _is_complex_html(self, text: str) -> bool:
        """Detecta se o texto contém HTML complexo ou problemático"""
        try:
            # Verificar indicadores de HTML complexo
            complex_indicators = [
                "data:image",  # Imagens base64
                "base64,",  # Dados base64
                "<style>",  # CSS inline
                "cellspacing",  # Tabelas complexas
                "cellpadding",
                "@media",  # CSS media queries
                "font-family",  # Estilos CSS
                "background-color",
                "text-align",
            ]

            text_lower = text.lower()
            complex_count = sum(
                1 for indicator in complex_indicators if indicator in text_lower
            )

            # Se tem muitos indicadores, é complexo
            return complex_count >= 3

        except Exception:
            return False

    def _clean_complex_html(self, text: str) -> str:
        """Limpeza avançada para HTML complexo"""
        try:
            # Método simplificado que funciona

            # 1. Remover imagens base64 (são muito grandes e inúteis)
            text = re.sub(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", "", text)

            # 2. Remover outros dados base64
            text = re.sub(r"data:[^;]+;base64,[A-Za-z0-9+/=]+", "", text)

            # 3. Remover blocos de CSS e scripts
            text = re.sub(
                r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE
            )
            text = re.sub(
                r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE
            )

            # 4. Remover todas as tags HTML de uma vez (método que funcionou)
            text = re.sub(r"<[^>]+>", " ", text)

            # 5. Normalizar espaços
            text = re.sub(r"\s+", " ", text)

            # 6. Verificar se sobrou texto útil
            clean_text = text.strip()

            if len(clean_text) < 50:
                self.logger.warning("Texto muito pequeno após limpeza")
                return ""

            return clean_text

        except Exception as e:
            self.log_error(e, "_clean_complex_html")
            # Fallback: limpeza básica que sabemos que funciona
            fallback_text = re.sub(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", "", text)
            fallback_text = re.sub(r"<[^>]+>", " ", fallback_text)
            return re.sub(r"\s+", " ", fallback_text).strip()

    def _clean_encoding(self, text: str) -> str:
        """Limpa problemas de encoding"""
        try:
            # Normalizar unicode
            text = unicodedata.normalize("NFKD", text)

            # Remover caracteres de controle
            text = "".join(char for char in text if unicodedata.category(char) != "Cc")

            # Corrigir problemas comuns de encoding
            encoding_fixes = {
                "â€™": "'",
                "â€œ": '"',
                "â€": '"',
                "â€˜": "'",
                "â€¦": "...",
                "Ã§": "ç",
                "Ã¡": "á",
                "Ã©": "é",
                "Ã­": "í",
                "Ã³": "ó",
                "Ãº": "ú",
                "Ã ": "à",
                "Ã¢": "â",
                "Ãª": "ê",
                "Ã´": "ô",
                "Ã£": "ã",
                "Ãµ": "õ",
            }

            for wrong, correct in encoding_fixes.items():
                text = text.replace(wrong, correct)

            return text

        except Exception as e:
            self.log_error(e, "_clean_encoding")
            return text

    def _remove_headers_footers(self, text: str) -> str:
        """Remove cabeçalhos e rodapés comuns (versão menos agressiva)"""
        try:
            # Se o texto não tem quebras de linha (foi processado pelo HTML), não remover nada
            if "\n" not in text:
                return text

            lines = text.split("\n")
            cleaned_lines = []

            for line in lines:
                line = line.strip()

                # Pular linhas vazias
                if not line:
                    continue

                # Pular linhas com apenas números/caracteres especiais (mais específico)
                if len(line) <= 5 and self.patterns["useless_lines"].match(line):
                    continue

                # Pular apenas cabeçalhos muito específicos (linhas isoladas)
                if len(line) < 50 and self.patterns["headers_footers"].search(line):
                    # Verificar se é uma linha isolada de cabeçalho
                    if any(
                        term in line.upper() for term in ["PÁGINA", "FLS.", "FOLHA"]
                    ):
                        continue

                # Pular linhas muito curtas apenas se forem suspeitas
                if len(line) < 5:
                    continue

                # Pular linhas com APENAS texto em maiúsculas e muito curtas
                if (
                    len(line) < 30
                    and line.isupper()
                    and not any(
                        term in line for term in ["PROCESSO", "RECURSO", "DECISÃO"]
                    )
                ):
                    continue

                cleaned_lines.append(line)

            # Se removeu muito texto, retornar original
            result = "\n".join(cleaned_lines)
            if len(result) < len(text) * 0.5:  # Se removeu mais de 50%, algo deu errado
                self.logger.warning(
                    "Remoção de headers/footers muito agressiva, retornando texto original"
                )
                return text

            return result

        except Exception as e:
            self.log_error(e, "_remove_headers_footers")
            return text

    def _normalize_spaces(self, text: str) -> str:
        """Normaliza espaços em branco"""
        try:
            # Substituir múltiplos espaços por um único espaço
            text = self.patterns["multiple_spaces"].sub(" ", text)

            # Normalizar quebras de linha
            text = re.sub(r"\n\s*\n", "\n\n", text)  # Máximo 2 quebras consecutivas
            text = re.sub(r"\n{3,}", "\n\n", text)  # Máximo 2 quebras consecutivas

            return text

        except Exception as e:
            self.log_error(e, "_normalize_spaces")
            return text

    def _final_cleanup(self, text: str, preserve_structure: bool) -> str:
        """Limpeza final do texto"""
        try:
            # Remover caracteres especiais desnecessários
            text = self.patterns["special_chars"].sub("", text)

            # Se não preservar estrutura, remover quebras de linha
            if not preserve_structure:
                text = text.replace("\n", " ")
                text = self.patterns["multiple_spaces"].sub(" ", text)

            return text

        except Exception as e:
            self.log_error(e, "_final_cleanup")
            return text

    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extrai metadados do texto

        Args:
            text: Texto a ser analisado

        Returns:
            Dicionário com metadados extraídos
        """
        try:
            metadata = {
                "length": len(text),
                "words": len(text.split()) if text else 0,
                "sentences": len(re.split(r"[.!?]+", text)) if text else 0,
                "paragraphs": len(text.split("\n\n")) if text else 0,
                "process_numbers": self.patterns["process_numbers"].findall(text),
                "dates": self.patterns["dates"].findall(text),
                "monetary_values": self.patterns["monetary_values"].findall(text),
                "has_html": bool(re.search(r"<[^>]+>", text)),
                "language": "pt",  # Assumindo português
            }

            # Estatísticas de qualidade
            if metadata["words"] > 0:
                metadata["avg_word_length"] = metadata["length"] / metadata["words"]
            else:
                metadata["avg_word_length"] = 0

            self.log_operation(
                "metadata_extracted",
                text_length=metadata["length"],
                words=metadata["words"],
                sentences=metadata["sentences"],
            )

            return metadata

        except Exception as e:
            self.log_error(e, "extract_metadata")
            return {}

    def validate_text_quality(self, text: str) -> Dict[str, Any]:
        """
        Valida a qualidade do texto processado

        Args:
            text: Texto a ser validado

        Returns:
            Dicionário com métricas de qualidade
        """
        try:
            if not text:
                return {"quality_score": 0.0, "issues": ["empty_text"]}

            issues = []
            score = 1.0

            # Verificar tamanho mínimo
            if len(text) < 100:
                issues.append("text_too_short")
                score -= 0.3

            # Verificar se ainda há HTML residual
            html_tags = re.findall(r"<[^>]+>", text)
            if html_tags:
                issues.append("html_tags_remaining")
                score -= 0.4

            # Verificar se há dados base64 residuais
            if "base64," in text:
                issues.append("base64_data_remaining")
                score -= 0.5

            # Verificar se há CSS residual
            css_indicators = ["font-family", "background-color", "text-align", "@media"]
            css_count = sum(
                1 for indicator in css_indicators if indicator in text.lower()
            )
            if css_count > 0:
                issues.append("css_remnants")
                score -= 0.3

            # Verificar se há muitos caracteres especiais
            special_char_ratio = (
                len(re.findall(r'[^\w\s\.,;:!?()[\]{}""' '""-]', text)) / len(text)
                if text
                else 0
            )
            if special_char_ratio > 0.3:
                issues.append("too_many_special_chars")
                score -= 0.2

            # Verificar se há palavras muito longas (possível lixo)
            words = text.split()
            if words:
                avg_word_length = sum(len(word) for word in words) / len(words)
                if avg_word_length > 15:
                    issues.append("words_too_long")
                    score -= 0.2

                # Verificar se há muitas "palavras" que são na verdade códigos
                code_words = [
                    word
                    for word in words
                    if len(word) > 20 and not any(c.isalpha() for c in word)
                ]
                if len(code_words) > len(words) * 0.1:  # Mais de 10% são códigos
                    issues.append("too_many_code_words")
                    score -= 0.3

            # Verificar se há estrutura de sentenças
            sentences = re.split(r"[.!?]+", text)
            valid_sentences = [s for s in sentences if len(s.strip()) > 10]
            if len(valid_sentences) < 3:
                issues.append("too_few_sentences")
                score -= 0.2

            # Verificar presença de termos jurídicos
            legal_terms_found = 0
            for term in self.preserve_terms["legal_terms"]:
                if term.lower() in text.lower():
                    legal_terms_found += 1

            # Verificar presença de termos trabalhistas
            worker_terms_found = 0
            for term in self.preserve_terms["worker_rights"]:
                if term.lower() in text.lower():
                    worker_terms_found += 1

            # Bonificar presença de termos relevantes
            if legal_terms_found > 0:
                score += 0.1
            if worker_terms_found > 0:
                score += 0.1

            # Se não tem nenhum termo relevante, é suspeito
            if legal_terms_found == 0 and worker_terms_found == 0:
                issues.append("no_legal_terms")
                score -= 0.2

            # Verificar ratio de texto útil vs lixo
            useful_chars = len(
                re.findall(
                    r'[a-zA-ZáéíóúâêîôûàèìòùãõçÁÉÍÓÚÂÊÎÔÛÀÈÌÒÙÃÕÇ\s\.,;:!?()[\]{}""'
                    '""-]',
                    text,
                )
            )
            useful_ratio = useful_chars / len(text) if text else 0
            if useful_ratio < 0.7:
                issues.append("low_useful_text_ratio")
                score -= 0.3

            quality_score = max(0.0, min(1.0, score))

            return {
                "quality_score": quality_score,
                "issues": issues,
                "legal_terms_found": legal_terms_found,
                "worker_terms_found": worker_terms_found,
                "word_count": len(words) if words else 0,
                "sentence_count": len(valid_sentences),
                "special_char_ratio": special_char_ratio,
                "useful_text_ratio": useful_ratio,
                "html_tags_count": len(html_tags),
                "has_base64": "base64," in text,
                "css_indicators": css_count,
            }

        except Exception as e:
            self.log_error(e, "validate_text_quality")
            return {"quality_score": 0.0, "issues": ["validation_error"]}

    def batch_preprocess(self, texts: List[str], **kwargs) -> List[str]:
        """
        Processa uma lista de textos em lote

        Args:
            texts: Lista de textos a serem processados
            **kwargs: Argumentos para preprocess_text

        Returns:
            Lista de textos processados
        """
        try:
            processed_texts = []

            for i, text in enumerate(texts):
                if i % 100 == 0:
                    self.logger.info(f"Processando texto {i+1}/{len(texts)}")

                processed_text = self.preprocess_text(text, **kwargs)
                processed_texts.append(processed_text)

            self.log_operation(
                "batch_preprocessing_completed",
                total_texts=len(texts),
                processed_texts=len(processed_texts),
            )

            return processed_texts

        except Exception as e:
            self.log_error(e, "batch_preprocess", total_texts=len(texts))
            raise
