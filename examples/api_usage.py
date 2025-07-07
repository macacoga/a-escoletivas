#!/usr/bin/env python3
"""
Exemplos de uso da API RESTful de Ações Coletivas
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class APIClient:
    """Cliente para interagir com a API"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Faz uma requisição GET"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict:
        """Verifica a saúde da API"""
        return self.get('/health')
    
    def get_api_info(self) -> Dict:
        """Obter informações da API"""
        return self.get('/api')
    
    def list_acoes(self, page: int = 1, per_page: int = 20, 
                   include_content: bool = False) -> Dict:
        """Listar ações coletivas"""
        params = {
            'page': page,
            'per_page': per_page,
            'include_content': include_content
        }
        return self.get('/api/acoes', params=params)
    
    def get_acao(self, acao_id: int, include_content: bool = True) -> Dict:
        """Obter ação específica"""
        params = {'include_content': include_content}
        return self.get(f'/api/acoes/{acao_id}', params=params)
    
    def search_acoes(self, **filters) -> Dict:
        """Buscar ações com filtros"""
        return self.get('/api/acoes/search', params=filters)
    
    def get_topicos(self, limite: int = 20, apenas_nlp: bool = True) -> Dict:
        """Listar tópicos frequentes"""
        params = {'limite': limite, 'apenas_nlp': apenas_nlp}
        return self.get('/api/topicos', params=params)
    
    def get_direitos(self, limite: int = 20, resultado: str = "granted", 
                     detalhado: bool = False) -> Dict:
        """Listar direitos trabalhistas"""
        params = {'limite': limite, 'detalhado': detalhado}
        if resultado:
            params['resultado'] = resultado
        return self.get('/api/topicos/direitos', params=params)
    
    def get_stats_geral(self) -> Dict:
        """Obter estatísticas gerais"""
        return self.get('/api/stats/geral')
    
    def get_distribuicao(self, categoria: str, limite: int = 10) -> Dict:
        """Obter distribuição por categoria"""
        params = {'categoria': categoria, 'limite': limite}
        return self.get('/api/stats/distribuicao', params=params)
    
    def get_timeline(self, periodo: str = 'mes', limite: int = 12) -> Dict:
        """Obter timeline de coletas"""
        params = {'periodo': periodo, 'limite': limite}
        return self.get('/api/stats/timeline', params=params)
    
    def get_qualidade(self) -> Dict:
        """Obter estatísticas de qualidade NLP"""
        return self.get('/api/stats/qualidade')


