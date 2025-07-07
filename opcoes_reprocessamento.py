#!/usr/bin/env python3
"""
Opções práticas para reprocessamento NLP
"""

import sqlite3
import subprocess
import sys
import time
from typing import Optional

def opcao_1_processar_poucos():
    """Opção 1: Processar apenas alguns processos (10-50)"""
    
    print("=== OPÇÃO 1: PROCESSAR POUCOS PROCESSOS ===")
    print("Processará apenas os primeiros 10-50 processos não processados")
    
    conn = sqlite3.connect('data/acoes_coletivas.db')
    cursor = conn.cursor()
    
    # Buscar processos não processados
    query = """
    SELECT p.id, p.numero_processo, p.tribunal
    FROM processos_judiciais p
    LEFT JOIN resultados_nlp r ON p.id = r.processo_id
    WHERE p.processado_nlp = 0 OR r.id IS NULL
    ORDER BY p.id
    LIMIT 20
    """
    
    cursor.execute(query)
    processos = cursor.fetchall()
    conn.close()
    
    if not processos:
        print("✅ Não há processos para processar!")
        return
    
    print(f"Encontrados {len(processos)} processos:")
    for i, (p_id, numero, tribunal) in enumerate(processos[:5], 1):
        print(f"  {i}. {numero} ({tribunal})")
    
    if len(processos) > 5:
        print(f"  ... e mais {len(processos) - 5} processos")
    
    resposta = input(f"\nProcessar estes {len(processos)} processos? (s/N): ").strip().lower()
    
    if resposta in ['s', 'sim', 'y', 'yes']:
        ids = [str(p[0]) for p in processos]
        cmd = f"python acoes_coletivas.py nlp process --ids {','.join(ids)}"
        
        print(f"Executando: {cmd}")
        result = subprocess.run(cmd, shell=True)
        
        if result.returncode == 0:
            print("✅ Processamento concluído!")
        else:
            print("❌ Erro no processamento")
    else:
        print("❌ Operação cancelada")

def opcao_2_processar_por_tribunal():
    """Opção 2: Processar apenas de um tribunal específico"""
    
    print("=== OPÇÃO 2: PROCESSAR POR TRIBUNAL ===")
    
    conn = sqlite3.connect('data/acoes_coletivas.db')
    cursor = conn.cursor()
    
    # Listar tribunais disponíveis
    query = """
    SELECT p.tribunal, COUNT(*) as total,
           COUNT(r.id) as processados
    FROM processos_judiciais p
    LEFT JOIN resultados_nlp r ON p.id = r.processo_id
    WHERE p.tribunal IS NOT NULL AND p.tribunal != ''
    GROUP BY p.tribunal
    ORDER BY total DESC
    """
    
    cursor.execute(query)
    tribunais = cursor.fetchall()
    
    if not tribunais:
        print("❌ Nenhum tribunal encontrado!")
        conn.close()
        return
    
    print("Tribunais disponíveis:")
    for i, (tribunal, total, processados) in enumerate(tribunais, 1):
        pendentes = total - processados
        print(f"  {i}. {tribunal}: {total} processos ({pendentes} pendentes)")
    
    try:
        escolha = int(input(f"\nEscolha um tribunal (1-{len(tribunais)}): ")) - 1
        
        if 0 <= escolha < len(tribunais):
            tribunal_escolhido = tribunais[escolha][0]
            
            # Buscar processos não processados deste tribunal
            query = """
            SELECT p.id, p.numero_processo
            FROM processos_judiciais p
            LEFT JOIN resultados_nlp r ON p.id = r.processo_id
            WHERE p.tribunal = ? AND (p.processado_nlp = 0 OR r.id IS NULL)
            ORDER BY p.id
            LIMIT 50
            """
            
            cursor.execute(query, (tribunal_escolhido,))
            processos = cursor.fetchall()
            
            if not processos:
                print(f"✅ Todos os processos do {tribunal_escolhido} já foram processados!")
                conn.close()
                return
            
            print(f"\nEncontrados {len(processos)} processos pendentes do {tribunal_escolhido}")
            
            resposta = input(f"Processar estes {len(processos)} processos? (s/N): ").strip().lower()
            
            if resposta in ['s', 'sim', 'y', 'yes']:
                ids = [str(p[0]) for p in processos]
                cmd = f"python acoes_coletivas.py nlp process --ids {','.join(ids)}"
                
                print(f"Executando: {cmd}")
                result = subprocess.run(cmd, shell=True)
                
                if result.returncode == 0:
                    print("✅ Processamento concluído!")
                else:
                    print("❌ Erro no processamento")
            else:
                print("❌ Operação cancelada")
        else:
            print("❌ Escolha inválida")
    
    except ValueError:
        print("❌ Entrada inválida")
    
    conn.close()

