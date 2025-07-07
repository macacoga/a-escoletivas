#!/usr/bin/env python3
"""
Demonstração dos Resumos Inteligentes da API
"""

import requests
import json
from typing import Dict, Any

class DemoResumos:
    """Demonstração dos recursos de resumo"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        
    def print_header(self, title: str):
        """Imprime cabeçalho formatado"""
        print("\n" + "=" * 60)
        print(f"📋 {title}")
        print("=" * 60)
    
    def print_section(self, title: str):
        """Imprime seção formatada"""
        print(f"\n🔍 {title}")
        print("-" * 40)
    
    def fazer_requisicao(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Faz requisição à API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
                return {}
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
            return {}
    
    def demo_resumo_individual(self):
        """Demonstra resumo individual"""
        self.print_header("RESUMO INDIVIDUAL DE PROCESSO")
        
        # Buscar um processo processado pelo NLP
        print("Buscando processo processado pelo NLP...")
        acoes = self.fazer_requisicao('/api/acoes', {'per_page': 10})
        
        if not acoes.get('data'):
            print("❌ Nenhum processo encontrado")
            return
        
        # Encontrar processo com NLP
        processo_id = None
        numero_processo = None
        
        for acao in acoes['data']:
            if acao.get('processado_nlp'):
                processo_id = acao['id']
                numero_processo = acao['numero_processo']
                break
        
        if not processo_id:
            # Usar o primeiro disponível
            processo_id = acoes['data'][0]['id']
            numero_processo = acoes['data'][0]['numero_processo']
            print("⚠️  Usando processo sem NLP para demonstração")
        
        print(f"✅ Processo selecionado: {numero_processo} (ID: {processo_id})")
        
        # Buscar resumo
        self.print_section("RESUMO RÁPIDO")
        resumo = self.fazer_requisicao(f'/api/acoes/{processo_id}/resumo')
        
        if resumo:
            print(f"📄 Processo: {resumo.get('processo', 'N/A')}")
            print(f"🏛️  Tribunal: {resumo.get('tribunal', 'N/A')}")
            print(f"📋 Tipo: {resumo.get('tipo_documento', 'N/A')}")
            print(f"⚖️  Resultado: {resumo.get('resultado_principal', 'N/A')}")
            print(f"💰 Valor: {resumo.get('valor_total', 'N/A')}")
            print(f"📊 Qualidade: {resumo.get('qualidade_analise', 'N/A')}")
            print(f"🎯 Confiança: {resumo.get('confianca_percentual', 'N/A')}")
            
            if resumo.get('principais_direitos'):
                print(f"⚖️  Direitos: {', '.join(resumo['principais_direitos'])}")
            
            print(f"\n📝 RESUMO COMPLETO:")
            print(f"{resumo.get('resumo_rapido', 'Resumo não disponível')}")
            
            if resumo.get('data_julgamento'):
                print(f"\n📅 Data do julgamento: {resumo['data_julgamento']}")
            
            if resumo.get('relator'):
                print(f"👨‍⚖️ Relator: {resumo['relator']}")
        else:
            print("❌ Não foi possível obter o resumo")
    
    def demo_resumos_lote(self):
        """Demonstra resumos em lote"""
        self.print_header("RESUMOS EM LOTE")
        
        print("Buscando resumos de múltiplos processos...")
        resumos = self.fazer_requisicao('/api/acoes/resumos', {'per_page': 5})
        
        if resumos.get('data'):
            print(f"✅ Encontrados {len(resumos['data'])} resumos")
            print(f"📊 Total disponível: {resumos.get('total_found', 0)}")
            
            self.print_section("LISTA DE RESUMOS")
            
            for i, resumo in enumerate(resumos['data'], 1):
                print(f"\n{i}. 📄 {resumo.get('processo', 'N/A')}")
                print(f"   🏛️  {resumo.get('tribunal', 'N/A')} - {resumo.get('tipo_documento', 'N/A')}")
                print(f"   🎯 Tema: {resumo.get('tema_principal', 'N/A')}")
                print(f"   📊 Qualidade: {resumo.get('qualidade_analise', 'N/A')} ({resumo.get('confianca_percentual', 'N/A')})")
                print(f"   🔗 Link: {resumo.get('link_resumo_completo', 'N/A')}")
        else:
            print("❌ Nenhum resumo encontrado")
    
    def demo_resumos_filtrados(self):
        """Demonstra resumos filtrados"""
        self.print_header("RESUMOS FILTRADOS")
        
        # Filtrar por tribunal
        self.print_section("FILTRO POR TRIBUNAL (TRT)")
        resumos_trt = self.fazer_requisicao('/api/acoes/resumos', {
            'tribunal': 'TRT',
            'per_page': 3
        })
        
        if resumos_trt.get('data'):
            print(f"✅ Encontrados {len(resumos_trt['data'])} processos do TRT")
            
            for resumo in resumos_trt['data']:
                print(f"📄 {resumo.get('processo', 'N/A')} - {resumo.get('tribunal', 'N/A')}")
                print(f"   🎯 {resumo.get('tema_principal', 'N/A')}")
        else:
            print("❌ Nenhum processo do TRT encontrado")
        
        # Filtrar por tema
        self.print_section("FILTRO POR TEMA")
        resumos_tema = self.fazer_requisicao('/api/acoes/resumos', {
            'tema': 'horas',
            'per_page': 2
        })
        
        if resumos_tema.get('data'):
            print(f"✅ Encontrados {len(resumos_tema['data'])} processos sobre o tema")
            
            for resumo in resumos_tema['data']:
                print(f"📄 {resumo.get('processo', 'N/A')}")
                print(f"   🎯 {resumo.get('tema_principal', 'N/A')}")
        else:
            print("❌ Nenhum processo com esse tema encontrado")
    
    def demo_comparacao_apis(self):
        """Demonstra comparação entre APIs"""
        self.print_header("COMPARAÇÃO: DADOS COMPLETOS vs RESUMO")
        
        # Buscar um processo
        acoes = self.fazer_requisicao('/api/acoes', {'per_page': 1})
        
        if not acoes.get('data'):
            print("❌ Nenhum processo encontrado")
            return
        
        processo_id = acoes['data'][0]['id']
        numero_processo = acoes['data'][0]['numero_processo']
        
        print(f"📄 Comparando processo: {numero_processo}")
        
        # API completa
        self.print_section("API COMPLETA (/api/acoes/{id})")
        dados_completos = self.fazer_requisicao(f'/api/acoes/{processo_id}')
        
        if dados_completos:
            print(f"📊 Tamanho da resposta: ~{len(json.dumps(dados_completos))} caracteres")
            print("📋 Campos disponíveis:")
            for campo in sorted(dados_completos.keys()):
                valor = dados_completos[campo]
                if isinstance(valor, str) and len(valor) > 50:
                    print(f"   - {campo}: {valor[:47]}...")
                else:
                    print(f"   - {campo}: {valor}")
        
        # API de resumo
        self.print_section("API DE RESUMO (/api/acoes/{id}/resumo)")
        resumo = self.fazer_requisicao(f'/api/acoes/{processo_id}/resumo')
        
        if resumo:
            print(f"📊 Tamanho da resposta: ~{len(json.dumps(resumo))} caracteres")
            print("📋 Resumo estruturado:")
            print(f"   📄 Processo: {resumo.get('processo', 'N/A')}")
            print(f"   ⚖️  Resultado: {resumo.get('resultado_principal', 'N/A')}")
            print(f"   💰 Valor: {resumo.get('valor_total', 'N/A')}")
            print(f"   📝 Resumo: {resumo.get('resumo_rapido', 'N/A')[:100]}...")
    
    def executar_demo_completa(self):
        """Executa demonstração completa"""
        print("🚀 DEMONSTRAÇÃO DOS RESUMOS INTELIGENTES")
        print("=" * 60)
        print("Esta demonstração mostra como usar os novos endpoints de resumo")
        print("para obter informações condensadas e úteis dos processos jurídicos.")
        
        try:
            # Verificar se API está rodando
            health = self.fazer_requisicao('/health')
            if not health:
                print("❌ API não está rodando. Execute: python start_api.py")
                return
            
            print("✅ API está rodando!")
            
            # Executar demonstrações
            self.demo_resumo_individual()
            self.demo_resumos_lote()
            self.demo_resumos_filtrados()
            self.demo_comparacao_apis()
            
            # Conclusão
            self.print_header("CONCLUSÃO")
            print("✅ Demonstração concluída!")
            print("\n📚 ENDPOINTS DISPONÍVEIS:")
            print("   - GET /api/acoes/{id}/resumo - Resumo individual")
            print("   - GET /api/acoes/resumos - Resumos em lote")
            print("   - GET /api/acoes/resumos?tribunal=TRT - Filtrados por tribunal")
            print("   - GET /api/acoes/resumos?tema=horas - Filtrados por tema")
            print("\n💡 CASOS DE USO:")
            print("   - Dashboards executivos")
            print("   - Relatórios rápidos")
            print("   - Análise de tendências")
            print("   - Sistemas de alerta")
            print("   - Integração com outras ferramentas")
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Demonstração interrompida pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro durante a demonstração: {e}")


def main():
    """Função principal"""
    demo = DemoResumos()
    demo.executar_demo_completa()


if __name__ == "__main__":
    main() 