def exemplo_basico():
    """Exemplo básico de uso da API"""
    print("=" * 60)
    print("🔍 EXEMPLO BÁSICO - Informações da API")
    print("=" * 60)
    
    try:
        client = APIClient()
        
        # Verificar saúde da API
        health = client.health_check()
        print(f"✅ API Status: {health['status']}")
        print(f"📊 Total de processos: {health['database']['total_processos']}")
        
        # Obter informações da API
        info = client.get_api_info()
        print(f"📋 API: {info['name']} v{info['version']}")
        print(f"📖 Descrição: {info['description']}")
        
        # Listar primeiras ações
        acoes = client.list_acoes(page=1, per_page=3)
        print(f"\n📄 Primeiras {len(acoes['data'])} ações:")
        for acao in acoes['data']:
            print(f"  - {acao['numero_processo']} ({acao['tribunal']})")
            if acao['processado_nlp']:
                print(f"    NLP: {acao.get('tema_principal', 'N/A')} "
                      f"(qualidade: {acao.get('qualidade_texto', 0):.2f})")
        
        print(f"\n📊 Paginação: {acoes['pagination']['page']}/{acoes['pagination']['pages']}")
        print(f"📈 Total: {acoes['pagination']['total']} processos")
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def exemplo_busca_avancada():
    """Exemplo de busca avançada com filtros"""
    print("\n" + "=" * 60)
    print("🔍 EXEMPLO AVANÇADO - Busca com Filtros")
    print("=" * 60)
    
    try:
        client = APIClient()
        
        # Buscar processos sobre horas extras
        print("🔍 Buscando processos sobre 'horas extras'...")
        resultados = client.search_acoes(
            keywords='horas extras',
            processado_nlp=True,
            qualidade_minima=0.7,
            sort_by='qualidade_texto',
            sort_order='desc',
            page=1,
            per_page=5
        )
        
        print(f"📊 Encontrados: {resultados['total_found']} processos")
        print("🏆 Top 5 por qualidade:")
        for i, acao in enumerate(resultados['data'], 1):
            print(f"  {i}. {acao['numero_processo']} ({acao['tribunal']})")
            print(f"     Qualidade: {acao.get('qualidade_texto', 0):.3f}")
            print(f"     Tema: {acao.get('tema_principal', 'N/A')}")
        
        # Buscar por tribunal específico
        print("\n🏛️ Buscando processos do TRT10...")
        trt10 = client.search_acoes(
            tribunal='TRT10',
            processado_nlp=True,
            page=1,
            per_page=3
        )
        
        print(f"📊 TRT10: {trt10['total_found']} processos")
        for acao in trt10['data']:
            print(f"  - {acao['numero_processo']}")
            if acao.get('tema_principal'):
                print(f"    Tema: {acao['tema_principal']}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def exemplo_topicos_e_direitos():
    """Exemplo de análise de tópicos e direitos"""
    print("\n" + "=" * 60)
    print("📊 EXEMPLO - Tópicos e Direitos Trabalhistas")
    print("=" * 60)
    
    try:
        client = APIClient()
        
        # Obter tópicos frequentes
        print("🏷️ Tópicos mais frequentes:")
        topicos = client.get_topicos(limite=5)
        
        print(f"📈 Analisados: {topicos['total_processos_analisados']} processos")
        
        # Temas principais
        print("\n🎯 Temas principais:")
        for tema in topicos['temas_principais'][:3]:
            print(f"  - {tema['nome']}: {tema['frequencia']} "
                  f"({tema['porcentagem']:.1f}%)")
        
        # Direitos trabalhistas
        print("\n⚖️ Direitos trabalhistas:")
        for direito in topicos['direitos_trabalhistas'][:3]:
            print(f"  - {direito['nome']}: {direito['frequencia']} "
                  f"({direito['porcentagem']:.1f}%)")
        
        # Tribunais
        print("\n🏛️ Tribunais:")
        for tribunal in topicos['tribunais'][:3]:
            print(f"  - {tribunal['nome']}: {tribunal['frequencia']} "
                  f"({tribunal['porcentagem']:.1f}%)")
        
        # Análise detalhada de direitos
        print("\n📋 Análise detalhada de direitos concedidos:")
        direitos = client.get_direitos(
            limite=3,
            resultado='granted',
            detalhado=False
        )
        
        for direito in direitos['direitos_trabalhistas']:
            print(f"  - {direito['tipo']}: {direito['total_casos']} casos")
            print(f"    Taxa de sucesso: {direito['taxa_sucesso']:.1f}%")
            print(f"    Confiança média: {direito['confianca_media']:.3f}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def exemplo_estatisticas():
    """Exemplo de análise estatística"""
    print("\n" + "=" * 60)
    print("📈 EXEMPLO - Estatísticas e Análises")
    print("=" * 60)
    
    try:
        client = APIClient()
        
        # Estatísticas gerais
        print("📊 Estatísticas gerais:")
        stats = client.get_stats_geral()
        
        print(f"  📄 Total de processos: {stats['total_processos']}")
        print(f"  🤖 Processados com NLP: {stats['processos_processados']}")
        print(f"  🏛️ Tribunais únicos: {stats['tribunais_unicos']}")
        
        if stats['qualidade_media']:
            print(f"  📊 Qualidade média: {stats['qualidade_media']:.3f}")
            print(f"  🎯 Confiança média: {stats['confianca_media']:.3f}")
            print(f"  ⏱️ Tempo médio: {stats['tempo_processamento_medio']:.2f}s")
        
        # Distribuição por tribunal
        print("\n🏛️ Distribuição por tribunal:")
        dist_tribunal = client.get_distribuicao('tribunal', limite=5)
        
        for item in dist_tribunal['items']:
            print(f"  - {item['nome']}: {item['quantidade']} "
                  f"({item['porcentagem']:.1f}%)")
        
        # Distribuição por qualidade
        print("\n📊 Distribuição por qualidade:")
        dist_qualidade = client.get_distribuicao('qualidade', limite=5)
        
        for item in dist_qualidade['items']:
            print(f"  - {item['nome']}: {item['quantidade']} "
                  f"({item['porcentagem']:.1f}%)")
        
        # Timeline de coletas
        print("\n📅 Timeline de coletas (últimos 6 meses):")
        timeline = client.get_timeline('mes', limite=6)
        
        for periodo in timeline['timeline'][-3:]:  # Últimos 3 meses
            print(f"  - {periodo['periodo']}: {periodo['total_processos']} processos "
                  f"({periodo['taxa_processamento']:.1f}% processados)")
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def exemplo_processo_especifico():
    """Exemplo de análise de processo específico"""
    print("\n" + "=" * 60)
    print("🔍 EXEMPLO - Análise de Processo Específico")
    print("=" * 60)
    
    try:
        client = APIClient()
        
        # Buscar um processo processado com NLP
        print("🔍 Buscando processo com NLP...")
        acoes = client.search_acoes(
            processado_nlp=True,
            qualidade_minima=0.8,
            page=1,
            per_page=1
        )
        
        if not acoes['data']:
            print("❌ Nenhum processo encontrado com NLP de alta qualidade")
            return
        
        acao_id = acoes['data'][0]['id']
        print(f"📋 Analisando processo ID: {acao_id}")
        
        # Obter detalhes completos
        detalhes = client.get_acao(acao_id, include_content=False)
        
        print(f"📄 Número: {detalhes['numero_processo']}")
        print(f"🏛️ Tribunal: {detalhes['tribunal']}")
        print(f"📅 Data publicação: {detalhes.get('data_publicacao', 'N/A')}")
        print(f"👥 Partes: {detalhes.get('partes', 'N/A')[:100]}...")
        
        # Análise NLP
        if detalhes.get('resultado_nlp'):
            nlp = detalhes['resultado_nlp']
            print(f"\n🤖 Análise NLP:")
            print(f"  📊 Qualidade: {nlp['qualidade_texto']:.3f}")
            print(f"  🎯 Confiança: {nlp['confianca_global']:.3f}")
            print(f"  🏷️ Tema: {nlp.get('tema_principal', 'N/A')}")
            print(f"  ⏱️ Tempo processamento: {nlp['tempo_processamento']:.2f}s")
            
            # Entidades identificadas
            if nlp.get('entidades'):
                print(f"  🔍 Entidades identificadas: {len(nlp['entidades'])}")
                for ent in nlp['entidades'][:3]:
                    print(f"    - {ent['text']} ({ent['label']}) "
                          f"confiança: {ent['confidence']:.3f}")
            
            # Direitos trabalhistas
            if nlp.get('direitos_trabalhistas'):
                print(f"  ⚖️ Direitos identificados: {len(nlp['direitos_trabalhistas'])}")
                for direito in nlp['direitos_trabalhistas'][:3]:
                    outcome = direito.get('decision_outcome', 'N/A')
                    print(f"    - {direito['type']}: {outcome} "
                          f"(confiança: {direito['confidence']:.3f})")
            
            # Resumo
            if nlp.get('resumo_extrativo'):
                print(f"  📝 Resumo: {nlp['resumo_extrativo'][:200]}...")
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def exemplo_relatorio_completo():
    """Exemplo de relatório completo"""
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO COMPLETO - Análise Geral")
    print("=" * 60)
    
    try:
        client = APIClient()
        
        # Obter dados gerais
        stats = client.get_stats_geral()
        topicos = client.get_topicos(limite=10)
        qualidade = client.get_qualidade()
        
        print("📈 RESUMO EXECUTIVO")
        print("-" * 40)
        print(f"Total de processos coletados: {stats['total_processos']}")
        print(f"Processados com NLP: {stats['processos_processados']}")
        print(f"Taxa de processamento: {(stats['processos_processados']/stats['total_processos']*100):.1f}%")
        print(f"Tribunais únicos: {stats['tribunais_unicos']}")
        
        if stats['qualidade_media']:
            print(f"Qualidade média dos textos: {stats['qualidade_media']:.3f}")
            print(f"Confiança média das análises: {stats['confianca_media']:.3f}")
        
        print("\n🏛️ TRIBUNAIS MAIS ATIVOS")
        print("-" * 40)
        for tribunal in topicos['tribunais'][:5]:
            print(f"{tribunal['nome']}: {tribunal['frequencia']} processos "
                  f"({tribunal['porcentagem']:.1f}%)")
        
        print("\n⚖️ DIREITOS MAIS FREQUENTES")
        print("-" * 40)
        for direito in topicos['direitos_trabalhistas'][:5]:
            print(f"{direito['nome']}: {direito['frequencia']} menções "
                  f"({direito['porcentagem']:.1f}%)")
        
        print("\n📊 QUALIDADE DO PROCESSAMENTO")
        print("-" * 40)
        if qualidade.get('distribuicao_qualidade'):
            for nivel, dados in qualidade['distribuicao_qualidade'].items():
                print(f"{nivel.replace('_', ' ').title()}: {dados['quantidade']} "
                      f"({dados['porcentagem']:.1f}%)")
        
        print("\n✅ TAXA DE SUCESSO NLP")
        print("-" * 40)
        if qualidade.get('taxa_sucesso'):
            for componente, taxa in qualidade['taxa_sucesso'].items():
                print(f"{componente.title()}: {taxa:.1f}%")
        
        print(f"\n📅 Relatório gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def main():
    """Função principal - executa todos os exemplos"""
    print("🚀 EXEMPLOS DE USO DA API - AÇÕES COLETIVAS")
    print("=" * 60)
    
    # Verificar se a API está disponível
    try:
        client = APIClient()
        client.health_check()
    except Exception as e:
        print(f"❌ API não está disponível: {e}")
        print("\n💡 Para iniciar a API:")
        print("   python start_api.py")
        print("   ou")
        print("   python app.py")
        return
    
    # Executar exemplos
    exemplo_basico()
    exemplo_busca_avancada()
    exemplo_topicos_e_direitos()
    exemplo_estatisticas()
    exemplo_processo_especifico()
    exemplo_relatorio_completo()
    
    print("\n" + "=" * 60)
    print("🎉 EXEMPLOS CONCLUÍDOS")
    print("=" * 60)
    print("💡 Para mais informações:")
    print("   - Documentação: docs/API.md")
    print("   - Swagger UI: http://localhost:5000/api/docs/")
    print("   - Testes: python test_api.py")


if __name__ == "__main__":
    main() 