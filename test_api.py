#!/usr/bin/env python3
"""
Script de teste da API RESTful para Ações Coletivas
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class APITester:
    """Testador da API"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def test_endpoint(self, endpoint: str, method: str = "GET", 
                     params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """Testa um endpoint da API"""
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            print(f"\n🔍 Testando {method} {endpoint}")
            if params:
                print(f"   Parâmetros: {params}")
            
            start_time = time.time()
            
            if method == "GET":
                response = self.session.get(url, params=params)
            elif method == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Método não suportado: {method}")
            
            elapsed_time = time.time() - start_time
            
            print(f"   Status: {response.status_code}")
            print(f"   Tempo: {elapsed_time:.3f}s")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Sucesso")
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'data': result,
                    'elapsed_time': elapsed_time
                }
            else:
                print(f"   ❌ Erro: {response.text}")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text,
                    'elapsed_time': elapsed_time
                }
                
        except Exception as e:
            print(f"   ❌ Exceção: {e}")
            return {
                'success': False,
                'error': str(e),
                'elapsed_time': 0
            }
    
    def test_health_check(self):
        """Testa health check"""
        return self.test_endpoint('/health')
    
    def test_api_info(self):
        """Testa informações da API"""
        return self.test_endpoint('/api')
    
    def test_acoes_list(self):
        """Testa listagem de ações"""
        return self.test_endpoint('/api/acoes', params={'page': 1, 'per_page': 5})
    
    def test_acoes_search(self):
        """Testa busca de ações"""
        return self.test_endpoint('/api/acoes/search', params={
            'keywords': 'trabalho',
            'processado_nlp': True,
            'page': 1,
            'per_page': 3
        })
    
    def test_topicos(self):
        """Testa listagem de tópicos"""
        return self.test_endpoint('/api/topicos', params={'limite': 5})
    
    def test_topicos_direitos(self):
        """Testa direitos trabalhistas"""
        return self.test_endpoint('/api/topicos/direitos', params={'limite': 5})
    
    def test_stats_geral(self):
        """Testa estatísticas gerais"""
        return self.test_endpoint('/api/stats/geral')
    
    def test_stats_distribuicao(self):
        """Testa distribuição por tribunal"""
        return self.test_endpoint('/api/stats/distribuicao', params={
            'categoria': 'tribunal',
            'limite': 5
        })
    
    def test_stats_timeline(self):
        """Testa timeline"""
        return self.test_endpoint('/api/stats/timeline', params={
            'periodo': 'mes',
            'limite': 6
        })
    
    def test_stats_qualidade(self):
        """Testa estatísticas de qualidade"""
        return self.test_endpoint('/api/stats/qualidade')
    
    def test_acao_individual(self):
        """Testa busca de ação individual"""
        # Primeiro, buscar uma ação para pegar o ID
        acoes_result = self.test_endpoint('/api/acoes', params={'page': 1, 'per_page': 1})
        
        if acoes_result['success'] and acoes_result['data'].get('data'):
            acao_id = acoes_result['data']['data'][0]['id']
            return self.test_endpoint(f'/api/acoes/{acao_id}')
        else:
            print("   ⚠️  Nenhuma ação encontrada para teste individual")
            return {'success': False, 'error': 'Nenhuma ação encontrada'}
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 Iniciando testes da API...")
        print(f"   Base URL: {self.base_url}")
        print(f"   Horário: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("API Info", self.test_api_info),
            ("Listar Ações", self.test_acoes_list),
            ("Buscar Ações", self.test_acoes_search),
            ("Ação Individual", self.test_acao_individual),
            ("Listar Tópicos", self.test_topicos),
            ("Direitos Trabalhistas", self.test_topicos_direitos),
            ("Estatísticas Gerais", self.test_stats_geral),
            ("Distribuição", self.test_stats_distribuicao),
            ("Timeline", self.test_stats_timeline),
            ("Qualidade NLP", self.test_stats_qualidade),
        ]
        
        results = []
        successful_tests = 0
        total_time = 0
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            print("-" * 50)
            
            result = test_func()
            results.append({
                'name': test_name,
                'result': result
            })
            
            if result['success']:
                successful_tests += 1
            
            total_time += result.get('elapsed_time', 0)
        
        # Resumo dos testes
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        print(f"Total de testes: {len(tests)}")
        print(f"Sucessos: {successful_tests}")
        print(f"Falhas: {len(tests) - successful_tests}")
        print(f"Taxa de sucesso: {(successful_tests / len(tests)) * 100:.1f}%")
        print(f"Tempo total: {total_time:.3f}s")
        
        # Detalhes dos testes falhos
        failed_tests = [r for r in results if not r['result']['success']]
        if failed_tests:
            print("\n❌ TESTES FALHOS:")
            for test in failed_tests:
                print(f"   - {test['name']}: {test['result'].get('error', 'Erro desconhecido')}")
        
        # Estatísticas dos testes bem-sucedidos
        successful_results = [r for r in results if r['result']['success']]
        if successful_results:
            print("\n✅ TESTES BEM-SUCEDIDOS:")
            for test in successful_results:
                result = test['result']
                status = result.get('status_code', 'N/A')
                time_str = f"{result.get('elapsed_time', 0):.3f}s"
                print(f"   - {test['name']}: {status} ({time_str})")
        
        return {
            'total_tests': len(tests),
            'successful_tests': successful_tests,
            'failed_tests': len(tests) - successful_tests,
            'success_rate': (successful_tests / len(tests)) * 100,
            'total_time': total_time,
            'results': results
        }

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Testa a API RESTful de Ações Coletivas')
    parser.add_argument(
        '--url', 
        default='http://localhost:5000',
        help='URL base da API (padrão: http://localhost:5000)'
    )
    parser.add_argument(
        '--test',
        help='Teste específico para executar',
        choices=['health', 'api', 'acoes', 'search', 'topicos', 'stats']
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Mostrar detalhes das respostas'
    )
    
    args = parser.parse_args()
    
    # Verificar se a API está rodando
    try:
        response = requests.get(f"{args.url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API não está respondendo corretamente em {args.url}")
            print(f"   Status: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Não foi possível conectar à API em {args.url}")
        print(f"   Erro: {e}")
        print("\n💡 Verifique se a API está rodando:")
        print("   python app.py")
        return
    
    tester = APITester(args.url)
    
    if args.test:
        # Executar teste específico
        test_methods = {
            'health': tester.test_health_check,
            'api': tester.test_api_info,
            'acoes': tester.test_acoes_list,
            'search': tester.test_acoes_search,
            'topicos': tester.test_topicos,
            'stats': tester.test_stats_geral
        }
        
        if args.test in test_methods:
            result = test_methods[args.test]()
            if args.verbose and result['success']:
                print("\n📄 Resposta:")
                print(json.dumps(result['data'], indent=2, ensure_ascii=False))
        else:
            print(f"❌ Teste '{args.test}' não encontrado")
    else:
        # Executar todos os testes
        summary = tester.run_all_tests()
        
        if args.verbose:
            print("\n📄 DETALHES DAS RESPOSTAS:")
            for result in summary['results']:
                if result['result']['success']:
                    print(f"\n--- {result['name']} ---")
                    print(json.dumps(result['result']['data'], indent=2, ensure_ascii=False)[:500] + "...")

if __name__ == "__main__":
    main() 