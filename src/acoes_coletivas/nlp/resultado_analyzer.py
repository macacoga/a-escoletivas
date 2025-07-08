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
        self.padroes_acordo = self._criar_padroes_acordo()
        self.padroes_extinto_com_merito = self._criar_padroes_extinto_com_merito()
        self.padroes_extinto_sem_merito = self._criar_padroes_extinto_sem_merito()

    def _criar_padroes_favoravel(self) -> List[Dict[str, Any]]:
        """Cria padrões expandidos e mais robustos para decisões favoráveis."""
        return [
            # --- Padrões de Resultado Direto (Verbos de Julgamento) ---
            # Prioridade alta para termos que indicam decisão final e positiva
            {
                "pattern": r"\b(julgo|decido)\s+(?:totalmente\s+)?procedente\b",
                "weight": 0.98,
                "tipo": "julgamento_procedente_direto",
            },
            {
                "pattern": r"\b(homologo|homologar|homologada)\b",
                "weight": 0.95,
                "tipo": "homologacao_favoravel",
            },  # Acordo ou decisão favorável
            # --- Padrões Básicos de Concessão/Deferimento/Acolhimento ---
            {
                "pattern": r"\b(concedo|conceder|concedido|concedida|concessão)\b",
                "weight": 0.9,
                "tipo": "concessao",
            },
            {
                "pattern": r"\b(defiro|deferir|deferimento|deferido|deferida)\b",
                "weight": 0.9,
                "tipo": "deferimento",
            },
            {
                "pattern": r"\b(acolho|acolher|acolhido|acolhida|acolhimento)\b",
                "weight": 0.9,
                "tipo": "acolhimento",
            },
            {
                "pattern": r"\b(reconheço|reconhecer|reconhecido|reconhecida|reconhecimento)\b",
                "weight": 0.88,
                "tipo": "reconhecimento",
            },
            {
                "pattern": r"\b(confirmo|confirmar|confirmado|confirmada|confirmação)\b",
                "weight": 0.85,
                "tipo": "confirmacao_favoravel",
            },  # Confirmar uma decisão favorável anterior
            # --- Padrões de Condenação/Obrigação de Pagamento ---
            {
                "pattern": r"\b(condeno|condenar|condenado|condenada|condenação)\b",
                "weight": 0.95,
                "tipo": "condenacao_direta",
            },
            {
                "pattern": r"(?:condeno|condenar|condenado|condenada)\s+(?:o|a)?\s*(?:reclamad[ao]|ré[u]?|empresa|empregador|parte)\s*(?:ao\s+pagamento|a\s+pagar|a\s+indenizar)\b",
                "weight": 0.98,
                "tipo": "condenacao_especifica",
            },
            {
                "pattern": r"\b(arbitro|arbitrar|arbitrado|arbitrada)\b",
                "weight": 0.85,
                "tipo": "arbitramento",
            },  # Valor arbitrado judicialmente
            {
                "pattern": r"\b(determino|determinar|determinada|determinado)\s+(?:o\s+pagamento|a\s+reintegração|a\s+\w+ação)\b",
                "weight": 0.85,
                "tipo": "determinacao_positiva",
            },  # Determina uma ação positiva
            # --- Padrões de Recurso (Provimento) ---
            {
                "pattern": r"\b(recurso\s+provido|recurso\s+parcialmente\s+provido)\b",
                "weight": 0.95,
                "tipo": "recurso_provido_direto",
            },
            {
                "pattern": r"\b(dar\s+provimento|dando\s+provimento|dou\s+provimento|dá\s+provimento)\b",
                "weight": 0.9,
                "tipo": "dar_provimento_ao_recurso",
            },
            {
                "pattern": r"\b(provimento\s+ao\s+recurso)\b",
                "weight": 0.9,
                "tipo": "provimento_ao_recurso_frase",
            },
            {
                "pattern": r"\b(reformo|reformar|reformada|reformado)\s+(?:a\s+sentença|o\s+acórdão)\b",
                "weight": 0.9,
                "tipo": "reforma_favoravel",
            },  # Reforma para tornar favorável
            # --- Padrões de Direito Reconhecido ---
            {
                "pattern": r"\b(faz\s+jus|fazendo\s+jus)\b",
                "weight": 0.85,
                "tipo": "faz_jus",
            },
            {
                "pattern": r"\b(tem\s+direito|tendo\s+direito)\b",
                "weight": 0.85,
                "tipo": "tem_direito",
            },
            {
                "pattern": r"\b(é\s+devido|são\s+devidos|devida|devido)\b",
                "weight": 0.85,
                "tipo": "e_devido",
            },
            {
                "pattern": r"\b(deve\s+ser\s+pago|devem\s+ser\s+pagos|deve\s+pagar)\b",
                "weight": 0.85,
                "tipo": "deve_ser_pago",
            },
            {
                "pattern": r"\b(cabe\s+ao\s+(?:reclamante|autor|empregado))\b",
                "weight": 0.8,
                "tipo": "cabe_ao_requerente",
            },
            # --- Padrões de Êxito / Vitória ---
            {
                "pattern": r"\b(vitória|êxito|procede)\b",
                "weight": 0.75,
                "tipo": "vitoria_geral",
            },  # "procede" sozinho pode ser ambíguo, mas em contexto tende a ser positivo
            {
                "pattern": r"em\s+favor\s+d(?:o|a)\s+(?:reclamante|autor|empregado|parte)\b",
                "weight": 0.8,
                "tipo": "em_favor_do_requerente",
            },
            {
                "pattern": r"\b(razão\s+à?s?\s+(?:reclamante|autor|parte))\b",
                "weight": 0.8,
                "tipo": "razao_ao_requerente",
            },  # Ter razão
            # --- Padrões de Valores Monetários (indicam condenação) ---
            # Estes padrões são mais fracos porque apenas a presença de um valor não garante o deferimento do pedido específico
            # A menos que estejam próximos de um verbo de condenação.
            {
                "pattern": r"(?:pagar|pagamento|condeno|condenação)\s+R\$\s*(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)",
                "weight": 0.7,
                "tipo": "pagamento_com_valor",
            },
            {
                "pattern": r"(?:indenização|indenizar)\s+de\s+R\$\s*(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)",
                "weight": 0.7,
                "tipo": "indenizacao_com_valor",
            },
            {
                "pattern": r"no\s+valor\s+de\s+R\$\s*(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)",
                "weight": 0.6,
                "tipo": "valor_monetario_especifico",
            },
            # --- Padrões Específicos de Direitos Trabalhistas (com indicação de deferimento) ---
            # Idealmente, o sistema identificaria o direito e, em seguida, os padrões de decisão.
            # Estes são "atalhos" que já combinam os dois.
            {
                "pattern": r"\b(horas\s+extras)\s+(?:devidas|deferidas|concedidas)\b",
                "weight": 0.8,
                "tipo": "horas_extras_deferidas",
            },
            {
                "pattern": r"\b(adicional\s+(?:noturno|de\s+insalubridade|de\s+periculosidade))\s+(?:devido|deferido|concedido)\b",
                "weight": 0.8,
                "tipo": "adicional_deferido",
            },
            {
                "pattern": r"\b(verbas\s+rescisórias)\s+(?:devidas|deferidas|concedidas)\b",
                "weight": 0.8,
                "tipo": "verbas_rescisorias_deferidas",
            },
            {
                "pattern": r"\b(aviso\s+prévio)\s+(?:devido|deferido|concedido)\b",
                "weight": 0.75,
                "tipo": "aviso_previo_deferido",
            },
            {
                "pattern": r"\b(décimo\s+terceiro|13[º°]\s+salário)\s+(?:devido|deferido|concedido)\b",
                "weight": 0.75,
                "tipo": "decimo_terceiro_deferido",
            },
            {
                "pattern": r"\b(férias)\s+(?:devidas|deferidas|concedidas)\b",
                "weight": 0.75,
                "tipo": "ferias_deferidas",
            },
            {
                "pattern": r"\b(FGTS)\s+(?:devido|deferido|concedido|liberado)\b",
                "weight": 0.75,
                "tipo": "fgts_deferido",
            },
            {
                "pattern": r"\b(vínculo\s+empregatício)\s+(?:reconhecido|declarado)\b",
                "weight": 0.85,
                "tipo": "vinculo_empregaticio_reconhecido",
            },
            {
                "pattern": r"\b(reintegração)\s+(?:deferida|determinada|ordenada)\b",
                "weight": 0.85,
                "tipo": "reintegracao_deferida",
            },
            {
                "pattern": r"\b(rescisão\s+indireta)\s+(?:reconhecida|declarada)\b",
                "weight": 0.85,
                "tipo": "rescisao_indireta_reconhecida",
            },
        ]

    def _criar_padroes_desfavoravel(self) -> List[Dict[str, Any]]:
        """Cria padrões expandidos para decisões desfavoráveis"""
        return [
            # Padrões básicos
            {
                "pattern": r"\b(improcedente|improcedência)\b",
                "weight": 0.9,
                "tipo": "decisao_direta",
            },
            {
                "pattern": r"\b(nego|negar|negado|negada)\b",
                "weight": 0.8,
                "tipo": "negacao",
            },
            {
                "pattern": r"\b(indefiro|indeferimento|indeferido|indeferida)\b",
                "weight": 0.8,
                "tipo": "indeferimento",
            },
            {
                "pattern": r"\b(rejeito|rejeição|rejeitado|rejeitada)\b",
                "weight": 0.8,
                "tipo": "rejeicao",
            },
            {
                "pattern": r"\b(desconheço|desconhecimento)\b",
                "weight": 0.7,
                "tipo": "desconhecimento",
            },
            # Padrões contextuais
            {
                "pattern": r"julgo\s+improcedente",
                "weight": 0.95,
                "tipo": "julgamento_improcedente",
            },
            {
                "pattern": r"sentença\s+improcedente",
                "weight": 0.9,
                "tipo": "sentenca_improcedente",
            },
            {
                "pattern": r"ação\s+improcedente",
                "weight": 0.9,
                "tipo": "acao_improcedente",
            },
            {
                "pattern": r"pedido\s+improcedente",
                "weight": 0.85,
                "tipo": "pedido_improcedente",
            },
            {
                "pattern": r"recurso\s+desprovido",
                "weight": 0.8,
                "tipo": "recurso_desprovido",
            },
            {
                "pattern": r"negar\s+provimento",
                "weight": 0.8,
                "tipo": "negar_provimento",
            },
            {"pattern": r"nego\s+provimento", "weight": 0.8, "tipo": "nego_provimento"},
            {"pattern": r"nego\s+seguimento", "weight": 0.8, "tipo": "nego_seguimento"},
            {
                "pattern": r"denego\s+seguimento",
                "weight": 0.8,
                "tipo": "denego_seguimento",
            },
            {"pattern": r"nega\s+provimento", "weight": 0.8, "tipo": "nega_provimento"},
            {
                "pattern": r"desprovimento\s+do\s+recurso",
                "weight": 0.8,
                "tipo": "desprovimento_recurso",
            },
            {
                "pattern": r"rejeitado\s+o\s+recurso",
                "weight": 0.8,
                "tipo": "rejeitado_recurso",
            },
            {
                "pattern": r"rejeitado\s+o\s+pedido",
                "weight": 0.8,
                "tipo": "rejeitado_pedido",
            },
            {
                "pattern": r"rejeitado\s+o\s+recurso",
                "weight": 0.8,
                "tipo": "rejeitado_recurso",
            },
            # Padrões de não direito
            {
                "pattern": r"não\s+tem\s+direito",
                "weight": 0.8,
                "tipo": "nao_tem_direito",
            },
            {"pattern": r"não\s+faz\s+jus", "weight": 0.8, "tipo": "nao_faz_jus"},
            {"pattern": r"não\s+é\s+devido", "weight": 0.8, "tipo": "nao_e_devido"},
            {
                "pattern": r"ausência\s+de\s+direito",
                "weight": 0.7,
                "tipo": "ausencia_direito",
            },
            {
                "pattern": r"não\s+deve\s+ser\s+pago",
                "weight": 0.7,
                "tipo": "nao_deve_pago",
            },
            {"pattern": r"não\s+procede", "weight": 0.7, "tipo": "nao_procede"},
            # Padrões de extinção
            {
                "pattern": r"extingo\s+o\s+processo",
                "weight": 0.7,
                "tipo": "extincao_processo",
            },
            {
                "pattern": r"extingo\s+a\s+execução",
                "weight": 0.6,
                "tipo": "extincao_execucao",
            },
            {
                "pattern": r"processo\s+extinto",
                "weight": 0.6,
                "tipo": "processo_extinto",
            },
            # Padrões de perda/derrota
            {
                "pattern": r"\b(perdeu|perderam|derrota|insucesso)\b",
                "weight": 0.6,
                "tipo": "derrota",
            },
            {
                "pattern": r"em\s+favor\s+do\s+requerido",
                "weight": 0.7,
                "tipo": "favor_requerido",
            },
            {"pattern": r"em\s+favor\s+do\s+réu", "weight": 0.7, "tipo": "favor_reu"},
            {
                "pattern": r"razão\s+ao\s+requerido",
                "weight": 0.7,
                "tipo": "razao_requerido",
            },
            {"pattern": r"razão\s+ao\s+réu", "weight": 0.7, "tipo": "razao_reu"},
            # Padrões de absolvição
            {
                "pattern": r"\b(absolvo|absolvição|absolvido|absolvida)\b",
                "weight": 0.8,
                "tipo": "absolvicao",
            },
            {
                "pattern": r"isento\s+de\s+pagamento",
                "weight": 0.7,
                "tipo": "isento_pagamento",
            },
            {"pattern": r"sem\s+condenação", "weight": 0.7, "tipo": "sem_condenacao"},
            # Padrões de falta de prova
            {"pattern": r"falta\s+de\s+prova", "weight": 0.6, "tipo": "falta_prova"},
            {"pattern": r"não\s+comprovado", "weight": 0.6, "tipo": "nao_comprovado"},
            {
                "pattern": r"prova\s+insuficiente",
                "weight": 0.6,
                "tipo": "prova_insuficiente",
            },
            {"pattern": r"não\s+demonstrado", "weight": 0.6, "tipo": "nao_demonstrado"},
            # Padrões de arquivamento
            {
                "pattern": r"\b(arquivo|arquivado|arquivamento)\b",
                "weight": 0.6,
                "tipo": "arquivamento",
            },
            {"pattern": r"baixa\s+dos\s+autos", "weight": 0.5, "tipo": "baixa_autos"},
        ]

    def _criar_padroes_parcial(self) -> List[Dict[str, Any]]:
        """Cria padrões expandidos e mais robustos para decisões parciais."""
        return [
            # --- Padrões de Resultado Direto (Fortes indicadores de parcialidade) ---
            # Prioridade alta para as formas mais explícitas
            {
                "pattern": r"\b(?:julgo|decido)\s+(?:os\s+pedidos\s+)?parcialmente\s+procedente(?:s)?\b",
                "weight": 0.98,
                "tipo": "julgamento_parcial_direto",
            },
            {
                "pattern": r"\bprocedente(?:s)?\s+em\s+parte\b",
                "weight": 0.95,
                "tipo": "procedente_em_parte_direto",
            },
            {
                "pattern": r"\b(acolho|defiro|concedo)\s+(?:os\s+pedidos\s+)?parcialmente\b",
                "weight": 0.95,
                "tipo": "acolhimento_parcial_direto",
            },
            {
                "pattern": r"\b(dou|dá|dando|dar)\s+parcial\s+provimento\b",
                "weight": 0.95,
                "tipo": "dar_parcial_provimento_direto",
            },
            {
                "pattern": r"\b(recurso\s+parcialmente\s+provido)\b",
                "weight": 0.95,
                "tipo": "recurso_parcialmente_provido_direto",
            },
            {
                "pattern": r"\b(reformo|reformar|reformada|reformado)\s+(?:parcialmente)\s+(?:a\s+sentença|o\s+acórdão)\b",
                "weight": 0.93,
                "tipo": "reforma_parcial",
            },
            # --- Padrões Básicos de Expressão de Parcialidade ---
            # Termos que diretamente indicam "parte"
            {
                "pattern": r"\b(?:parcialmente|em\s+parte)\b",
                "weight": 0.9,
                "tipo": "indicador_parcialidade_geral",
            },
            {
                "pattern": r"\b(parte\s+do\s+pedido|parte\s+dos\s+pedidos|parte\s+da\s+pretensão)\b",
                "weight": 0.88,
                "tipo": "parte_do_pedido",
            },
            {
                "pattern": r"\b(acolho|defiro|concedo)\s+em\s+parte\b",
                "weight": 0.88,
                "tipo": "acolhimento_em_parte",
            },  # "Acolho em parte o recurso"
            # --- Padrões de Divisão/Exclusão Implícita ---
            # Indicam que nem tudo foi concedido
            {
                "pattern": r"(?:apenas|somente|tão\s+somente)\s+o\s+pedido\s+de\s+(?:.*?\s+)?(?:devido|procedente)\b",
                "weight": 0.8,
                "tipo": "apenas_pedido_especifico_procedente",
            },
            {
                "pattern": r"(?:concedo|defiro|acolho)\s+(?:somente|apenas)\s+o\s+pedido\s+de\s+.*\b",
                "weight": 0.8,
                "tipo": "concedido_somente_um_pedido",
            },
            {
                "pattern": r"\b(alguns\s+pedidos?)\s+(?:foram\s+acolhidos|procedem|deferidos)\b",
                "weight": 0.75,
                "tipo": "alguns_pedidos_acolhidos",
            },
            {
                "pattern": r"\b(parte\s+dos\s+direitos)\s+(?:reconhecidos|deferidos)\b",
                "weight": 0.75,
                "tipo": "parte_dos_direitos_reconhecidos",
            },
            {
                "pattern": r"(?:rejeitados|indeferidos)\s+os\s+demais\s+pedidos?\b",
                "weight": 0.7,
                "tipo": "rejeitado_o_restante",
            },  # Indica parcialidade ao rejeitar o que não foi listado
            {
                "pattern": r"(?:não\s+procede|improcedente)\s+o\s+pedido\s+de\s+.*\s+(?:mas|porém|contudo)\s+procede\s+o\s+de\s+.*\b",
                "weight": 0.85,
                "tipo": "contraste_pedidos",
            },  # "Não procede o pedido A, mas procede o B"
            # --- Padrões de Limitação / Restrição ---
            # Indicam que o que foi concedido tem um limite
            {
                "pattern": r"\b(limitado\s+(?:a|ao|à|aos|às))\b",
                "weight": 0.7,
                "tipo": "limitado_a",
            },
            {
                "pattern": r"\b(restrito\s+(?:a|ao|à|aos|às))\b",
                "weight": 0.7,
                "tipo": "restrito_a",
            },
            {
                "pattern": r"\b(no\s+que\s+se\s+refere\s+a)\b",
                "weight": 0.65,
                "tipo": "no_que_se_refere_a",
            },  # Contextualiza a abrangência
            # --- Padrões de Exclusão (que sugerem parcialidade pelo que não foi incluído) ---
            {
                "pattern": r"\b(excluído|excluímos|excluir)\s+(?:o\s+pedido\s+de|da\s+condenação)\b",
                "weight": 0.7,
                "tipo": "exclusao_de_pedido",
            },
            {
                "pattern": r"\b(afasto|afastado|afastar)\s+(?:a\s+condenação\s+em|o\s+pedido\s+de)\b",
                "weight": 0.7,
                "tipo": "afastamento_de_condenacao",
            },
            {
                "pattern": r"\b(apenas\s+no\s+tocante\s+a|somente\s+no\s+tocante\s+a)\b",
                "weight": 0.7,
                "tipo": "apenas_no_tocante_a",
            },  # Restringe a aplicação
        ]

    def _criar_padroes_acordo(self) -> List[Dict[str, Any]]:
        """
        Cria padrões para identificar decisões que homologam acordos.
        Geralmente, um acordo é um desfecho consensual do processo.
        """
        return [
            # Padrões diretos de homologação de acordo
            {
                "pattern": r"\b(homologo|homologar|homologado|homologada)\s+(?:o\s+)?(acordo|conciliação|transação)\b",
                "weight": 1.0,
                "tipo": "acordo_homologado_direto",
            },
            {
                "pattern": r"\b(acordo|conciliação|transação)\s+(?:celebrado|firmado|obtido|realizado)\b",
                "weight": 0.95,
                "tipo": "acordo_celebrado_confirmado",
            },
            {
                "pattern": r"\bpartes\s+(?:transigiram|celebraram\s+acordo|conciliaram)\b",
                "weight": 0.9,
                "tipo": "partes_conciliaram",
            },
            # Padrões que indicam extinção pelo acordo
            {
                "pattern": r"\b(extinção\s+do\s+processo)\s+em\s+razão\s+do\s+(?:acordo|conciliação)\b",
                "weight": 0.95,
                "tipo": "extincao_por_acordo",
            },
            {
                "pattern": r"\b(resolução\s+do\s+mérito)\s+pelo\s+(?:acordo|conciliação)\b",
                "weight": 0.9,
                "tipo": "resolucao_merito_por_acordo",
            },
            # Termos que indicam a aceitação do acordo
            {
                "pattern": r"\b(julgo|decido)\s+(?:extinto|resolvido)\s+o\s+processo\s+com\s+resolução\s+do\s+mérito\s+em\s+razão\s+do\s+acordo\b",
                "weight": 0.98,
                "tipo": "julgamento_extincao_acordo",
            },
        ]

    def _criar_padroes_extinto_com_merito(self) -> List[Dict[str, Any]]:
        """
        Cria padrões para identificar decisões que extinguem o processo
        com resolução do mérito (o direito em si é analisado e negado,
        geralmente por prescrição ou decadência).
        """
        return [
            # Padrões diretos de extinção com mérito
            {
                "pattern": r"\b(extingo|extinta|extinto)\s+(?:o\s+processo|o\s+feito)\s+com\s+resolução\s+do\s+mérito\b",
                "weight": 1.0,
                "tipo": "extincao_com_merito_direta",
            },
            {
                "pattern": r"\b(resolução\s+do\s+mérito)\b",
                "weight": 0.9,
                "tipo": "resolucao_merito_geral",
            },
            # Padrões relacionados a prescrição e decadência (principais causas de extinção com mérito)
            {
                "pattern": r"\b(pronuncio|pronunciada|pronunciado)\s+a\s+(?:prescrição|decadência)\b",
                "weight": 0.98,
                "tipo": "declaracao_prescricao_decadencia",
            },
            {
                "pattern": r"\b(declaro|declarada|declarado)\s+a\s+(?:prescrição|decadência)\b",
                "weight": 0.98,
                "tipo": "declaracao_prescricao_decadencia",
            },
            {
                "pattern": r"\b(prescrição|decadência)\s+(?:reconhecida|declarada|configurada|acolhida)\b",
                "weight": 0.95,
                "tipo": "prescricao_decadencia_reconhecida",
            },
            {
                "pattern": r"\b(julgo|decido)\s+(?:o\s+processo|o\s+feito)\s+(?:extinto)\s+pela\s+(?:prescrição|decadência)\b",
                "weight": 0.98,
                "tipo": "julgamento_extinto_por_prescricao",
            },
            # Padrões que indicam perda do direito de ação
            {
                "pattern": r"\b(perda\s+do\s+direito\s+de\s+ação)\b",
                "weight": 0.85,
                "tipo": "perda_direito_acao",
            },
            {
                "pattern": r"\b(extinção\s+da\s+pretensão)\b",
                "weight": 0.85,
                "tipo": "extincao_pretensao",
            },
        ]

    def _criar_padroes_extinto_sem_merito(self) -> List[Dict[str, Any]]:
        """
        Cria padrões para identificar decisões que extinguem o processo
        sem resolução do mérito (por questões processuais, sem analisar o direito em si).
        """
        return [
            # Padrões diretos de extinção sem mérito
            {
                "pattern": r"\b(extingo|extinta|extinto)\s+(?:o\s+processo|o\s+feito)\s+sem\s+resolução\s+do\s+mérito\b",
                "weight": 1.0,
                "tipo": "extincao_sem_merito_direta",
            },
            # Padrões relacionados a vícios processuais
            {
                "pattern": r"\b(ausência\s+de\s+pressuposto\s+processual)\b",
                "weight": 0.95,
                "tipo": "ausencia_pressuposto",
            },
            {
                "pattern": r"\b(carência\s+da\s+ação)\b",
                "weight": 0.95,
                "tipo": "carencia_acao",
            },
            {
                "pattern": r"\b(ilegitimidade\s+de\s+(?:parte|polo))\b",
                "weight": 0.95,
                "tipo": "ilegitimidade_parte",
            },
            {
                "pattern": r"\b(falta\s+de\s+interesse\s+de\s+agir)\b",
                "weight": 0.95,
                "tipo": "falta_interesse_agir",
            },
            {
                "pattern": r"\b(inépcia\s+da\s+inicial)\b",
                "weight": 0.95,
                "tipo": "inepcia_inicial",
            },
            {
                "pattern": r"\b(coisa\s+julgada|litispendência|conexão)\b",
                "weight": 0.9,
                "tipo": "pressuposto_negativo",
            },  # Condições da ação que impedem o prosseguimento
            # Padrões que indicam não conhecimento do recurso (similar a extinção sem mérito no recurso)
            {
                "pattern": r"\b(não\s+conheço|não\s+conhecido)\s+(?:do|do\s+recurso|do\s+apelo)\b",
                "weight": 0.9,
                "tipo": "nao_conhecimento_recurso",
            },
            {
                "pattern": r"\b(intempestividade)\s+(?:do\s+recurso)?\b",
                "weight": 0.85,
                "tipo": "intempestividade_recurso",
            },  # Causa comum de não conhecimento
            # Padrões que indicam arquivamento ou não processamento
            {
                "pattern": r"\b(arquivamento|arquivado|arquivada)\b",
                "weight": 0.8,
                "tipo": "arquivamento_processo",
            },
            {
                "pattern": r"\b(indeferimento\s+da\s+petição\s+inicial)\b",
                "weight": 0.9,
                "tipo": "indeferimento_inicial",
            },
        ]

    def _criar_padroes_contexto(self) -> List[Dict[str, Any]]:
        """Cria padrões expandidos e mais robustos para identificar o contexto da decisão."""
        return [
            # --- Identificadores de Seção Dispositiva / Conclusão Principal ---
            # Termos que introduzem diretamente o dispositivo ou a conclusão final
            {
                "pattern": r"\b(dispositivo|dispositiva|decisão|conclusão|decisório)\b",
                "weight": 1.0,
                "tipo": "secao_dispositiva",
            },
            {
                "pattern": r"\b(isto\s+posto|diante\s+do\s+exposto|pelo\s+exposto|ante\s+o\s+exposto|por\s+todo\s+o\s+exposto|em\s+face\s+do\s+exposto)\b",
                "weight": 0.95,
                "tipo": "conclusao_formal",
            },
            {
                "pattern": r"\b(assim\s+sendo|dessa\s+forma|portanto|em\s+consequência)\b",
                "weight": 0.85,
                "tipo": "conclusao_inferencial",
            },
            {
                "pattern": r"\b(com\s+efeito|nesse\s+sentido)\b",
                "weight": 0.7,
                "tipo": "introducao_argumento",
            },  # Pode preceder a conclusão, bom para contextualizar
            {
                "pattern": r"\b(em\s+face\s+de\s+todo\s+o\s+conjunto\s+probatório)\b",
                "weight": 0.75,
                "tipo": "sinalizador_resultado_prova",
            },  # Liga a prova ao resultado
            # --- Identificadores de Verbos de Decisão ---
            # Verbos que expressam o ato de julgar ou decidir
            {
                "pattern": r"\b(decido|decide|decidimos|decidir)\b",
                "weight": 0.9,
                "tipo": "decisao_verbo",
            },
            {
                "pattern": r"\b(julgo|julga|julgamos|julgar)\b",
                "weight": 0.95,
                "tipo": "julgamento_verbo",
            },
            {
                "pattern": r"\b(sentencio|sentencia|sentenciamos|sentenciar)\b",
                "weight": 0.9,
                "tipo": "sentenciamento_verbo",
            },
            {
                "pattern": r"\b(determino|determina|determinamos|determinar)\b",
                "weight": 0.85,
                "tipo": "determinacao_verbo",
            },
            {
                "pattern": r"\b(ordeno|ordena|ordenamos|ordenar)\b",
                "weight": 0.85,
                "tipo": "ordem_verbo",
            },
            {
                "pattern": r"\b(homologo|homologa|homologamos|homologar)\b",
                "weight": 0.9,
                "tipo": "homologacao_verbo",
            },  # Comum em acordos
            # --- Identificadores de Mérito e Fundamentação ---
            # Termos que sinalizam a análise do caso em si, e não apenas o relatório ou formalidades
            {
                "pattern": r"\b(no\s+mérito|quanto\s+ao\s+mérito|em\s+relação\s+ao\s+mérito)\b",
                "weight": 0.9,
                "tipo": "merito_direto",
            },
            {
                "pattern": r"\b(análise\s+do\s+mérito|exame\s+do\s+mérito|discussão\s+do\s+mérito)\b",
                "weight": 0.85,
                "tipo": "analise_exame_merito",
            },
            {
                "pattern": r"\b(fundamentação|fundamentando|fundamento)\b",
                "weight": 0.8,
                "tipo": "secao_fundamentacao",
            },
            {
                "pattern": r"\b(voto|votando)\b",
                "weight": 0.8,
                "tipo": "secao_voto",
            },  # Comum em acórdãos para fundamentação do relator
            {
                "pattern": r"\b(passo\s+a\s+analisar|passamos\s+a\s+analisar)\b",
                "weight": 0.75,
                "tipo": "introducao_analise",
            },  # Sinaliza o início da análise do mérito
            {
                "pattern": r"\b(da\s+análise\s+dos\s+autos|da\s+instrução\s+processual)\b",
                "weight": 0.7,
                "tipo": "inicio_analise_fatos",
            },  # Conecta os fatos à fundamentação
        ]

    def _criar_padroes_inferencia(self) -> List[Dict[str, Any]]:
        """Cria padrões expandidos e mais robustos para inferir o resultado quando não há palavras-chave diretas."""
        return [
            # --- Padrões de Concessão de Direitos / Pagamento (Geralmente Favorável) ---
            # Indicam que algo será pago ou concedido.
            {
                "pattern": r"\b(pagamento|pagar)\s+(?:de|referente\s+a|o\s+valor\s+de)?\s*(?:R\$\s*|quantia\s+de\s*R\$\s*|o\s+importe\s+de\s*R\$\s*)?\d{1,3}(?:\.?\d{3})*(?:,\d{2})?",
                "weight": 0.7,
                "tipo": "pagamento_com_valor_implied",
                "resultado": "favoravel",
            },
            {
                "pattern": r"\b(indenização|indenizar)\s+(?:por|a\s+título\s+de)?\s+danos?\s+(?:morais?|materiais?)\b",
                "weight": 0.8,
                "tipo": "indenizacao_explicit",
                "resultado": "favoravel",
            },
            {
                "pattern": r"\b(valor|montante|importe|quantia)\s+(?:de|referente\s+a)?\s*(?:R\$\s*)?\d{1,3}(?:\.?\d{3})*(?:,\d{2})?\s+(?:devido|a\s+ser\s+pago|condenado)\b",
                "weight": 0.85,
                "tipo": "valor_devido_condenado",
                "resultado": "favoravel",
            },
            {
                "pattern": r"\b(receber|recebimento)\s+de\s+(?:valores|verbas)\b",
                "weight": 0.65,
                "tipo": "recebimento_verbas_implied",
                "resultado": "favoravel",
            },
            {
                "pattern": r"\b(liberação|liberado)\s+(?:do\s+)?(FGTS|guia)\b",
                "weight": 0.75,
                "tipo": "liberacao_fgts",
                "resultado": "favoravel",
            },
            {
                "pattern": r"\b(reintegrar|reintegração)\b",
                "weight": 0.8,
                "tipo": "reintegracao_implied",
                "resultado": "favoravel",
            },  # Forte indício de procedência do pedido de reintegração
            # --- Padrões de Não Concessão / Ausência de Direito (Geralmente Desfavorável) ---
            # Indicam que o pedido não será atendido.
            {
                "pattern": r"\bnão\s+há\s+que\s+se\s+falar\s+em\b",
                "weight": 0.9,
                "tipo": "nao_ha_falar_explicit",
                "resultado": "desfavoravel",
            },
            {
                "pattern": r"\b(não\s+se\s+vislumbra|não\s+se\s+verifica|não\s+restou\s+comprovado|ausência\s+de\s+prova)\b",
                "weight": 0.85,
                "tipo": "falta_prova_vislumbre",
                "resultado": "desfavoravel",
            },
            {
                "pattern": r"\b(incabível|descabido|improcedente)\b",
                "weight": 0.8,
                "tipo": "incabivel_descabido",
                "resultado": "desfavoravel",
            },  # Mesmo sem "julgo" antes, é forte
            {
                "pattern": r"\b(não\s+faz\s+jus|não\s+tem\s+direito|não\s+é\s+devido|não\s+cabe)\b",
                "weight": 0.9,
                "tipo": "negacao_direito",
                "resultado": "desfavoravel",
            },
            {
                "pattern": r"\b(indeferimento|rejeição)\s+(?:do|da|dos|das)?\s+(?:pedido|pretensão)\b",
                "weight": 0.85,
                "tipo": "indeferimento_rejeicao_nominal",
                "resultado": "desfavoravel",
            },
            {
                "pattern": r"\b(ônus\s+da\s+prova\s+não\s+foi\s+desincumbido)\b",
                "weight": 0.85,
                "tipo": "onus_prova_nao_desincumbido",
                "resultado": "desfavoravel",
            },  # Forte para improcedência
            {
                "pattern": r"\b(improvido|improvida)\b",
                "weight": 0.7,
                "tipo": "improvido_geral",
                "resultado": "desfavoravel",
            },  # Improvido o pedido/recurso
            # --- Padrões de Determinação / Obrigação de Fazer (Geralmente Favorável) ---
            # Indicam que uma ação não monetária deve ser realizada.
            {
                "pattern": r"\b(cumprir|cumprimento)\s+(?:com\s+a|de\s+sua)?\s*obrigação\b",
                "weight": 0.7,
                "tipo": "cumprir_obrigacao_explicit",
                "resultado": "favoravel",
            },
            {
                "pattern": r"\b(obrigação\s+de\s+fazer|obrigação\s+de\s+pagar|obrigação\s+de\s+entregar)\b",
                "weight": 0.75,
                "tipo": "obrigacao_de_acao",
                "resultado": "favoravel",
            },
            {
                "pattern": r"\b(anotação|retificação)\s+(?:na\s+)?CTPS\b",
                "weight": 0.7,
                "tipo": "ctps_anotacao_retificacao",
                "resultado": "favoravel",
            },
            {
                "pattern": r"\b(registro|averbação)\s+em\s+(?:carteira|CTPS)\b",
                "weight": 0.7,
                "tipo": "registro_carteira_explicit",
                "resultado": "favoravel",
            },
            {
                "pattern": r"\b(expedição|emitir|fornecer)\s+(?:de\s+)?(guias?|alvará|certidão)\b",
                "weight": 0.75,
                "tipo": "expedicao_documentos",
                "resultado": "favoravel",
            },  # Guias para saque, alvará para FGTS
            # --- Padrões de Extinção / Perda do Direito (Pode ser Desfavorável ou Neutro, dependendo do contexto) ---
            # Estes padrões indicam encerramento do processo por motivos específicos.
            {
                "pattern": r"\b(extinção|extinto|extinta)\s+(?:do\s+processo|do\s+feito|da\s+pretensão)\b",
                "weight": 0.8,
                "tipo": "extincao_processo",
                "resultado": "extinto",
            },
            {
                "pattern": r"\b(prescrição|prescrita|prescrito)\b",
                "weight": 0.85,
                "tipo": "prescricao_declarada",
                "resultado": "extinto_merito",
            },
            {
                "pattern": r"\b(decadência|decaído|decaída)\b",
                "weight": 0.85,
                "tipo": "decadencia_declarada",
                "resultado": "extinto_merito",
            },
            {
                "pattern": r"\b(carência\s+da\s+ação|ilegitimidade\s+de\s+parte|falta\s+de\s+interesse\s+de\s+agir)\b",
                "weight": 0.8,
                "tipo": "extincao_sem_merito_motivo",
                "resultado": "extinto_sem_merito",
            },
            # --- Padrões de Acordo/Transação (Neutro no resultado do litígio, mas resolutivo) ---
            # Indicam que as partes chegaram a um consenso.
            {
                "pattern": r"\b(acordo|conciliação|transação)\s+(?:homologado|celebrado|firmado|obtido)\b",
                "weight": 0.9,
                "tipo": "acordo_homologado",
                "resultado": "acordo",
            },
        ]

    def analisar_resultado(
        self, texto: str, direitos_trabalhistas: Optional[str] = None
    ) -> ResultadoAnalise:
        """Analisa o resultado de uma decisão judicial com algoritmo melhorado"""

        if not texto or len(texto.strip()) < 10:
            return ResultadoAnalise(
                resultado_principal="Resultado não identificado",
                confianca=0.0,
                evidencias=["Texto vazio ou muito curto"],
                metodo_usado="texto_insuficiente",
                detalhes={},
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
                detalhes={"tamanho_texto": len(texto)},
            )

    def _analisar_por_inferencia(self, texto: str) -> Optional[ResultadoAnalise]:
        """Analisa usando padrões de inferência"""

        texto_lower = texto.lower()
        evidencias = []
        score_favoravel = 0.0
        score_desfavoravel = 0.0

        for padrao in self.padroes_inferencia:
            matches = re.finditer(padrao["pattern"], texto_lower, re.IGNORECASE)
            for match in matches:
                peso = padrao["weight"]
                resultado_esperado = padrao["resultado"]

                if resultado_esperado == "favoravel":
                    score_favoravel += peso
                elif resultado_esperado == "desfavoravel":
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
                "score_desfavoravel": score_desfavoravel,
            },
        )

    def _analisar_por_linguagem_juridica(
        self, texto: str
    ) -> Optional[ResultadoAnalise]:
        """Analisa usando padrões específicos da linguagem jurídica"""

        texto_lower = texto.lower()
        evidencias = []
        score = 0.0

        # Padrões específicos para documentos jurídicos trabalhistas
        padroes_linguagem = [
            # Conclusões típicas de sentenças favoráveis
            {
                "pattern": r"pelos\s+fundamentos\s+.*\s+procedente",
                "weight": 0.8,
                "resultado": "favoravel",
            },
            {
                "pattern": r"pelas\s+razões\s+.*\s+procedente",
                "weight": 0.8,
                "resultado": "favoravel",
            },
            {
                "pattern": r"face\s+ao\s+conjunto\s+probatório",
                "weight": 0.5,
                "resultado": "favoravel",
            },
            # Conclusões típicas de sentenças desfavoráveis
            {
                "pattern": r"pelos\s+fundamentos\s+.*\s+improcedente",
                "weight": 0.8,
                "resultado": "desfavoravel",
            },
            {
                "pattern": r"pelas\s+razões\s+.*\s+improcedente",
                "weight": 0.8,
                "resultado": "desfavoravel",
            },
            {
                "pattern": r"ausência\s+de\s+elementos\s+probatórios",
                "weight": 0.6,
                "resultado": "desfavoravel",
            },
            # Padrões de fundamentação
            {
                "pattern": r"restou\s+comprovado",
                "weight": 0.6,
                "resultado": "favoravel",
            },
            {
                "pattern": r"não\s+restou\s+comprovado",
                "weight": 0.6,
                "resultado": "desfavoravel",
            },
            {
                "pattern": r"ficou\s+demonstrado",
                "weight": 0.6,
                "resultado": "favoravel",
            },
            {
                "pattern": r"não\s+ficou\s+demonstrado",
                "weight": 0.6,
                "resultado": "desfavoravel",
            },
        ]

        score_favoravel = 0.0
        score_desfavoravel = 0.0

        for padrao in padroes_linguagem:
            matches = re.finditer(padrao["pattern"], texto_lower, re.IGNORECASE)
            for match in matches:
                peso = padrao["weight"]
                resultado_esperado = padrao["resultado"]

                if resultado_esperado == "favoravel":
                    score_favoravel += peso
                elif resultado_esperado == "desfavoravel":
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
                "score_desfavoravel": score_desfavoravel,
            },
        )

    def _analisar_por_padroes(self, texto: str) -> Optional[ResultadoAnalise]:
        """Analisa usando padrões regex expandidos"""

        texto_lower = texto.lower()
        evidencias_favoravel = []
        evidencias_desfavoravel = []
        evidencias_parcial = []
        evidencias_acordo = []
        evidencias_extinto_com_merito = []
        evidencias_extinto_sem_merito = []

        score_favoravel = 0.0
        score_desfavoravel = 0.0
        score_parcial = 0.0
        score_acordo = 0.0
        score_extinto_com_merito = 0.0
        score_extinto_sem_merito = 0.0

        # Verificar padrões favoráveis
        for padrao in self.padroes_favoravel:
            matches = re.finditer(padrao["pattern"], texto_lower, re.IGNORECASE)
            for match in matches:
                score_favoravel += padrao["weight"]
                evidencias_favoravel.append(f"{padrao['tipo']}: '{match.group()}'")

        # Verificar padrões desfavoráveis
        for padrao in self.padroes_desfavoravel:
            matches = re.finditer(padrao["pattern"], texto_lower, re.IGNORECASE)
            for match in matches:
                score_desfavoravel += padrao["weight"]
                evidencias_desfavoravel.append(f"{padrao['tipo']}: '{match.group()}'")

        # Verificar padrões parciais
        for padrao in self.padroes_parcial:
            matches = re.finditer(padrao["pattern"], texto_lower, re.IGNORECASE)
            for match in matches:
                score_parcial += padrao["weight"]
                evidencias_parcial.append(f"{padrao['tipo']}: '{match.group()}'")

        # Verificar padrões de acordo
        for padrao in self.padroes_acordo:
            matches = re.finditer(padrao["pattern"], texto_lower, re.IGNORECASE)
            for match in matches:
                score_acordo += padrao["weight"]
                evidencias_acordo.append(f"{padrao['tipo']}: '{match.group()}'")

        # Verificar padrões de extinção com mérito
        for padrao in self.padroes_extinto_com_merito:
            matches = re.finditer(padrao["pattern"], texto_lower, re.IGNORECASE)
            for match in matches:
                score_extinto_com_merito += padrao["weight"]
                evidencias_extinto_com_merito.append(
                    f"{padrao['tipo']}: '{match.group()}'"
                )

        # Verificar padrões de extinção sem mérito
        for padrao in self.padroes_extinto_sem_merito:
            matches = re.finditer(padrao["pattern"], texto_lower, re.IGNORECASE)
            for match in matches:
                score_extinto_sem_merito += padrao["weight"]
                evidencias_extinto_sem_merito.append(
                    f"{padrao['tipo']}: '{match.group()}'"
                )
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
                "score_parcial": score_parcial,
                "score_acordo": score_acordo,
                "score_extinto_com_merito": score_extinto_com_merito,
                "score_extinto_sem_merito": score_extinto_sem_merito,
            },
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
                    outcome = direito.get("decision_outcome", "")
                    if outcome is None:
                        outcome = ""
                    outcome = outcome.lower()
                    tipo = direito.get("type", direito.get("description", "Direito"))

                    if outcome in ["granted", "concedido", "deferido"]:
                        resultados_direitos.append("favoravel")
                        evidencias.append(f"Direito {tipo}: {outcome}")
                    elif outcome in ["denied", "negado", "indeferido"]:
                        resultados_direitos.append("desfavoravel")
                        evidencias.append(f"Direito {tipo}: {outcome}")
                    elif outcome in ["partially_granted", "parcialmente"]:
                        resultados_direitos.append("parcial")
                        evidencias.append(f"Direito {tipo}: {outcome}")
                    elif outcome in ["extinctive_with_merit", "extinto_com_merito"]:
                        resultados_direitos.append("extinto_com_merito")
                        evidencias.append(f"Direito {tipo}: {outcome}")
                    elif outcome in ["extinctive_without_merit", "extinto_sem_merito"]:
                        resultados_direitos.append("extinto_sem_merito")
                        evidencias.append(f"Direito {tipo}: {outcome}")
                    elif outcome in ["agreement", "acordo"]:
                        resultados_direitos.append("acordo")
                        evidencias.append(f"Direito {tipo}: {outcome}")

            if not resultados_direitos:
                return None

            # Determinar resultado majoritário
            favoravel_count = resultados_direitos.count("favoravel")
            desfavoravel_count = resultados_direitos.count("desfavoravel")
            parcial_count = resultados_direitos.count("parcial")
            acordo_count = resultados_direitos.count("acordo")
            extinto_com_merito_count = resultados_direitos.count("extinto_com_merito")
            extinto_sem_merito_count = resultados_direitos.count("extinto_sem_merito")

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
            elif parcial_count > 0:
                resultado = "PARCIALMENTE FAVORÁVEL"
                confianca = parcial_count / total
            elif acordo_count > 0:
                resultado = "ACORDO"
                confianca = acordo_count / total
            elif extinto_com_merito_count > 0:
                resultado = "EXTINTO COM MERITO"
                confianca = extinto_com_merito_count / total
            elif extinto_sem_merito_count > 0:
                resultado = "EXTINTO SEM MERITO"
                confianca = extinto_sem_merito_count / total

            return ResultadoAnalise(
                resultado_principal=resultado,
                confianca=confianca,
                evidencias=evidencias,
                metodo_usado="direitos_trabalhistas",
                detalhes={
                    "total_direitos": total,
                    "favoravel_count": favoravel_count,
                    "desfavoravel_count": desfavoravel_count,
                    "parcial_count": parcial_count,
                    "acordo_count": acordo_count,
                    "extinto_com_merito_count": extinto_com_merito_count,
                    "extinto_sem_merito_count": extinto_sem_merito_count,
                },
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
            matches = re.finditer(padrao["pattern"], texto_lower, re.IGNORECASE)
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
            # Sentenças (primeira instância) - Captura a palavra "sentença" seguida de um resultado
            r"\b(?:sentença|decisão\s+de\s+primeiro\s+grau|decisão\s+de\s+primeira\s+instância)\s*(?:foi)?\s*(?:julgada|proferida|que\s+resultou\s+em)?\s*(?:totalmente\s+)?(?:procedente|improcedente|parcialmente\s+procedente|homologatória|extinta)\b",
            r"\b(?:julgo|decido|sentencio)\s+(?:o\s+pedido|a\s+ação|os\s+pedidos|a\s+pretensão)?\s*(?:totalmente\s+)?(?:procedente|improcedente|parcialmente\s+procedente)\b",
            # Acórdãos (segunda instância e superiores) - Foca em termos de recurso e suas resoluções
            r"\b(?:acórdão|decisão\s+colegiada|julgado|aresto)\s*(?:que\s+)?(?:deu|negou|manteve|reformou|confirmou|proveu|desproveu|improvimento)?\s*(?:provimento|desprovimento|provimento\s+parcial|reforma|manutenção)?\s*(?:ao\s+recurso)?\b",
            r"\b(?:recurso\s+ordinário|recurso\s+de\s+revista|agravo\s+de\s+instrumento|embargos\s+de\s+declaração)\s*(?:foi)?\s*(?:provido|desprovido|parcialmente\s+provido|conhecido\s+e\s+não\s+provido|reformado|mantido|não\s+conhecido)\b",
            r"\b(?:dou|nego|mantenho|reformo|provejo|desprovejo)\s+(?:provimento\s+)?(?:ao\s+)?(?:recurso|apelo)?\b",
            # Dispositivo / Conclusão - Linguagem final e decisória
            r"\b(?:dispositivo|decisão|conclusão|ante\s+o\s+exposto|pelo\s+exposto|isto\s+posto|em\s+face\s+do\s+exposto)\s*(?:o\s+juiz|o\s+tribunal|o\s+relator)?\s*(?:julga|decide|condena|absolve|defere|indefere|acolhe|rejeita|homologa|concede|reconhece|determina|extingue)?\s*(?:o\s+pedido|a\s+ação)?\s*(?:totalmente\s+)?(?:procedente|improcedente|parcialmente\s+procedente|acordado|extinto)\b",
            r"\b(?:condeno|absolvo|defiro|indefiro|acolho|rejeito|homologo|concedo|reconheço|determino|extingo)\s+(?:o\s+reclamado|a\s+empresa|o\s+pedido|a\s+pretensão|as\s+partes)?(?:\s+ao\s+pagamento|\s+a\s+anotação|\s+o\s+vínculo|\s+a\s+extinção)?\b",
            # Ementa - Geralmente um resumo conciso da decisão
            r"\bementa\s*(?:deu|negou|proveu|desproveu)?\s*(?:provimento|desprovimento)?\s*(?:a\s+recurso)?\s*(?:para)?\s*(?:julgar|declarar)?\s*(?:procedente|improcedente|parcialmente)?\b",
            r"\bementa\s*:\s*(?:horas\s+extras|indenização|vínculo|adicional\s+noturno)\s*(?:devidas|deferido|reconhecido|indeferidas)\b",  # Ementa com resultado do direito específico
            # Padrões mais genéricos que indicam desfecho no texto corrido
            r"\b(?:restou\s+comprovado|não\s+restou\s+comprovado|ficou\s+demonstrado|não\s+ficou\s+demonstrado)\s+que\s+(?:o\s+reclamante\s+faz\s+jus|a\s+pretensão\s+não\s+procede)\b",
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

    def _combinar_resultados(
        self, resultados: List[ResultadoAnalise]
    ) -> ResultadoAnalise:
        """Combina múltiplos resultados de análise"""

        if not resultados:
            return ResultadoAnalise(
                resultado_principal="Resultado não identificado",
                confianca=0.0,
                evidencias=[],
                metodo_usado="sem_resultados",
                detalhes={},
            )

        if len(resultados) == 1:
            return resultados[0]

        # Calcular pesos por método
        pesos_metodo = {
            "padroes_regex": 1.0,
            "direitos_trabalhistas": 0.8,
            "contexto_semantico": 0.9,
            "estrutura_documento": 0.7,
            "inferencia": 0.6,
            "linguagem_juridica": 0.7,
        }

        # Calcular scores ponderados
        scores = {
            "FAVORÁVEL AO REQUERENTE": 0.0,
            "DESFAVORÁVEL AO REQUERENTE": 0.0,
            "PARCIALMENTE FAVORÁVEL": 0.0,
            "ACORDO": 0.0,
            "EXTINTO COM MERITO": 0.0,
            "EXTINTO SEM MERITO": 0.0,
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
            detalhes={"scores": scores, "metodos_detalhes": detalhes_combinados},
        )
