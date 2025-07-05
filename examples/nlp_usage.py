#!/usr/bin/env python3
"""
Exemplo de uso do sistema de processamento de linguagem natural (NLP)
para análise de decisões judiciais trabalhistas
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.acoes_coletivas.database.manager import DatabaseManager
from src.acoes_coletivas.database.models import ProcessoJudicial, ResultadoNLP
from src.acoes_coletivas.nlp.nlp_pipeline import NLPPipeline
from src.acoes_coletivas.nlp.text_preprocessor import TextPreprocessor
from src.acoes_coletivas.nlp.entity_extractor import EntityExtractor
from src.acoes_coletivas.nlp.rights_analyzer import RightsAnalyzer
from src.acoes_coletivas.nlp.extractive_summarizer import ExtractiveSummarizer
from src.acoes_coletivas.config.settings import settings
from datetime import datetime
import json


def exemplo_texto_judicial():
    """Retorna um exemplo de texto de decisão judicial para teste"""
    return """
    TRIBUNAL REGIONAL DO TRABALHO DA 10ª REGIÃO
    VARA DO TRABALHO DE BRASÍLIA
    
    Processo nº 0001234-56.2023.5.10.0001
    
    RELATÓRIO
    
    Trata-se de reclamação trabalhista ajuizada por João Silva contra o Banco do Brasil S.A., 
    pleiteando o pagamento de horas extras, adicional noturno, equiparação salarial e 
    indenização por danos morais.
    
    O reclamante alega ter trabalhado para a reclamada por 5 anos, exercendo função de 
    operador de caixa, cumprindo jornada superior a 8 horas diárias sem o devido pagamento 
    das horas extraordinárias. Sustenta ainda que trabalhava em período noturno sem receber 
    o adicional devido.
    
    Pleiteia equiparação salarial com colega que exercia função idêntica, mas recebia 
    salário superior em R$ 2.000,00 mensais. Requer também indenização por danos morais 
    no valor de R$ 50.000,00 em razão de assédio moral sofrido.
    
    FUNDAMENTAÇÃO
    
    Analisando os autos e as provas produzidas, verifico que restou comprovado o trabalho 
    em sobrejornada pelo reclamante. Os cartões de ponto demonstram jornada habitual de 
    10 horas diárias, configurando 2 horas extras por dia.
    
    Quanto ao adicional noturno, ficou evidenciado que o autor trabalhava no período das 
    22h às 06h, fazendo jus ao adicional de 20% sobre o salário.
    
    A equiparação salarial procede parcialmente. Embora exercesse função similar, o 
    paradigma possuía maior tempo de serviço, justificando diferença salarial de R$ 500,00.
    
    Relativamente aos danos morais, não restou configurado o assédio alegado, sendo 
    improcedente este pedido.
    
    DISPOSITIVO
    
    Julgo PARCIALMENTE PROCEDENTE o pedido para condenar o Banco do Brasil S.A. ao 
    pagamento de:
    
    1. Horas extras no valor de R$ 15.000,00;
    2. Adicional noturno no valor de R$ 8.000,00;
    3. Diferenças salariais (equiparação) no valor de R$ 30.000,00;
    4. INDEFIRO o pedido de indenização por danos morais.
    
    Total da condenação: R$ 53.000,00
    
    Brasília, 15 de março de 2024.
    
    Dr. Maria Santos
    Juíza do Trabalho
    """


def exemplo_1_componentes_individuais():
    """Demonstra uso individual de cada componente do pipeline NLP"""
    print("="*80)
    print("EXEMPLO 1: USO DE COMPONENTES INDIVIDUAIS")
    print("="*80)
    
    texto = exemplo_texto_judicial()
    
    # 1. Pré-processamento de texto
    print("\n1. PRÉ-PROCESSAMENTO DE TEXTO")
    print("-" * 40)
    
    preprocessor = TextPreprocessor()
    texto_processado = preprocessor.preprocess_text(texto)
    
    print(f"Texto original: {len(texto)} caracteres")
    print(f"Texto processado: {len(texto_processado)} caracteres")
    
    # Validação da qualidade
    qualidade = preprocessor.validate_text_quality(texto_processado)
    print(f"Qualidade do texto: {qualidade['quality_score']:.2f}")
    print(f"Problemas encontrados: {qualidade['issues']}")
    
    # 2. Extração de entidades
    print("\n2. EXTRAÇÃO DE ENTIDADES NOMEADAS")
    print("-" * 40)
    
    entity_extractor = EntityExtractor()
    entities = entity_extractor.extract_entities(texto_processado)
    
    print(f"Entidades encontradas: {len(entities)}")
    for entity in entities[:10]:  # Mostrar apenas as primeiras 10
        print(f"  {entity.text} ({entity.label}) - Confiança: {entity.confidence:.2f}")
    
    # Análise por tipo
    analysis = entity_extractor.analyze_entities_by_type(entities)
    print(f"\nDistribuição por tipo:")
    for tipo, count in analysis.get('type_distribution', {}).items():
        print(f"  {tipo}: {count}")
    
    # 3. Análise de direitos trabalhistas
    print("\n3. ANÁLISE DE DIREITOS TRABALHISTAS")
    print("-" * 40)
    
    rights_analyzer = RightsAnalyzer()
    worker_rights = rights_analyzer.analyze_rights(texto_processado)
    
    print(f"Direitos identificados: {len(worker_rights)}")
    for right in worker_rights:
        print(f"  {right.description}")
        print(f"    Resultado: {right.decision_outcome or 'Indefinido'}")
        print(f"    Confiança: {right.confidence:.2f}")
        print(f"    Menções: {len(right.mentions)}")
    
    # 4. Resumo extrativo
    print("\n4. RESUMO EXTRATIVO")
    print("-" * 40)
    
    summarizer = ExtractiveSummarizer()
    summary = summarizer.create_summary(texto_processado, max_sentences=5, method='textrank')
    
    print(f"Método: {summary['method']}")
    print(f"Sentenças no resumo: {summary['sentence_count']}")
    print(f"Taxa de compressão: {summary.get('metrics', {}).get('compression_ratio', 'N/A')}")
    print(f"\nResumo:")
    print(summary['summary'][:500] + "..." if len(summary['summary']) > 500 else summary['summary'])


def exemplo_2_pipeline_completo():
    """Demonstra uso do pipeline completo de NLP"""
    print("\n\n" + "="*80)
    print("EXEMPLO 2: PIPELINE COMPLETO DE NLP")
    print("="*80)
    
    # Inicializar pipeline
    pipeline = NLPPipeline()
    
    # Validar pipeline
    print("\nValidando pipeline...")
    validation = pipeline.validate_pipeline()
    
    if not validation.get('pipeline_valid', False):
        print("❌ Pipeline inválido! Verifique as dependências.")
        failed_components = [comp for comp, status in validation.items() if not status and comp != 'pipeline_valid']
        print(f"Componentes com falha: {failed_components}")
        return
    
    print("✅ Pipeline validado com sucesso!")
    
    # Processar texto
    texto = exemplo_texto_judicial()
    resultado = pipeline.process_text(
        texto, 
        processo_id="exemplo_001",
        include_summary=True,
        include_entities=True,
        include_rights=True,
        summary_method='hybrid'
    )
    
    # Exibir resultados
    print(f"\n📄 RESULTADOS DO PROCESSAMENTO")
    print(f"Processo ID: {resultado.processo_id}")
    print(f"Tempo de processamento: {resultado.processing_time:.2f}s")
    print(f"Confiança global: {resultado.confidence_score:.2f}")
    print(f"Qualidade do texto: {resultado.text_quality.get('quality_score', 0):.2f}")
    
    print(f"\n🎯 ENTIDADES ENCONTRADAS ({len(resultado.entities)})")
    entity_types = {}
    for entity in resultado.entities:
        entity_types[entity.label] = entity_types.get(entity.label, 0) + 1
    
    for tipo, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tipo}: {count}")
    
    print(f"\n⚖️ DIREITOS TRABALHISTAS ({len(resultado.worker_rights)})")
    for right in resultado.worker_rights:
        status_icon = {"granted": "✅", "denied": "❌", "partially_granted": "⚠️"}.get(right.decision_outcome, "❓")
        print(f"  {status_icon} {right.description} (Confiança: {right.confidence:.2f})")
    
    print(f"\n📝 RESUMO")
    print(f"Método: {resultado.summary.get('method', 'N/A')}")
    print(f"Compressão: {resultado.summary.get('metrics', {}).get('compression_ratio', 'N/A')}")
    print(f"Conteúdo: {resultado.summary.get('summary', 'N/A')[:300]}...")
    
    return resultado


def exemplo_3_integracao_banco():
    """Demonstra integração com banco de dados"""
    print("\n\n" + "="*80)
    print("EXEMPLO 3: INTEGRAÇÃO COM BANCO DE DADOS")
    print("="*80)
    
    # Inicializar banco
    db = DatabaseManager("examples/exemplo_nlp.db")
    
    # Criar processo de exemplo
    processo = ProcessoJudicial(
        numero_processo="0001234-56.2023.5.10.0001",
        numero_processo_planilha="123456",
        tribunal="TRT10",
        classe_processo="Reclamação Trabalhista",
        tipo_documento="Sentença",
        data_julgamento="2024-03-15",
        data_publicacao="2024-03-16",
        relator="Maria Santos",
        partes="João Silva vs Banco do Brasil S.A.",
        link_decisao="https://exemplo.com/processo/123456",
        conteudo_bruto_decisao=exemplo_texto_judicial(),
        origem_texto="Exemplo",
        colecao_api="EXEMPLO",
        id_documento_api="EX123456"
    )
    
    # Inserir processo
    processo_id = db.insert_processo(processo)
    print(f"✅ Processo inserido com ID: {processo_id}")
    
    # Processar com NLP
    pipeline = NLPPipeline()
    
    print("🤖 Processando texto com NLP...")
    sucesso = db.processar_texto_nlp(processo_id, pipeline)
    
    if sucesso:
        print("✅ Processamento NLP concluído!")
        
        # Buscar resultado
        resultado_nlp = db.get_resultado_nlp_by_processo(processo_id)
        
        if resultado_nlp:
            print(f"\n📊 RESULTADO SALVO NO BANCO:")
            print(f"Qualidade: {resultado_nlp.qualidade_texto:.2f}")
            print(f"Confiança: {resultado_nlp.confianca_global:.2f}")
            print(f"Tempo: {resultado_nlp.tempo_processamento:.2f}s")
            print(f"Método: {resultado_nlp.metodo_sumarizacao}")
            
            # Mostrar direitos trabalhistas
            if resultado_nlp.direitos_trabalhistas:
                try:
                    direitos = json.loads(resultado_nlp.direitos_trabalhistas)
                    print(f"\n⚖️ DIREITOS IDENTIFICADOS:")
                    for direito in direitos:
                        print(f"  • {direito.get('description', 'N/A')} - {direito.get('decision_outcome', 'N/A')}")
                except json.JSONDecodeError:
                    print("Erro ao decodificar direitos trabalhistas")
    else:
        print("❌ Erro no processamento NLP")
    
    # Estatísticas
    print(f"\n📈 ESTATÍSTICAS DO BANCO:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


def exemplo_4_processamento_lote():
    """Demonstra processamento em lote"""
    print("\n\n" + "="*80)
    print("EXEMPLO 4: PROCESSAMENTO EM LOTE")
    print("="*80)
    
    # Dados de exemplo
    textos_exemplo = [
        {
            'text': exemplo_texto_judicial(),
            'processo_id': 'lote_001'
        },
        {
            'text': exemplo_texto_judicial().replace("João Silva", "Maria Oliveira").replace("R$ 53.000,00", "R$ 25.000,00"),
            'processo_id': 'lote_002'
        },
        {
            'text': exemplo_texto_judicial().replace("horas extras", "adicional de insalubridade").replace("Banco do Brasil", "Empresa XYZ"),
            'processo_id': 'lote_003'
        }
    ]
    
    # Processar em lote
    pipeline = NLPPipeline()
    
    print(f"🚀 Processando {len(textos_exemplo)} textos em lote...")
    resultados = pipeline.batch_process(textos_exemplo)
    
    print(f"✅ Processamento concluído! {len(resultados)} resultados gerados.")
    
    # Criar relatório
    relatorio = pipeline.create_analysis_report(resultados)
    
    print(f"\n📊 RELATÓRIO DE ANÁLISE:")
    print(f"Total de processos: {relatorio['general_stats']['total_processes']}")
    print(f"Tempo médio: {relatorio['general_stats']['avg_processing_time']:.2f}s")
    print(f"Confiança média: {relatorio['general_stats']['avg_confidence_score']:.2f}")
    
    print(f"\n🎯 ENTIDADES MAIS COMUNS:")
    for entity_type, count in list(relatorio['entity_stats']['entity_type_distribution'].items())[:5]:
        print(f"  {entity_type}: {count}")
    
    print(f"\n⚖️ DIREITOS MAIS IDENTIFICADOS:")
    for right_type, count in list(relatorio['rights_stats']['rights_type_distribution'].items())[:5]:
        print(f"  {right_type}: {count}")
    
    # Exportar resultados
    print(f"\n💾 Exportando resultados...")
    json_path = pipeline.export_results_to_json(resultados, "examples/resultados_lote.json")
    print(f"Resultados exportados para: {json_path}")


def main():
    """Função principal - executa todos os exemplos"""
    print("🤖 SISTEMA DE PROCESSAMENTO NLP PARA DECISÕES JUDICIAIS")
    print("Ferramenta de Análise de Ações Coletivas - Fase 2")
    
    try:
        # Executar exemplos
        exemplo_1_componentes_individuais()
        exemplo_2_pipeline_completo()
        exemplo_3_integracao_banco()
        exemplo_4_processamento_lote()
        
        print("\n\n" + "="*80)
        print("✅ TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!")
        print("="*80)
        
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("1. Instale as dependências: pip install -r requirements.txt")
        print("2. Instale o modelo spaCy: python install_spacy_model.py")
        print("3. Use o CLI: python acoes_coletivas.py nlp validate")
        print("4. Processe seus dados: python acoes_coletivas.py nlp process --limit 10")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        print("\nVerifique se:")
        print("1. Todas as dependências estão instaladas")
        print("2. O modelo spaCy está disponível")
        print("3. Execute: python install_spacy_model.py")


if __name__ == "__main__":
    main() 