def opcao_3_limpar_resultados():
    """Opção 3: Limpar resultados de baixa qualidade e reprocessar"""
    
    print("=== OPÇÃO 3: LIMPAR E REPROCESSAR BAIXA QUALIDADE ===")
    
    conn = sqlite3.connect('data/acoes_coletivas.db')
    cursor = conn.cursor()
    
    # Buscar resultados de baixa qualidade
    query = """
    SELECT p.id, p.numero_processo, p.tribunal,
           r.qualidade_texto, r.confianca_global
    FROM processos_judiciais p
    JOIN resultados_nlp r ON p.id = r.processo_id
    WHERE r.qualidade_texto < 0.5 OR r.confianca_global < 0.5
    ORDER BY r.qualidade_texto ASC
    LIMIT 20
    """
    
    cursor.execute(query)
    processos = cursor.fetchall()
    
    if not processos:
        print("✅ Não há processos com baixa qualidade!")
        conn.close()
        return
    
    print(f"Encontrados {len(processos)} processos com baixa qualidade:")
    for i, (p_id, numero, tribunal, qualidade, confianca) in enumerate(processos[:5], 1):
        print(f"  {i}. {numero} ({tribunal}) - Q: {qualidade:.2f}, C: {confianca:.2f}")
    
    if len(processos) > 5:
        print(f"  ... e mais {len(processos) - 5} processos")
    
    resposta = input(f"\nLimpar e reprocessar estes {len(processos)} processos? (s/N): ").strip().lower()
    
    if resposta in ['s', 'sim', 'y', 'yes']:
        # Limpar resultados
        ids = [p[0] for p in processos]
        placeholders = ','.join(['?' for _ in ids])
        
        cursor.execute(f"DELETE FROM resultados_nlp WHERE processo_id IN ({placeholders})", ids)
        cursor.execute(f"UPDATE processos_judiciais SET processado_nlp = 0 WHERE id IN ({placeholders})", ids)
        
        conn.commit()
        print(f"✅ Limpeza concluída! {len(processos)} resultados removidos.")
        
        # Reprocessar
        ids_str = ','.join(map(str, ids))
        cmd = f"python acoes_coletivas.py nlp process --ids {ids_str}"
        
        print(f"Executando: {cmd}")
        result = subprocess.run(cmd, shell=True)
        
        if result.returncode == 0:
            print("✅ Reprocessamento concluído!")
        else:
            print("❌ Erro no reprocessamento")
    else:
        print("❌ Operação cancelada")
    
    conn.close()

