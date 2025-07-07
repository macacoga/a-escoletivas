#!/usr/bin/env python3
"""
Analisador de resultados de decisões judiciais - Versão Melhorada
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class ResultadoAnalise:
    """Resultado da análise de decisão"""
    resultado_principal: str
    confianca: float
    evidencias: List[str]
    metodo_usado: str
    detalhes: Dict[str, Any]


class ResultadoAnalyzer:
    """Analisador inteligente de resultados de decisões judiciais - Versão Melhorada"""
    
    def __init__(self):
        self.padroes_favoravel = self._criar_padroes_favoravel()
        self.padroes_desfavoravel = self._criar_padroes_desfavoravel()
        self.padroes_parcial = self._criar_padroes_parcial()
        self.padroes_contexto = self._criar_padroes_contexto()
        self.padroes_inferencia = self._criar_padroes_inferencia()
    
    def _criar_padroes_favoravel(self) -> List[Dict[str, Any]]:
        """Cria padrões expandidos para decisões favoráveis"""
        return [
            # Padrões básicos
            {'pattern': r'\b(procedente|procedência)\b', 'weight': 0.9, 'tipo': 'decisao_direta'},
            {'pattern': r'\b(concedo|conceder|concedido|concedida)\b', 'weight': 0.8, 'tipo': 'concessao'},
            {'pattern': r'\b(defiro|deferimento|deferido|deferida)\b', 'weight': 0.8, 'tipo': 'deferimento'},
            {'pattern': r'\b(acolho|acolher|acolhido|acolhida)\b', 'weight': 0.8, 'tipo': 'acolhimento'},
            {'pattern': r'\b(condeno|condenação|condenado|condenada)\b', 'weight': 0.7, 'tipo': 'condenacao'},
            
            # Padrões contextuais
            {'pattern': r'julgo\s+procedente', 'weight': 0.95, 'tipo': 'julgamento_procedente'},
            {'pattern': r'sentença\s+procedente', 'weight': 0.9, 'tipo': 'sentenca_procedente'},
            {'pattern': r'ação\s+procedente', 'weight': 0.9, 'tipo': 'acao_procedente'},
            {'pattern': r'pedido\s+procedente', 'weight': 0.85, 'tipo': 'pedido_procedente'},
            {'pattern': r'recurso\s+provido', 'weight': 0.8, 'tipo': 'recurso_provido'},
            {'pattern': r'dar\s+provimento', 'weight': 0.8, 'tipo': 'dar_provimento'},
            {'pattern': r'dou\s+provimento', 'weight': 0.8, 'tipo': 'dou_provimento'},
            {'pattern': r'provimento\s+ao\s+recurso', 'weight': 0.8, 'tipo': 'provimento_recurso'},
            
            # Padrões de resultado
            {'pattern': r'reconheço\s+o\s+direito', 'weight': 0.8, 'tipo': 'reconhecimento_direito'},
            {'pattern': r'tem\s+direito', 'weight': 0.7, 'tipo': 'tem_direito'},
            {'pattern': r'faz\s+jus', 'weight': 0.7, 'tipo': 'faz_jus'},
            {'pattern': r'é\s+devido', 'weight': 0.7, 'tipo': 'e_devido'},
            {'pattern': r'deve\s+ser\s+pago', 'weight': 0.7, 'tipo': 'deve_ser_pago'},
            {'pattern': r'deve\s+pagar', 'weight': 0.7, 'tipo': 'deve_pagar'},
            
            # Padrões de condenação
            {'pattern': r'condeno\s+a\s+ré', 'weight': 0.85, 'tipo': 'condeno_re'},
            {'pattern': r'condeno\s+o\s+réu', 'weight': 0.85, 'tipo': 'condeno_reu'},
            {'pattern': r'condeno\s+a\s+empresa', 'weight': 0.8, 'tipo': 'condeno_empresa'},
            {'pattern': r'condeno\s+.*\s+ao\s+pagamento', 'weight': 0.8, 'tipo': 'condeno_pagamento'},
            {'pattern': r'condeno\s+.*\s+a\s+pagar', 'weight': 0.8, 'tipo': 'condeno_pagar'},
            
            # Padrões de ganho/vitória
            {'pattern': r'\b(ganhou|venceu|vitória|êxito)\b', 'weight': 0.6, 'tipo': 'vitoria'},
            {'pattern': r'em\s+favor\s+do\s+requerente', 'weight': 0.7, 'tipo': 'favor_requerente'},
            {'pattern': r'em\s+favor\s+do\s+autor', 'weight': 0.7, 'tipo': 'favor_autor'},
            {'pattern': r'razão\s+ao\s+requerente', 'weight': 0.7, 'tipo': 'razao_requerente'},
            {'pattern': r'razão\s+ao\s+autor', 'weight': 0.7, 'tipo': 'razao_autor'},
            
            # Padrões de valores monetários (indicam condenação)
            {'pattern': r'pagar\s+.*\s+r\$', 'weight': 0.6, 'tipo': 'pagamento_valor'},
            {'pattern': r'indenização\s+.*\s+r\$', 'weight': 0.6, 'tipo': 'indenizacao_valor'},
            {'pattern': r'valor\s+de\s+r\$', 'weight': 0.5, 'tipo': 'valor_monetario'},
            
            # Padrões específicos do direito trabalhista
            {'pattern': r'horas\s+extras\s+devidas', 'weight': 0.7, 'tipo': 'horas_extras_devidas'},
            {'pattern': r'adicional\s+.*\s+devido', 'weight': 0.7, 'tipo': 'adicional_devido'},
            {'pattern': r'verbas\s+rescisórias\s+devidas', 'weight': 0.7, 'tipo': 'verbas_devidas'},
            {'pattern': r'aviso\s+prévio\s+devido', 'weight': 0.7, 'tipo': 'aviso_devido'},
            {'pattern': r'décimo\s+terceiro\s+devido', 'weight': 0.7, 'tipo': 'decimo_devido'},
            {'pattern': r'férias\s+devidas', 'weight': 0.7, 'tipo': 'ferias_devidas'},
            {'pattern': r'fgts\s+devido', 'weight': 0.7, 'tipo': 'fgts_devido'},
            
            # Padrões de determinação/ordem
            {'pattern': r'determino\s+que', 'weight': 0.6, 'tipo': 'determinacao'},
            {'pattern': r'ordeno\s+que', 'weight': 0.6, 'tipo': 'ordem'},
            {'pattern': r'deve\s+.*\s+cumprir', 'weight': 0.6, 'tipo': 'deve_cumprir'},
        ]
    
    def _criar_padroes_desfavoravel(self) -> List[Dict[str, Any]]:
        """Cria padrões expandidos para decisões desfavoráveis"""
        return [
            # Padrões básicos
            {'pattern': r'\b(improcedente|improcedência)\b', 'weight': 0.9, 'tipo': 'decisao_direta'},
            {'pattern': r'\b(nego|negar|negado|negada)\b', 'weight': 0.8, 'tipo': 'negacao'},
            {'pattern': r'\b(indefiro|indeferimento|indeferido|indeferida)\b', 'weight': 0.8, 'tipo': 'indeferimento'},
            {'pattern': r'\b(rejeito|rejeição|rejeitado|rejeitada)\b', 'weight': 0.8, 'tipo': 'rejeicao'},
            {'pattern': r'\b(desconheço|desconhecimento)\b', 'weight': 0.7, 'tipo': 'desconhecimento'},
            
            # Padrões contextuais
            {'pattern': r'julgo\s+improcedente', 'weight': 0.95, 'tipo': 'julgamento_improcedente'},
            {'pattern': r'sentença\s+improcedente', 'weight': 0.9, 'tipo': 'sentenca_improcedente'},
            {'pattern': r'ação\s+improcedente', 'weight': 0.9, 'tipo': 'acao_improcedente'},
            {'pattern': r'pedido\s+improcedente', 'weight': 0.85, 'tipo': 'pedido_improcedente'},
            {'pattern': r'recurso\s+desprovido', 'weight': 0.8, 'tipo': 'recurso_desprovido'},
            {'pattern': r'negar\s+provimento', 'weight': 0.8, 'tipo': 'negar_provimento'},
            {'pattern': r'nego\s+provimento', 'weight': 0.8, 'tipo': 'nego_provimento'},
            {'pattern': r'nego\s+seguimento', 'weight': 0.8, 'tipo': 'nego_seguimento'},
            {'pattern': r'denego\s+seguimento', 'weight': 0.8, 'tipo': 'denego_seguimento'},
            {'pattern': r'nega\s+provimento', 'weight': 0.8, 'tipo': 'nega_provimento'},
            {'pattern': r'desprovimento\s+do\s+recurso', 'weight': 0.8, 'tipo': 'desprovimento_recurso'},
            {'pattern': r'rejeitado\s+o\s+recurso', 'weight': 0.8, 'tipo': 'rejeitado_recurso'},
            {'pattern': r'rejeitado\s+o\s+pedido', 'weight': 0.8, 'tipo': 'rejeitado_pedido'},
            {'pattern': r'rejeitado\s+o\s+recurso', 'weight': 0.8, 'tipo': 'rejeitado_recurso'},
            
            # Padrões de não direito
            {'pattern': r'não\s+tem\s+direito', 'weight': 0.8, 'tipo': 'nao_tem_direito'},
            {'pattern': r'não\s+faz\s+jus', 'weight': 0.8, 'tipo': 'nao_faz_jus'},
            {'pattern': r'não\s+é\s+devido', 'weight': 0.8, 'tipo': 'nao_e_devido'},
            {'pattern': r'ausência\s+de\s+direito', 'weight': 0.7, 'tipo': 'ausencia_direito'},
            {'pattern': r'não\s+deve\s+ser\s+pago', 'weight': 0.7, 'tipo': 'nao_deve_pago'},
            {'pattern': r'não\s+procede', 'weight': 0.7, 'tipo': 'nao_procede'},
            
            # Padrões de extinção
            {'pattern': r'extingo\s+o\s+processo', 'weight': 0.7, 'tipo': 'extincao_processo'},
            {'pattern': r'extingo\s+a\s+execução', 'weight': 0.6, 'tipo': 'extincao_execucao'},
            {'pattern': r'processo\s+extinto', 'weight': 0.6, 'tipo': 'processo_extinto'},
            
            # Padrões de perda/derrota
            {'pattern': r'\b(perdeu|perderam|derrota|insucesso)\b', 'weight': 0.6, 'tipo': 'derrota'},
            {'pattern': r'em\s+favor\s+do\s+requerido', 'weight': 0.7, 'tipo': 'favor_requerido'},
            {'pattern': r'em\s+favor\s+do\s+réu', 'weight': 0.7, 'tipo': 'favor_reu'},
            {'pattern': r'razão\s+ao\s+requerido', 'weight': 0.7, 'tipo': 'razao_requerido'},
            {'pattern': r'razão\s+ao\s+réu', 'weight': 0.7, 'tipo': 'razao_reu'},
            
            # Padrões de absolvição
            {'pattern': r'\b(absolvo|absolvição|absolvido|absolvida)\b', 'weight': 0.8, 'tipo': 'absolvicao'},
            {'pattern': r'isento\s+de\s+pagamento', 'weight': 0.7, 'tipo': 'isento_pagamento'},
            {'pattern': r'sem\s+condenação', 'weight': 0.7, 'tipo': 'sem_condenacao'},
            
            # Padrões de falta de prova
            {'pattern': r'falta\s+de\s+prova', 'weight': 0.6, 'tipo': 'falta_prova'},
            {'pattern': r'não\s+comprovado', 'weight': 0.6, 'tipo': 'nao_comprovado'},
            {'pattern': r'prova\s+insuficiente', 'weight': 0.6, 'tipo': 'prova_insuficiente'},
            {'pattern': r'não\s+demonstrado', 'weight': 0.6, 'tipo': 'nao_demonstrado'},
            
            # Padrões de arquivamento
            {'pattern': r'\b(arquivo|arquivado|arquivamento)\b', 'weight': 0.6, 'tipo': 'arquivamento'},
            {'pattern': r'baixa\s+dos\s+autos', 'weight': 0.5, 'tipo': 'baixa_autos'},
        ]
    
    def _criar_padroes_parcial(self) -> List[Dict[str, Any]]:
        """Cria padrões expandidos para decisões parciais"""
        return [
            # Padrões básicos
            {'pattern': r'\b(parcialmente)\b', 'weight': 0.9, 'tipo': 'parcialmente'},
            {'pattern': r'\b(em\s+parte)\b', 'weight': 0.9, 'tipo': 'em_parte'},
            {'pattern': r'\b(parte\s+do\s+pedido)\b', 'weight': 0.8, 'tipo': 'parte_pedido'},
            
            # Padrões contextuais
            {'pattern': r'julgo\s+parcialmente\s+procedente', 'weight': 0.95, 'tipo': 'julgamento_parcial'},
            {'pattern': r'procedente\s+em\s+parte', 'weight': 0.9, 'tipo': 'procedente_parte'},
            {'pattern': r'acolho\s+parcialmente', 'weight': 0.85, 'tipo': 'acolho_parcialmente'},
            {'pattern': r'defiro\s+parcialmente', 'weight': 0.85, 'tipo': 'defiro_parcialmente'},
            {'pattern': r'concedo\s+parcialmente', 'weight': 0.85, 'tipo': 'concedo_parcialmente'},
            
            # Padrões de provimento parcial
            {'pattern': r'recurso\s+parcialmente\s+provido', 'weight': 0.8, 'tipo': 'recurso_parcial'},
            {'pattern': r'dar\s+parcial\s+provimento', 'weight': 0.8, 'tipo': 'provimento_parcial'},
            {'pattern': r'dou\s+parcial\s+provimento', 'weight': 0.8, 'tipo': 'dou_parcial'},
            
            # Padrões de divisão
            {'pattern': r'alguns\s+pedidos', 'weight': 0.7, 'tipo': 'alguns_pedidos'},
            {'pattern': r'parte\s+dos\s+direitos', 'weight': 0.7, 'tipo': 'parte_direitos'},
            {'pattern': r'apenas\s+.*\s+devido', 'weight': 0.7, 'tipo': 'apenas_devido'},
            {'pattern': r'somente\s+.*\s+procedente', 'weight': 0.7, 'tipo': 'somente_procedente'},
            
            # Padrões de limitação
            {'pattern': r'limitado\s+a', 'weight': 0.6, 'tipo': 'limitado_a'},
            {'pattern': r'restrito\s+a', 'weight': 0.6, 'tipo': 'restrito_a'},
            {'pattern': r'no\s+que\s+se\s+refere\s+a', 'weight': 0.6, 'tipo': 'refere_a'},
        ]
    
    def _criar_padroes_contexto(self) -> List[Dict[str, Any]]:
        """Cria padrões para identificar contexto da decisão"""
        return [
            # Identificadores de seção dispositiva
            {'pattern': r'dispositivo|dispositiva', 'weight': 1.0, 'tipo': 'secao_dispositiva'},
            {'pattern': r'isto\s+posto|diante\s+do\s+exposto', 'weight': 0.9, 'tipo': 'conclusao'},
            {'pattern': r'pelo\s+exposto|ante\s+o\s+exposto', 'weight': 0.9, 'tipo': 'conclusao'},
            {'pattern': r'assim\s+sendo|dessa\s+forma', 'weight': 0.8, 'tipo': 'conclusao'},
            {'pattern': r'por\s+todo\s+o\s+exposto', 'weight': 0.9, 'tipo': 'conclusao'},
            {'pattern': r'em\s+face\s+do\s+exposto', 'weight': 0.9, 'tipo': 'conclusao'},
            
            # Identificadores de decisão
            {'pattern': r'decidir?o|decido', 'weight': 0.8, 'tipo': 'decisao'},
            {'pattern': r'julgar?o|julgo', 'weight': 0.9, 'tipo': 'julgamento'},
            {'pattern': r'sentenciar?o|sentencio', 'weight': 0.9, 'tipo': 'sentenciamento'},
            {'pattern': r'determinar?o|determino', 'weight': 0.8, 'tipo': 'determinacao'},
            {'pattern': r'ordenar?o|ordeno', 'weight': 0.8, 'tipo': 'ordem'},
            
            # Identificadores de mérito
            {'pattern': r'no\s+mérito|quanto\s+ao\s+mérito', 'weight': 0.8, 'tipo': 'merito'},
            {'pattern': r'análise\s+do\s+mérito', 'weight': 0.8, 'tipo': 'analise_merito'},
            {'pattern': r'exame\s+do\s+mérito', 'weight': 0.8, 'tipo': 'exame_merito'},
        ]
    
    def _criar_padroes_inferencia(self) -> List[Dict[str, Any]]:
        """Cria padrões para inferir resultado quando não há palavras-chave diretas"""
        return [
            # Padrões de pagamento (geralmente favorável)
            {'pattern': r'pagamento\s+de\s+r\$', 'weight': 0.5, 'tipo': 'pagamento_valor', 'resultado': 'favoravel'},
            {'pattern': r'valor\s+de\s+r\$.*\s+devido', 'weight': 0.6, 'tipo': 'valor_devido', 'resultado': 'favoravel'},
            {'pattern': r'indenização\s+de\s+r\$', 'weight': 0.6, 'tipo': 'indenizacao', 'resultado': 'favoravel'},
            
            # Padrões de negação de pagamento (geralmente desfavorável)
            {'pattern': r'não\s+há\s+que\s+se\s+falar\s+em', 'weight': 0.6, 'tipo': 'nao_ha_falar', 'resultado': 'desfavoravel'},
            {'pattern': r'não\s+se\s+vislumbra', 'weight': 0.5, 'tipo': 'nao_vislumbra', 'resultado': 'desfavoravel'},
            {'pattern': r'não\s+se\s+verifica', 'weight': 0.5, 'tipo': 'nao_verifica', 'resultado': 'desfavoravel'},
            
            # Padrões de cumprimento (geralmente favorável)
            {'pattern': r'cumprir\s+.*\s+obrigação', 'weight': 0.5, 'tipo': 'cumprir_obrigacao', 'resultado': 'favoravel'},
            {'pattern': r'obrigação\s+de\s+fazer', 'weight': 0.5, 'tipo': 'obrigacao_fazer', 'resultado': 'favoravel'},
            {'pattern': r'obrigação\s+de\s+pagar', 'weight': 0.6, 'tipo': 'obrigacao_pagar', 'resultado': 'favoravel'},
            
            # Padrões de documentos específicos
            {'pattern': r'carteira\s+de\s+trabalho.*\s+anotação', 'weight': 0.5, 'tipo': 'ctps_anotacao', 'resultado': 'favoravel'},
            {'pattern': r'registro\s+em\s+carteira', 'weight': 0.5, 'tipo': 'registro_carteira', 'resultado': 'favoravel'},
            {'pattern': r'vínculo\s+empregatício\s+reconhecido', 'weight': 0.7, 'tipo': 'vinculo_reconhecido', 'resultado': 'favoravel'},
            
            # Padrões de tempo/prazo
            {'pattern': r'prazo\s+para\s+cumprimento', 'weight': 0.4, 'tipo': 'prazo_cumprimento', 'resultado': 'favoravel'},
            {'pattern': r'no\s+prazo\s+de\s+.*\s+dias', 'weight': 0.4, 'tipo': 'prazo_dias', 'resultado': 'favoravel'},
        ]
    
    def analisar_resultado(self, texto: str, direitos_trabalhistas: Optional[str] = None) -> ResultadoAnalise:
        """Analisa o resultado de uma decisão judicial com algoritmo melhorado"""
        
        if not texto or len(texto.strip()) < 10:
            return ResultadoAnalise(
                resultado_principal="Resultado não identificado",
                confianca=0.0,
                evidencias=["Texto vazio ou muito curto"],
                metodo_usado="texto_insuficiente",
                detalhes={}
            )
        
        # Tentar múltiplos métodos de análise
        resultados = []
        
        # Método 1: Análise por padrões regex expandidos
        resultado_regex = self._analisar_por_padroes(texto)
        if resultado_regex:
            resultados.append(resultado_regex)
        
        # Método 2: Análise por inferência (novo)
        resultado_inferencia = self._analisar_por_inferencia(texto)
        if resultado_inferencia:
            resultados.append(resultado_inferencia)
        
        # Método 3: Análise por direitos trabalhistas
        if direitos_trabalhistas:
            resultado_direitos = self._analisar_por_direitos(direitos_trabalhistas)
            if resultado_direitos:
                resultados.append(resultado_direitos)
        
        # Método 4: Análise por contexto semântico
        resultado_semantico = self._analisar_por_contexto(texto)
        if resultado_semantico:
            resultados.append(resultado_semantico)
        
        # Método 5: Análise por estrutura do documento
        resultado_estrutura = self._analisar_por_estrutura(texto)
        if resultado_estrutura:
            resultados.append(resultado_estrutura)
        
        # Método 6: Análise por padrões de linguagem jurídica (novo)
        resultado_linguagem = self._analisar_por_linguagem_juridica(texto)
        if resultado_linguagem:
            resultados.append(resultado_linguagem)
        
        # Combinar resultados
        if resultados:
            return self._combinar_resultados(resultados)
        else:
            return ResultadoAnalise(
                resultado_principal="Resultado não identificado",
                confianca=0.0,
                evidencias=["Nenhum padrão identificado"],
                metodo_usado="sem_padroes",
                detalhes={"tamanho_texto": len(texto)}
            )
    
    def _analisar_por_inferencia(self, texto: str) -> Optional[ResultadoAnalise]:
        """Analisa usando padrões de inferência"""
        
        texto_lower = texto.lower()
        evidencias = []
        score_favoravel = 0.0
        score_desfavoravel = 0.0
        
        for padrao in self.padroes_inferencia:
            matches = re.finditer(padrao['pattern'], texto_lower, re.IGNORECASE)
            for match in matches:
                peso = padrao['weight']
                resultado_esperado = padrao['resultado']
                
                if resultado_esperado == 'favoravel':
                    score_favoravel += peso
                elif resultado_esperado == 'desfavoravel':
                    score_desfavoravel += peso
                
                evidencias.append(f"inferencia_{padrao['tipo']}: '{match.group()}'")
        
        if score_favoravel == 0 and score_desfavoravel == 0:
            return None
        
        if score_favoravel > score_desfavoravel:
            resultado = "FAVORÁVEL AO REQUERENTE"
            confianca = min(score_favoravel / 2.0, 0.8)  # Máximo 0.8 para inferência
        else:
            resultado = "DESFAVORÁVEL AO REQUERENTE"
            confianca = min(score_desfavoravel / 2.0, 0.8)
        
        return ResultadoAnalise(
            resultado_principal=resultado,
            confianca=confianca,
            evidencias=evidencias,
            metodo_usado="inferencia",
            detalhes={
                "score_favoravel": score_favoravel,
                "score_desfavoravel": score_desfavoravel
            }
        )
    
    def _analisar_por_linguagem_juridica(self, texto: str) -> Optional[ResultadoAnalise]:
        """Analisa usando padrões específicos da linguagem jurídica"""
        
        texto_lower = texto.lower()
        evidencias = []
        score = 0.0
        
        # Padrões específicos para documentos jurídicos trabalhistas
        padroes_linguagem = [
            # Conclusões típicas de sentenças favoráveis
            {'pattern': r'pelos\s+fundamentos\s+.*\s+procedente', 'weight': 0.8, 'resultado': 'favoravel'},
            {'pattern': r'pelas\s+razões\s+.*\s+procedente', 'weight': 0.8, 'resultado': 'favoravel'},
            {'pattern': r'face\s+ao\s+conjunto\s+probatório', 'weight': 0.5, 'resultado': 'favoravel'},
            
            # Conclusões típicas de sentenças desfavoráveis
            {'pattern': r'pelos\s+fundamentos\s+.*\s+improcedente', 'weight': 0.8, 'resultado': 'desfavoravel'},
            {'pattern': r'pelas\s+razões\s+.*\s+improcedente', 'weight': 0.8, 'resultado': 'desfavoravel'},
            {'pattern': r'ausência\s+de\s+elementos\s+probatórios', 'weight': 0.6, 'resultado': 'desfavoravel'},
            
            # Padrões de fundamentação
            {'pattern': r'restou\s+comprovado', 'weight': 0.6, 'resultado': 'favoravel'},
            {'pattern': r'não\s+restou\s+comprovado', 'weight': 0.6, 'resultado': 'desfavoravel'},
            {'pattern': r'ficou\s+demonstrado', 'weight': 0.6, 'resultado': 'favoravel'},
            {'pattern': r'não\s+ficou\s+demonstrado', 'weight': 0.6, 'resultado': 'desfavoravel'},
        ]
        
        score_favoravel = 0.0
        score_desfavoravel = 0.0
        
        for padrao in padroes_linguagem:
            matches = re.finditer(padrao['pattern'], texto_lower, re.IGNORECASE)
            for match in matches:
                peso = padrao['weight']
                resultado_esperado = padrao['resultado']
                
                if resultado_esperado == 'favoravel':
                    score_favoravel += peso
                elif resultado_esperado == 'desfavoravel':
                    score_desfavoravel += peso
                
                evidencias.append(f"linguagem_{resultado_esperado}: '{match.group()}'")
        
        if score_favoravel == 0 and score_desfavoravel == 0:
            return None
        
        if score_favoravel > score_desfavoravel:
            resultado = "FAVORÁVEL AO REQUERENTE"
            confianca = min(score_favoravel / 2.0, 0.7)
        else:
            resultado = "DESFAVORÁVEL AO REQUERENTE"
            confianca = min(score_desfavoravel / 2.0, 0.7)
        
        return ResultadoAnalise(
            resultado_principal=resultado,
            confianca=confianca,
            evidencias=evidencias,
            metodo_usado="linguagem_juridica",
            detalhes={
                "score_favoravel": score_favoravel,
                "score_desfavoravel": score_desfavoravel
            }
        )
    
    def _analisar_por_padroes(self, texto: str) -> Optional[ResultadoAnalise]:
        """Analisa usando padrões regex expandidos"""
        
        texto_lower = texto.lower()
        evidencias_favoravel = []
        evidencias_desfavoravel = []
        evidencias_parcial = []
        
        score_favoravel = 0.0
        score_desfavoravel = 0.0
        score_parcial = 0.0
        
        # Verificar padrões favoráveis
        for padrao in self.padroes_favoravel:
            matches = re.finditer(padrao['pattern'], texto_lower, re.IGNORECASE)
            for match in matches:
                score_favoravel += padrao['weight']
                evidencias_favoravel.append(f"{padrao['tipo']}: '{match.group()}'")
        
        # Verificar padrões desfavoráveis
        for padrao in self.padroes_desfavoravel:
            matches = re.finditer(padrao['pattern'], texto_lower, re.IGNORECASE)
            for match in matches:
                score_desfavoravel += padrao['weight']
                evidencias_desfavoravel.append(f"{padrao['tipo']}: '{match.group()}'")
        
        # Verificar padrões parciais
        for padrao in self.padroes_parcial:
            matches = re.finditer(padrao['pattern'], texto_lower, re.IGNORECASE)
            for match in matches:
                score_parcial += padrao['weight']
                evidencias_parcial.append(f"{padrao['tipo']}: '{match.group()}'")
        
        # Determinar resultado
        max_score = max(score_favoravel, score_desfavoravel, score_parcial)
        
        if max_score == 0:
            return None
        
        if score_parcial == max_score:
            resultado = "PARCIALMENTE FAVORÁVEL"
            evidencias = evidencias_parcial
            confianca = min(score_parcial / 2.0, 1.0)
        elif score_favoravel == max_score:
            resultado = "FAVORÁVEL AO REQUERENTE"
            evidencias = evidencias_favoravel
            confianca = min(score_favoravel / 2.0, 1.0)
        else:
            resultado = "DESFAVORÁVEL AO REQUERENTE"
            evidencias = evidencias_desfavoravel
            confianca = min(score_desfavoravel / 2.0, 1.0)
        
        return ResultadoAnalise(
            resultado_principal=resultado,
            confianca=confianca,
            evidencias=evidencias,
            metodo_usado="padroes_regex",
            detalhes={
                "score_favoravel": score_favoravel,
                "score_desfavoravel": score_desfavoravel,
                "score_parcial": score_parcial
            }
        )
    
    def _analisar_por_direitos(self, direitos_json: str) -> Optional[ResultadoAnalise]:
        """Analisa usando dados de direitos trabalhistas"""
        
        try:
            direitos = json.loads(direitos_json)
            if not isinstance(direitos, list) or not direitos:
                return None
            
            resultados_direitos = []
            evidencias = []
            
            for direito in direitos:
                if isinstance(direito, dict):
                    outcome = direito.get('decision_outcome', '').lower()
                    tipo = direito.get('type', direito.get('description', 'Direito'))
                    
                    if outcome in ['granted', 'concedido', 'deferido']:
                        resultados_direitos.append('favoravel')
                        evidencias.append(f"Direito {tipo}: {outcome}")
                    elif outcome in ['denied', 'negado', 'indeferido']:
                        resultados_direitos.append('desfavoravel')
                        evidencias.append(f"Direito {tipo}: {outcome}")
                    elif outcome in ['partially_granted', 'parcialmente']:
                        resultados_direitos.append('parcial')
                        evidencias.append(f"Direito {tipo}: {outcome}")
            
            if not resultados_direitos:
                return None
            
            # Determinar resultado majoritário
            favoravel_count = resultados_direitos.count('favoravel')
            desfavoravel_count = resultados_direitos.count('desfavoravel')
            parcial_count = resultados_direitos.count('parcial')
            
            total = len(resultados_direitos)
            
            if parcial_count > 0 or (favoravel_count > 0 and desfavoravel_count > 0):
                resultado = "PARCIALMENTE FAVORÁVEL"
                confianca = 0.8
            elif favoravel_count > desfavoravel_count:
                resultado = "FAVORÁVEL AO REQUERENTE"
                confianca = favoravel_count / total
            elif desfavoravel_count > favoravel_count:
                resultado = "DESFAVORÁVEL AO REQUERENTE"
                confianca = desfavoravel_count / total
            else:
                resultado = "PARCIALMENTE FAVORÁVEL"
                confianca = 0.5
            
            return ResultadoAnalise(
                resultado_principal=resultado,
                confianca=confianca,
                evidencias=evidencias,
                metodo_usado="direitos_trabalhistas",
                detalhes={
                    "total_direitos": total,
                    "favoravel_count": favoravel_count,
                    "desfavoravel_count": desfavoravel_count,
                    "parcial_count": parcial_count
                }
            )
            
        except (json.JSONDecodeError, TypeError):
            return None
    
    def _analisar_por_contexto(self, texto: str) -> Optional[ResultadoAnalise]:
        """Analisa usando contexto semântico"""
        
        # Buscar seções dispositivas
        texto_lower = texto.lower()
        
        # Identificar seções importantes
        secoes_dispositivas = []
        for padrao in self.padroes_contexto:
            matches = re.finditer(padrao['pattern'], texto_lower, re.IGNORECASE)
            for match in matches:
                inicio = max(0, match.start() - 100)
                fim = min(len(texto), match.end() + 200)
                secao = texto[inicio:fim]
                secoes_dispositivas.append(secao)
        
        if not secoes_dispositivas:
            return None
        
        # Analisar cada seção dispositiva
        resultados_secoes = []
        evidencias = []
        
        for secao in secoes_dispositivas:
            resultado_secao = self._analisar_por_padroes(secao)
            if resultado_secao and resultado_secao.confianca > 0.3:
                resultados_secoes.append(resultado_secao)
                evidencias.extend(resultado_secao.evidencias)
        
        if not resultados_secoes:
            return None
        
        # Combinar resultados das seções
        return self._combinar_resultados(resultados_secoes)
    
    def _analisar_por_estrutura(self, texto: str) -> Optional[ResultadoAnalise]:
        """Analisa usando estrutura do documento"""
        
        # Buscar por estruturas típicas de decisões
        padroes_estrutura = [
            r'sentença.*?(?:procedente|improcedente|parcialmente)',
            r'acórdão.*?(?:provimento|desprovimento|parcial)',
            r'decisão.*?(?:defiro|indefiro|concedo|nego)',
            r'julgo.*?(?:procedente|improcedente|parcialmente)',
            r'dispositivo.*?(?:procedente|improcedente|parcialmente)',
        ]
        
        evidencias = []
        scores = []
        
        for padrao in padroes_estrutura:
            matches = re.finditer(padrao, texto, re.IGNORECASE | re.DOTALL)
            for match in matches:
                trecho = match.group()
                resultado_trecho = self._analisar_por_padroes(trecho)
                if resultado_trecho and resultado_trecho.confianca > 0.5:
                    scores.append(resultado_trecho)
                    evidencias.append(f"Estrutura: {trecho[:100]}...")
        
        if not scores:
            return None
        
        # Usar o resultado com maior confiança
        melhor_resultado = max(scores, key=lambda x: x.confianca)
        melhor_resultado.evidencias = evidencias
        melhor_resultado.metodo_usado = "estrutura_documento"
        
        return melhor_resultado
    
    def _combinar_resultados(self, resultados: List[ResultadoAnalise]) -> ResultadoAnalise:
        """Combina múltiplos resultados de análise"""
        
        if not resultados:
            return ResultadoAnalise(
                resultado_principal="Resultado não identificado",
                confianca=0.0,
                evidencias=[],
                metodo_usado="sem_resultados",
                detalhes={}
            )
        
        if len(resultados) == 1:
            return resultados[0]
        
        # Calcular pesos por método
        pesos_metodo = {
            'padroes_regex': 1.0,
            'direitos_trabalhistas': 0.8,
            'contexto_semantico': 0.9,
            'estrutura_documento': 0.7,
            'inferencia': 0.6,
            'linguagem_juridica': 0.7
        }
        
        # Calcular scores ponderados
        scores = {
            'FAVORÁVEL AO REQUERENTE': 0.0,
            'DESFAVORÁVEL AO REQUERENTE': 0.0,
            'PARCIALMENTE FAVORÁVEL': 0.0
        }
        
        evidencias_combinadas = []
        metodos_usados = []
        detalhes_combinados = {}
        
        for resultado in resultados:
            peso = pesos_metodo.get(resultado.metodo_usado, 0.5)
            score_ponderado = resultado.confianca * peso
            
            if resultado.resultado_principal in scores:
                scores[resultado.resultado_principal] += score_ponderado
            
            evidencias_combinadas.extend(resultado.evidencias)
            metodos_usados.append(resultado.metodo_usado)
            detalhes_combinados[resultado.metodo_usado] = resultado.detalhes
        
        # Determinar resultado final
        resultado_final = max(scores.keys(), key=lambda k: scores[k])
        confianca_final = min(scores[resultado_final], 1.0)
        
        return ResultadoAnalise(
            resultado_principal=resultado_final,
            confianca=confianca_final,
            evidencias=evidencias_combinadas,
            metodo_usado=f"combinado_{'+'.join(metodos_usados)}",
            detalhes={
                'scores': scores,
                'metodos_detalhes': detalhes_combinados
            }
        ) 