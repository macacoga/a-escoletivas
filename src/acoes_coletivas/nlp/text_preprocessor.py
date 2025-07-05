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
            # Múltiplos espaços, tabs e quebras de linha
            'multiple_spaces': re.compile(r'\s+'),
            
            # Números de processos
            'process_numbers': re.compile(r'\b\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}\b'),
            
            # Datas
            'dates': re.compile(r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b'),
            
            # Valores monetários
            'monetary_values': re.compile(r'R\$\s*\d+[.,]?\d*[.,]?\d*'),
            
            # Cabeçalhos e rodapés típicos
            'headers_footers': re.compile(r'(PODER JUDICIÁRIO|JUSTIÇA DO TRABALHO|TRIBUNAL|VARA|JUIZ|PÁGINA \d+|FLS\. \d+)', re.IGNORECASE),
            
            # Caracteres especiais repetidos
            'special_chars': re.compile(r'[^\w\s\.,;:!?()[\]{}""''""\-]'),
            
            # Linhas com apenas números ou caracteres especiais
            'useless_lines': re.compile(r'^[\d\s\-_=*#\.]+$'),
            
            # Texto em maiúsculas excessivo (provavelmente cabeçalhos)
            'excessive_caps': re.compile(r'\b[A-Z]{5,}\b'),
        }
        
        # Termos comuns a serem preservados
        self.preserve_terms = {
            'legal_terms': [
                'CLT', 'TST', 'TRT', 'STF', 'STJ', 'CF', 'CC', 'CPC',
                'FGTS', 'PIS', 'PASEP', 'INSS', 'CNPJ', 'CPF'
            ],
            'worker_rights': [
                'salário', 'férias', 'décimo terceiro', '13º salário',
                'adicional noturno', 'horas extras', 'insalubridade',
                'periculosidade', 'vale transporte', 'vale alimentação',
                'equiparação salarial', 'estabilidade', 'indenização',
                'rescisão', 'justa causa', 'aviso prévio'
            ]
        }
        
        # Configurar html2text
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True
        self.html_converter.ignore_emphasis = True
        self.html_converter.body_width = 0  # Sem quebra de linha
    
    @log_execution_time
    def preprocess_text(self, text: str, 
                       remove_html: bool = True,
                       clean_encoding: bool = True,
                       normalize_spaces: bool = True,
                       remove_headers_footers: bool = True,
                       preserve_structure: bool = False) -> str:
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
            self.log_metrics({
                'original_length': original_length,
                'processed_length': len(processed_text),
                'reduction_ratio': (original_length - len(processed_text)) / original_length if original_length > 0 else 0
            }, "text_preprocessing")
            
            return processed_text.strip()
            
        except Exception as e:
            self.log_error(e, "preprocess_text", text_length=len(text))
            return text  # Retorna texto original em caso de erro
    
    def _remove_html_tags(self, text: str) -> str:
        """Remove tags HTML e converte para texto plano"""
        try:
            # Usar BeautifulSoup para remover HTML
            soup = BeautifulSoup(text, 'html.parser')
            
            # Remover scripts e styles
            for script in soup(["script", "style"]):
                script.decompose()
            
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
    
    def _clean_encoding(self, text: str) -> str:
        """Limpa problemas de encoding"""
        try:
            # Normalizar unicode
            text = unicodedata.normalize('NFKD', text)
            
            # Remover caracteres de controle
            text = ''.join(char for char in text if unicodedata.category(char) != 'Cc')
            
            # Corrigir problemas comuns de encoding
            encoding_fixes = {
                'â€™': "'",
                'â€œ': '"',
                'â€': '"',
                'â€˜': "'",
                'â€¦': '...',
                'Ã§': 'ç',
                'Ã¡': 'á',
                'Ã©': 'é',
                'Ã­': 'í',
                'Ã³': 'ó',
                'Ãº': 'ú',
                'Ã ': 'à',
                'Ã¢': 'â',
                'Ãª': 'ê',
                'Ã´': 'ô',
                'Ã£': 'ã',
                'Ãµ': 'õ',
            }
            
            for wrong, correct in encoding_fixes.items():
                text = text.replace(wrong, correct)
            
            return text
            
        except Exception as e:
            self.log_error(e, "_clean_encoding")
            return text
    
    def _remove_headers_footers(self, text: str) -> str:
        """Remove cabeçalhos e rodapés comuns"""
        try:
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                
                # Pular linhas vazias
                if not line:
                    continue
                
                # Pular linhas com apenas números/caracteres especiais
                if self.patterns['useless_lines'].match(line):
                    continue
                
                # Pular cabeçalhos/rodapés conhecidos
                if self.patterns['headers_footers'].search(line):
                    continue
                
                # Pular linhas muito curtas (provavelmente fragmentos)
                if len(line) < 10:
                    continue
                
                # Pular linhas com texto em maiúsculas excessivo
                if len(self.patterns['excessive_caps'].findall(line)) > 2:
                    continue
                
                cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            self.log_error(e, "_remove_headers_footers")
            return text
    
    def _normalize_spaces(self, text: str) -> str:
        """Normaliza espaços em branco"""
        try:
            # Substituir múltiplos espaços por um único espaço
            text = self.patterns['multiple_spaces'].sub(' ', text)
            
            # Normalizar quebras de linha
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Máximo 2 quebras consecutivas
            text = re.sub(r'\n{3,}', '\n\n', text)   # Máximo 2 quebras consecutivas
            
            return text
            
        except Exception as e:
            self.log_error(e, "_normalize_spaces")
            return text
    
    def _final_cleanup(self, text: str, preserve_structure: bool) -> str:
        """Limpeza final do texto"""
        try:
            # Remover caracteres especiais desnecessários
            text = self.patterns['special_chars'].sub('', text)
            
            # Se não preservar estrutura, remover quebras de linha
            if not preserve_structure:
                text = text.replace('\n', ' ')
                text = self.patterns['multiple_spaces'].sub(' ', text)
            
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
                'length': len(text),
                'words': len(text.split()) if text else 0,
                'sentences': len(re.split(r'[.!?]+', text)) if text else 0,
                'paragraphs': len(text.split('\n\n')) if text else 0,
                'process_numbers': self.patterns['process_numbers'].findall(text),
                'dates': self.patterns['dates'].findall(text),
                'monetary_values': self.patterns['monetary_values'].findall(text),
                'has_html': bool(re.search(r'<[^>]+>', text)),
                'language': 'pt'  # Assumindo português
            }
            
            # Estatísticas de qualidade
            if metadata['words'] > 0:
                metadata['avg_word_length'] = metadata['length'] / metadata['words']
            else:
                metadata['avg_word_length'] = 0
            
            self.log_operation(
                "metadata_extracted",
                text_length=metadata['length'],
                words=metadata['words'],
                sentences=metadata['sentences']
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
                return {'quality_score': 0.0, 'issues': ['empty_text']}
            
            issues = []
            score = 1.0
            
            # Verificar tamanho mínimo
            if len(text) < 100:
                issues.append('text_too_short')
                score -= 0.3
            
            # Verificar se há muitos caracteres especiais
            special_char_ratio = len(re.findall(r'[^\w\s]', text)) / len(text) if text else 0
            if special_char_ratio > 0.3:
                issues.append('too_many_special_chars')
                score -= 0.2
            
            # Verificar se há palavras muito longas (possível lixo)
            words = text.split()
            if words:
                avg_word_length = sum(len(word) for word in words) / len(words)
                if avg_word_length > 15:
                    issues.append('words_too_long')
                    score -= 0.2
            
            # Verificar se há estrutura de sentenças
            sentences = re.split(r'[.!?]+', text)
            if len(sentences) < 3:
                issues.append('too_few_sentences')
                score -= 0.2
            
            # Verificar presença de termos jurídicos
            legal_terms_found = 0
            for term in self.preserve_terms['legal_terms']:
                if term.lower() in text.lower():
                    legal_terms_found += 1
            
            if legal_terms_found == 0:
                issues.append('no_legal_terms')
                score -= 0.1
            
            quality_score = max(0.0, score)
            
            return {
                'quality_score': quality_score,
                'issues': issues,
                'legal_terms_found': legal_terms_found,
                'word_count': len(words) if words else 0,
                'sentence_count': len(sentences),
                'special_char_ratio': special_char_ratio
            }
            
        except Exception as e:
            self.log_error(e, "validate_text_quality")
            return {'quality_score': 0.0, 'issues': ['validation_error']}
    
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
                processed_texts=len(processed_texts)
            )
            
            return processed_texts
            
        except Exception as e:
            self.log_error(e, "batch_preprocess", total_texts=len(texts))
            raise 