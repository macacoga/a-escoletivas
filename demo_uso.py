#!/usr/bin/env python3
"""
Script de Demonstração - Como Usar a Ferramenta de Ações Coletivas
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configurações da API
API_BASE_URL = "http://localhost:5000"
API_TIMEOUT = 10

def print_header(title):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*60)
    print(f"🎯 {title}")
    print("="*60)

def print_section(title):
    """Imprime seção formatada"""
    print(f"\n📋 {title}")
    print("-" * 40)

def check_api_status():
    """Verifica se a API está rodando"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=API_TIMEOUT)
        if response.status_code == 200:
            print("✅ API está funcionando!")
            return True
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar com a API: {e}")
        print("\n💡 Certifique-se de que a API está rodando:")
        print("   python start_api.py")
        return False

def demo_listar_acoes():
    """Demonstra como listar ações"""
    print_section("Listando Ações (Primeira página)")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/acoes",
            params={"page": 1, "per_page": 5},
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Total de ações: {data['total']}")
            print(f"📄 Página atual: {data['page']}")
            print(f"📋 Ações por página: {data['per_page']}")
            
            print("\n📋 Primeiras ações:")
            for i, acao in enumerate(data['acoes'][:3], 1):
                print(f"  {i}. Processo: {acao['numero_processo']}")
                print(f"     Tribunal: {acao['tribunal']}")
                print(f"     Data: {acao['data_publicacao']}")
                if acao.get('resumo'):
                    print(f"     Resumo: {acao['resumo'][:100]}...")
                print()
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def demo_buscar_acoes():
    """Demonstra como buscar ações"""
    print_section("Buscando Ações por Palavras-chave")
    
    try:
        # Buscar por palavras-chave
        response = requests.get(
            f"{API_BASE_URL}/api/acoes/search",
            params={
                "keywords": "banco",
                "page": 1,
                "per_page": 3
            },
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔍 Busca por 'banco' - Encontradas: {data['total']} ações")
            
            if data['acoes']:
                print("\n📋 Resultados:")
                for i, acao in enumerate(data['acoes'], 1):
                    print(f"  {i}. {acao['numero_processo']} - {acao['tribunal']}")
                    if acao.get('palavras_chave'):
                        print(f"     Palavras-chave: {', '.join(acao['palavras_chave'][:3])}")
            else:
                print("   Nenhuma ação encontrada")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def demo_detalhes_acao():
    """Demonstra como ver detalhes de uma ação"""
    print_section("Detalhes de uma Ação Específica")
    
    try:
        # Primeiro, pegar uma ação da lista
        response = requests.get(
            f"{API_BASE_URL}/api/acoes",
            params={"page": 1, "per_page": 1},
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['acoes']:
                acao_id = data['acoes'][0]['id']
                
                # Agora buscar detalhes
                response = requests.get(
                    f"{API_BASE_URL}/api/acoes/{acao_id}",
                    timeout=API_TIMEOUT
                )
                
                if response.status_code == 200:
                    acao = response.json()
                    print(f"📋 Ação ID: {acao['id']}")
                    print(f"   Processo: {acao['numero_processo']}")
                    print(f"   Tribunal: {acao['tribunal']}")
                    print(f"   Classe: {acao['classe_processo']}")
                    print(f"   Data: {acao['data_publicacao']}")
                    print(f"   Relator: {acao['relator']}")
                    
                    if acao.get('resumo'):
                        print(f"   Resumo: {acao['resumo'][:200]}...")
                    
                    if acao.get('palavras_chave'):
                        print(f"   Palavras-chave: {', '.join(acao['palavras_chave'])}")
                    
                    if acao.get('tema_principal'):
                        print(f"   Tema: {acao['tema_principal']}")
                else:
                    print(f"❌ Erro ao buscar detalhes: {response.status_code}")
            else:
                print("   Nenhuma ação disponível")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def demo_topicos():
    """Demonstra como listar tópicos"""
    print_section("Tópicos Mais Frequentes")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/topicos",
            params={"limit": 10},
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Total de tópicos: {len(data['topicos'])}")
            
            print("\n🏷️  Tópicos mais frequentes:")
            for i, topico in enumerate(data['topicos'][:5], 1):
                print(f"  {i}. {topico['tema']} ({topico['frequencia']} ocorrências)")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def demo_estatisticas():
    """Demonstra como ver estatísticas"""
    print_section("Estatísticas Gerais")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/stats/geral",
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            stats = response.json()
            print("📊 Estatísticas do Sistema:")
            print(f"   Total de ações: {stats['total_acoes']}")
            print(f"   Ações com resumo: {stats['acoes_com_resumo']}")
            print(f"   Ações com palavras-chave: {stats['acoes_com_palavras_chave']}")
            print(f"   Ações com tema: {stats['acoes_com_tema']}")
            print(f"   Tribunais únicos: {stats['tribunais_unicos']}")
            print(f"   Período: {stats['data_mais_antiga']} a {stats['data_mais_recente']}")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def demo_busca_avancada():
    """Demonstra busca avançada"""
    print_section("Busca Avançada (Múltiplos Filtros)")
    
    try:
        # Buscar ações de 2023 com palavras específicas
        response = requests.get(
            f"{API_BASE_URL}/api/acoes/search",
            params={
                "keywords": "trabalho",
                "data_inicio": "2023-01-01",
                "data_fim": "2023-12-31",
                "page": 1,
                "per_page": 3
            },
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔍 Busca avançada - Encontradas: {data['total']} ações")
            print("   Filtros: 'trabalho' + período 2023")
            
            if data['acoes']:
                print("\n📋 Resultados:")
                for i, acao in enumerate(data['acoes'], 1):
                    print(f"  {i}. {acao['numero_processo']}")
                    print(f"     Data: {acao['data_publicacao']}")
                    print(f"     Tribunal: {acao['tribunal']}")
            else:
                print("   Nenhuma ação encontrada")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def mostrar_urls_uteis():
    """Mostra URLs úteis da API"""
    print_section("URLs Úteis da API")
    
    urls = [
        ("🏠 Página Principal", f"{API_BASE_URL}/"),
        ("📚 Documentação", f"{API_BASE_URL}/api/docs/"),
        ("❤️  Health Check", f"{API_BASE_URL}/health"),
        ("📋 Listar Ações", f"{API_BASE_URL}/api/acoes"),
        ("🔍 Buscar Ações", f"{API_BASE_URL}/api/acoes/search"),
        ("🏷️  Tópicos", f"{API_BASE_URL}/api/topicos"),
        ("📊 Estatísticas", f"{API_BASE_URL}/api/stats/geral"),
    ]
    
    for nome, url in urls:
        print(f"   {nome}: {url}")

def main():
    """Função principal"""
    print_header("DEMONSTRAÇÃO - FERRAMENTA DE AÇÕES COLETIVAS")
    
    print("🎯 Este script demonstra como usar a API da ferramenta")
    print("💡 Certifique-se de que a API está rodando (python start_api.py)")
    
    # Verificar se API está rodando
    if not check_api_status():
        return
    
    # Executar demonstrações
    demo_estatisticas()
    demo_listar_acoes()
    demo_buscar_acoes()
    demo_detalhes_acao()
    demo_topicos()
    demo_busca_avancada()
    
    print_header("RESUMO DA DEMONSTRAÇÃO")
    
    print("✅ Demonstrações concluídas!")
    print("\n🎯 Principais funcionalidades testadas:")
    print("   📋 Listagem de ações com paginação")
    print("   🔍 Busca por palavras-chave")
    print("   📄 Visualização de detalhes")
    print("   🏷️  Listagem de tópicos")
    print("   📊 Estatísticas gerais")
    print("   🔍 Busca avançada com filtros")
    
    mostrar_urls_uteis()
    
    print("\n💡 Próximos passos:")
    print("   1. Explore a documentação Swagger")
    print("   2. Teste diferentes filtros de busca")
    print("   3. Integre com suas ferramentas")
    print("   4. Use os dados para análise")
    
    print("\n🎉 Sua ferramenta está pronta para uso!")

if __name__ == "__main__":
    main() 