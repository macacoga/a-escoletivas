"""
Módulo para extração das partes do processo (reclamante e reclamado)
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

from ..utils.logging import LoggerMixin, log_execution_time


@dataclass
class ProcessPart:
    """Representa uma parte do processo"""
    name: str
    type: str  # 'reclamante' ou 'reclamado'
    cpf_cnpj: Optional[str] = None
    address: Optional[str] = None
    lawyer: Optional[str] = None
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'name': self.name,
            'type': self.type,
            'cpf_cnpj': self.cpf_cnpj,
            'address': self.address,
            'lawyer': self.lawyer,
            'confidence': self.confidence
        }


class PartsExtractor(LoggerMixin):
    """
    Classe para extração das partes do processo judicial
    """
    
    def __init__(self):
        super().__init__()
        
        # Padrões para identificar seções de partes
        self.section_patterns = {
            'reclamante': [
                r'(?:RECLAMANTE|REQUERENTE|AUTOR|EXEQUENTE)[\s\:]+([^\.]+?)(?=\n|RECLAMAD|REQUERID|RÉU|EXECUTAD)',
                r'(?:RECLAMANTE|REQUERENTE|AUTOR|EXEQUENTE)[\s\:]+(.+?)(?=\n\n|\nRECLAMAD|\nREQUERID|\nRÉU|\nEXECUTAD)',
                r'(?:^|\n)(?:RECLAMANTE|REQUERENTE|AUTOR|EXEQUENTE)[\s\:]+(.+?)(?=\n(?:[A-Z]{3,}|$))',
            ],
            'reclamado': [
                r'(?:RECLAMAD[AO]|REQUERID[AO]|RÉU|EXECUTAD[AO])[\s\:]+([^\.]+?)(?=\n|ADVOGAD|PROCURAD|$)',
                r'(?:RECLAMAD[AO]|REQUERID[AO]|RÉU|EXECUTAD[AO])[\s\:]+(.+?)(?=\n\n|\nADVOGAD|\nPROCURAD|$)',
                r'(?:^|\n)(?:RECLAMAD[AO]|REQUERID[AO]|RÉU|EXECUTAD[AO])[\s\:]+(.+?)(?=\n(?:[A-Z]{3,}|$))',
            ]
        }
        
        # Padrões para extrair informações específicas
        self.info_patterns = {
            'cpf': r'CPF[:\s]*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
            'cnpj': r'CNPJ[:\s]*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})',
            'address': r'(?:endereço|residência|domicílio|sito)[:\s]+([^,\n]+(?:,[^,\n]+)*)',
            'lawyer': r'(?:advogado|procurador|representante)[:\s]+([^,\n]+)',
            'oab': r'OAB[:\s]*([A-Z]{2}[:\s]*\d+)',
        }
        
        # Padrões para limpeza de texto
        self.cleanup_patterns = [
            r'\s+', ' ',  # Múltiplos espaços
            r'^\s*[,\.\-\:]\s*', '',  # Pontuação no início
            r'\s*[,\.\-\:]\s*$', '',  # Pontuação no final
            r'\n+', ' ',  # Quebras de linha
            r'\s{2,}', ' ',  # Espaços duplos
        ]
        
        self.logger.info("PartsExtractor inicializado")
    
    @log_execution_time
    def extract_parts(self, text: str) -> Dict[str, Any]:
        """
        Extrai as partes do processo do texto
        
        Args:
            text: Texto da decisão judicial
            
        Returns:
            Dicionário com reclamante e reclamado
        """
        if not text:
            return {'reclamante': None, 'reclamado': None, 'partes_text': ''}
        
        try:
            # Normalizar texto
            normalized_text = self._normalize_text(text)
            
            # Extrair reclamante
            reclamante = self._extract_part(normalized_text, 'reclamante')
            
            # Extrair reclamado
            reclamado = self._extract_part(normalized_text, 'reclamado')
            
            # Extrair texto das partes para referência
            partes_text = self._extract_parts_section(normalized_text)
            
            result = {
                'reclamante': reclamante.to_dict() if reclamante else None,
                'reclamado': reclamado.to_dict() if reclamado else None,
                'partes_text': partes_text,
                'extraction_confidence': self._calculate_extraction_confidence(reclamante, reclamado)
            }
            
            self.log_operation(
                "parts_extracted",
                has_reclamante=reclamante is not None,
                has_reclamado=reclamado is not None,
                confidence=result['extraction_confidence']
            )
            
            return result
            
        except Exception as e:
            self.log_error(e, "extract_parts")
            return {'reclamante': None, 'reclamado': None, 'partes_text': ''}
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza o texto para extração"""
        # Remover caracteres especiais e normalizar
        text = re.sub(r'[^\w\s\.\,\:\;\-\n]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_part(self, text: str, part_type: str) -> Optional[ProcessPart]:
        """Extrai uma parte específica (reclamante ou reclamado)"""
        patterns = self.section_patterns.get(part_type, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                part_text = match.group(1).strip()
                
                if part_text and len(part_text) > 3:
                    # Limpar texto extraído
                    cleaned_text = self._clean_part_text(part_text)
                    
                    # Extrair informações adicionais
                    cpf_cnpj = self._extract_cpf_cnpj(part_text)
                    address = self._extract_address(part_text)
                    lawyer = self._extract_lawyer(part_text)
                    
                    # Calcular confiança
                    confidence = self._calculate_part_confidence(cleaned_text, cpf_cnpj, address)
                    
                    return ProcessPart(
                        name=cleaned_text,
                        type=part_type,
                        cpf_cnpj=cpf_cnpj,
                        address=address,
                        lawyer=lawyer,
                        confidence=confidence
                    )
        
        return None
    
    def _clean_part_text(self, text: str) -> str:
        """Limpa o texto da parte extraída"""
        # Aplicar padrões de limpeza
        for pattern, replacement in zip(self.cleanup_patterns[::2], self.cleanup_patterns[1::2]):
            text = re.sub(pattern, replacement, text)
        
        # Remover informações extras (CPF, endereço, etc.)
        text = re.sub(r'(?:CPF|CNPJ|OAB)[:\s]+[^\s,]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?:endereço|residência|domicílio)[:\s]+[^,\n]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?:advogado|procurador)[:\s]+[^,\n]+', '', text, flags=re.IGNORECASE)
        
        # Limpar pontuação extra
        text = re.sub(r'[,\.\-\:]+$', '', text.strip())
        text = re.sub(r'^[,\.\-\:]+', '', text.strip())
        
        return text.strip()
    
    def _extract_cpf_cnpj(self, text: str) -> Optional[str]:
        """Extrai CPF ou CNPJ do texto"""
        # Tentar CPF primeiro
        cpf_match = re.search(self.info_patterns['cpf'], text, re.IGNORECASE)
        if cpf_match:
            return cpf_match.group(1)
        
        # Tentar CNPJ
        cnpj_match = re.search(self.info_patterns['cnpj'], text, re.IGNORECASE)
        if cnpj_match:
            return cnpj_match.group(1)
        
        return None
    
    def _extract_address(self, text: str) -> Optional[str]:
        """Extrai endereço do texto"""
        match = re.search(self.info_patterns['address'], text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_lawyer(self, text: str) -> Optional[str]:
        """Extrai advogado do texto"""
        match = re.search(self.info_patterns['lawyer'], text, re.IGNORECASE)
        if match:
            lawyer = match.group(1).strip()
            # Verificar se tem OAB
            oab_match = re.search(self.info_patterns['oab'], text, re.IGNORECASE)
            if oab_match:
                lawyer += f" - OAB: {oab_match.group(1)}"
            return lawyer
        return None
    
    def _extract_parts_section(self, text: str) -> str:
        """Extrai a seção completa das partes para referência"""
        # Procurar seção que contenha reclamante e reclamado
        pattern = r'(?:RECLAMANTE|REQUERENTE|AUTOR)[\s\S]*?(?:RECLAMAD|REQUERID|RÉU)[\s\S]*?(?=\n\n|RELATÓRIO|FUNDAMENTAÇÃO|DECISÃO|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        
        if match:
            return match.group(0).strip()
        
        return ''
    
    def _calculate_part_confidence(self, name: str, cpf_cnpj: Optional[str], address: Optional[str]) -> float:
        """Calcula confiança da extração da parte"""
        confidence = 0.5  # Base
        
        # Bonus por ter nome válido
        if name and len(name) > 5:
            confidence += 0.2
        
        # Bonus por ter CPF/CNPJ
        if cpf_cnpj:
            confidence += 0.2
        
        # Bonus por ter endereço
        if address:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_extraction_confidence(self, reclamante: Optional[ProcessPart], reclamado: Optional[ProcessPart]) -> float:
        """Calcula confiança geral da extração"""
        if not reclamante and not reclamado:
            return 0.0
        
        if reclamante and reclamado:
            return (reclamante.confidence + reclamado.confidence) / 2
        
        if reclamante:
            return reclamante.confidence * 0.8  # Penalizar por não ter reclamado
        
        if reclamado:
            return reclamado.confidence * 0.8  # Penalizar por não ter reclamante
        
        return 0.0
    
    def format_parts_for_display(self, parts_data: Dict[str, Any]) -> str:
        """Formata as partes para exibição"""
        if not parts_data:
            return "Partes não identificadas"
        
        result = []
        
        # Reclamante
        if parts_data.get('reclamante'):
            rec = parts_data['reclamante']
            line = f"Reclamante: {rec['name']}"
            if rec.get('cpf_cnpj'):
                line += f" (CPF/CNPJ: {rec['cpf_cnpj']})"
            result.append(line)
        
        # Reclamado
        if parts_data.get('reclamado'):
            rec = parts_data['reclamado']
            line = f"Reclamado: {rec['name']}"
            if rec.get('cpf_cnpj'):
                line += f" (CPF/CNPJ: {rec['cpf_cnpj']})"
            result.append(line)
        
        return " | ".join(result) if result else "Partes não identificadas"
    
    def validate_parts(self, parts_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e melhora a qualidade das partes extraídas"""
        if not parts_data:
            return parts_data
        
        validation_result = {
            'is_valid': False,
            'issues': [],
            'suggestions': []
        }
        
        # Verificar se tem pelo menos uma parte
        has_reclamante = parts_data.get('reclamante') is not None
        has_reclamado = parts_data.get('reclamado') is not None
        
        if not has_reclamante and not has_reclamado:
            validation_result['issues'].append("Nenhuma parte identificada")
            validation_result['suggestions'].append("Verificar se o texto contém seção de partes")
            return validation_result
        
        if not has_reclamante:
            validation_result['issues'].append("Reclamante não identificado")
        
        if not has_reclamado:
            validation_result['issues'].append("Reclamado não identificado")
        
        # Verificar qualidade dos nomes
        for part_type in ['reclamante', 'reclamado']:
            part = parts_data.get(part_type)
            if part and part.get('name'):
                name = part['name']
                if len(name) < 3:
                    validation_result['issues'].append(f"Nome do {part_type} muito curto")
                elif len(name) > 200:
                    validation_result['issues'].append(f"Nome do {part_type} muito longo")
        
        # Determinar se é válido
        validation_result['is_valid'] = len(validation_result['issues']) == 0
        
        return validation_result 