def testar_sistema_atual():
    """Testa o sistema atual com o novo analisador"""
    
    print("=== TESTE DO SISTEMA ATUAL ===")
    print("Testando o novo ResultadoAnalyzer com dados reais do banco...")
    
    # Conectar ao banco
    conn = sqlite3.connect('data/acoes_coletivas.db')
    cursor = conn.cursor()
    
    # Buscar processos com dados NLP
    query = """
    SELECT p.id, p.numero_processo, p.tribunal,
           r.resumo_extrativo, r.direitos_trabalhistas,
           r.qualidade_texto, r.confianca_global
    FROM processos_judiciais p
    JOIN resultados_nlp r ON p.id = r.processo_id
    WHERE r.resumo_extrativo IS NOT NULL
    ORDER BY r.qualidade_texto DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    processos = cursor.fetchall()
    
    if not processos:
        print("❌ Nenhum processo com dados NLP encontrado!")
        conn.close()
        return 0
    
    print(f"✅ Encontrados {len(processos)} processos com dados NLP")
    print()
    
    # Inicializar analisador
    from src.acoes_coletivas.nlp.resultado_analyzer import ResultadoAnalyzer
    analyzer = ResultadoAnalyzer()
    
    # Estatísticas
    resultados_stats = {
        'FAVORÁVEL AO REQUERENTE': 0,
        'DESFAVORÁVEL AO REQUERENTE': 0,
        'PARCIALMENTE FAVORÁVEL': 0,
        'Resultado não identificado': 0
    }
    
    print("=== ANÁLISE DOS PROCESSOS ===")
    
    for i, processo in enumerate(processos, 1):
        processo_id = processo[0]
        numero_processo = processo[1]
        tribunal = processo[2]
        resumo_extrativo = processo[3]
        direitos_trabalhistas = processo[4]
        qualidade_texto = processo[5]
        confianca_global = processo[6]
        
        print(f"\n{i}. Processo {numero_processo} ({tribunal})")
        print(f"   Qualidade: {qualidade_texto:.2f}" if qualidade_texto else "   Qualidade: N/A")
        
        # Analisar resultado
        start_time = time.time()
        resultado_analise = analyzer.analisar_resultado(resumo_extrativo, direitos_trabalhistas)
        end_time = time.time()
        
        resultado = resultado_analise.resultado_principal
        confianca = resultado_analise.confianca
        
        print(f"   ➤ RESULTADO: {resultado}")
        print(f"   ➤ Confiança: {confianca:.2f}")
        print(f"   ➤ Tempo: {(end_time - start_time)*1000:.1f}ms")
        
        # Mostrar evidências se houver
        if resultado_analise.evidencias:
            print(f"   ➤ Evidências: {len(resultado_analise.evidencias)} encontradas")
            for evidencia in resultado_analise.evidencias[:2]:  # Mostrar só as 2 primeiras
                if isinstance(evidencia, dict):
                    metodo = evidencia.get('metodo', 'N/A')
                    texto = evidencia.get('texto', '')
                    print(f"     - {metodo}: {texto[:50]}...")
        
        # Atualizar estatísticas
        resultados_stats[resultado] += 1
    
    conn.close()
    
    print("\n=== ESTATÍSTICAS FINAIS ===")
    total_processos = len(processos)
    for resultado, count in resultados_stats.items():
        percentual = (count / total_processos) * 100
        print(f"{resultado}: {count} ({percentual:.1f}%)")
    
    # Calcular taxa de identificação
    identificados = total_processos - resultados_stats['Resultado não identificado']
    taxa_identificacao = (identificados / total_processos) * 100
    
    print(f"\n📊 TAXA DE IDENTIFICAÇÃO: {taxa_identificacao:.1f}%")
    
    if taxa_identificacao > 0:
        print("✅ Sistema funcionando! Resultados sendo identificados.")
    else:
        print("❌ Sistema não está identificando resultados.")
    
    return taxa_identificacao

def testar_casos_especificos():
    """Testa casos específicos para validar o analisador"""
    
    print("\n=== TESTE DE CASOS ESPECÍFICOS ===")
    
    from src.acoes_coletivas.nlp.resultado_analyzer import ResultadoAnalyzer
    analyzer = ResultadoAnalyzer()
    
    casos_teste = [
        {
            'nome': 'Caso Favorável - Deferimento',
            'resumo': 'Defiro o pedido de horas extras e determino o pagamento de R$ 5.000,00 ao requerente.',
            'direitos': None,
            'esperado': 'FAVORÁVEL AO REQUERENTE'
        },
        {
            'nome': 'Caso Desfavorável - Improcedência',
            'resumo': 'Julgo improcedente o pedido por falta de provas suficientes.',
            'direitos': None,
            'esperado': 'DESFAVORÁVEL AO REQUERENTE'
        },
        {
            'nome': 'Caso Parcial - Procedência em Parte',
            'resumo': 'Julgo parcialmente procedente o pedido, deferindo apenas as horas extras.',
            'direitos': None,
            'esperado': 'PARCIALMENTE FAVORÁVEL'
        },
        {
            'nome': 'Caso Novo Padrão - Nego Seguimento',
            'resumo': 'Nego seguimento ao recurso por ausência de fundamentação adequada.',
            'direitos': None,
            'esperado': 'DESFAVORÁVEL AO REQUERENTE'
        },
        {
            'nome': 'Caso Novo Padrão - Rejeição',
            'resumo': 'Rejeitado o pedido de indenização por danos morais por falta de comprovação.',
            'direitos': None,
            'esperado': 'DESFAVORÁVEL AO REQUERENTE'
        }
    ]
    
    acertos = 0
    
    for caso in casos_teste:
        resultado_analise = analyzer.analisar_resultado(caso['resumo'], caso['direitos'])
        resultado = resultado_analise.resultado_principal
        
        acertou = resultado == caso['esperado']
        status = "✅" if acertou else "❌"
        
        print(f"{status} {caso['nome']}")
        print(f"   Esperado: {caso['esperado']}")
        print(f"   Obtido: {resultado}")
        print(f"   Confiança: {resultado_analise.confianca:.2f}")
        
        if acertou:
            acertos += 1
        
        print()
    
    taxa_acerto = (acertos / len(casos_teste)) * 100
    print(f"📊 TAXA DE ACERTO EM CASOS ESPECÍFICOS: {taxa_acerto:.1f}%")
    
    return taxa_acerto

def opcao_4_testar_melhorias():
    """Opção 4: Apenas testar as melhorias sem reprocessar"""
    
    print("=== OPÇÃO 4: TESTAR MELHORIAS ATUAIS ===")
    
    try:
        # Testar sistema atual
        taxa_identificacao = testar_sistema_atual()
        
        # Testar casos específicos
        taxa_acerto = testar_casos_especificos()
        
        print("\n=== RESUMO FINAL ===")
        print(f"Taxa de identificação (dados reais): {taxa_identificacao:.1f}%")
        print(f"Taxa de acerto (casos teste): {taxa_acerto:.1f}%")
        
        if taxa_identificacao and taxa_acerto and taxa_identificacao > 30 and taxa_acerto > 80:
            print("✅ Sistema funcionando adequadamente!")
        elif taxa_identificacao and taxa_identificacao > 0:
            print("⚠️  Sistema funcionando, mas pode ser melhorado.")
        else:
            print("❌ Sistema precisa de ajustes.")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

def main():
    """Menu principal"""
    
    print("🔄 OPÇÕES DE REPROCESSAMENTO NLP")
    print("=" * 40)
    
    print("Escolha uma opção:")
    print("1. Processar poucos processos (10-50)")
    print("2. Processar por tribunal específico")
    print("3. Limpar baixa qualidade e reprocessar")
    print("4. Apenas testar melhorias atuais")
    print("5. Sair")
    
    try:
        opcao = int(input("\nSua escolha (1-5): "))
        
        if opcao == 1:
            opcao_1_processar_poucos()
        elif opcao == 2:
            opcao_2_processar_por_tribunal()
        elif opcao == 3:
            opcao_3_limpar_resultados()
        elif opcao == 4:
            opcao_4_testar_melhorias()
        elif opcao == 5:
            print("👋 Até logo!")
            sys.exit(0)
        else:
            print("❌ Opção inválida")
    
    except ValueError:
        print("❌ Entrada inválida")
    except KeyboardInterrupt:
        print("\n❌ Operação cancelada pelo usuário")

if __name__ == "__main__":
    main() 