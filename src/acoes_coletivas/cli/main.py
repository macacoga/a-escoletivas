"""
Interface de linha de comando para a Ferramenta de Análise de Ações Coletivas
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.acoes_coletivas.database.manager import DatabaseManager
from src.acoes_coletivas.config.settings import settings
from src.acoes_coletivas.utils.logging import setup_logging, get_logger
from src.acoes_coletivas.utils.excel_handler import ExcelHandler
from src.acoes_coletivas.nlp.nlp_pipeline import NLPPipeline


def setup_cli_logging():
    """Configura o logging para CLI"""
    setup_logging(
        level=settings.log_level,
        log_file=settings.log_file,
        json_format=False  # Formato mais legível para CLI
    )


def init_database():
    """Inicializa o banco de dados"""
    logger = get_logger("CLI")
    logger.info("Inicializando banco de dados...")
    
    db = DatabaseManager(str(settings.database_url.replace("sqlite:///", "")))
    logger.info("Banco de dados inicializado com sucesso!")
    
    return db


def show_stats(db: DatabaseManager):
    """Exibe estatísticas do banco de dados"""
    logger = get_logger("CLI")
    stats = db.get_stats()
    
    print("\n" + "="*50)
    print("ESTATÍSTICAS DO BANCO DE DADOS")
    print("="*50)
    print(f"Total de processos: {stats['total_processos']}")
    print(f"Processos processados: {stats['processos_processados']}")
    print(f"Resultados NLP: {stats['resultados_nlp']}")
    print(f"Total de logs: {stats['total_logs']}")
    print(f"Tribunais únicos: {stats['tribunais_unicos']}")
    print(f"Última coleta: {stats['ultima_coleta'] or 'N/A'}")
    print("="*50)


def import_excel(db: DatabaseManager, excel_file: str, column_name: str):
    """Importa processos de arquivo Excel"""
    logger = get_logger("CLI")
    
    try:
        handler = ExcelHandler()
        processos = handler.read_processo_numbers(excel_file, column_name)
        
        logger.info(f"Encontrados {len(processos)} processos no arquivo Excel")
        
        # Aqui você implementaria a lógica de scraping
        # Por ora, apenas mostramos as informações
        print(f"\nProcessos encontrados: {len(processos)}")
        for i, processo in enumerate(processos[:5]):  # Mostra apenas os primeiros 5
            print(f"{i+1}. {processo}")
        
        if len(processos) > 5:
            print(f"... e mais {len(processos) - 5} processos")
        
        print(f"\nPara processar estes dados, use o comando 'scrape'")
        
    except Exception as e:
        logger.error(f"Erro ao importar Excel: {e}")
        print(f"Erro: {e}")


def export_data(db: DatabaseManager, output_file: str):
    """Exporta dados do banco para Excel"""
    logger = get_logger("CLI")
    
    try:
        # Buscar todos os processos
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    pj.*,
                    rn.resumo_extrativo,
                    rn.palavras_chave,
                    rn.tema_principal
                FROM processos_judiciais pj
                LEFT JOIN resultados_nlp rn ON pj.id = rn.processo_id
            """)
            
            import pandas as pd
            columns = pd.Index([str(desc[0]) for desc in cursor.description])
            df = pd.DataFrame(cursor.fetchall(), columns=columns)
            
            df.to_excel(output_file, index=False, engine='openpyxl')
            logger.info(f"Dados exportados para {output_file}")
            print(f"Dados exportados com sucesso para: {output_file}")
            
    except Exception as e:
        logger.error(f"Erro ao exportar dados: {e}")
        print(f"Erro: {e}")


def process_nlp(db: DatabaseManager, process_id: Optional[int] = None, limit: int = 10):
    """Processa textos através do pipeline NLP"""
    logger = get_logger("CLI")
    
    try:
        # Inicializar pipeline
        print("Inicializando pipeline NLP...")
        pipeline = NLPPipeline()
        
        # Validar pipeline
        print("Validando componentes do pipeline...")
        validation = pipeline.validate_pipeline()
        
        if not validation['pipeline_valid']:
            print("❌ Erro: Pipeline NLP inválido!")
            failed_components = [comp for comp, status in validation.items() if not status]
            print(f"Componentes com falha: {failed_components}")
            return
        
        print("✅ Pipeline NLP validado com sucesso!")
        
        if process_id:
            # Processar processo específico
            print(f"Processando processo ID: {process_id}")
            success = db.processar_texto_nlp(process_id, pipeline)
            
            if success:
                print("✅ Processo processado com sucesso!")
            else:
                print("❌ Erro ao processar processo")
        else:
            # Processar lote
            print(f"Processando lote de {limit} processos...")
            result = db.processar_lote_nlp(pipeline, limit)
            
            if 'error' in result:
                print(f"❌ Erro: {result['error']}")
            else:
                print(f"✅ Processamento concluído!")
                print(f"   Total: {result['total_processos']}")
                print(f"   Sucessos: {result['sucessos']}")
                print(f"   Erros: {result['erros']}")
                print(f"   Taxa de sucesso: {result['taxa_sucesso']:.1%}")
                
    except Exception as e:
        logger.error(f"Erro no processamento NLP: {e}")
        print(f"Erro: {e}")


def show_nlp_stats(db: DatabaseManager):
    """Exibe estatísticas detalhadas de NLP"""
    logger = get_logger("CLI")
    
    try:
        stats = db.get_nlp_stats()
        
        print("\n" + "="*60)
        print("ESTATÍSTICAS DETALHADAS DE NLP")
        print("="*60)
        
        if stats.get('total_resultados', 0) > 0:
            print(f"Total de resultados NLP: {stats['total_resultados']}")
            print(f"Qualidade média: {stats['qualidade_media']:.2f}")
            print(f"Confiança média: {stats['confianca_media']:.2f}")
            print(f"Tempo médio de processamento: {stats['tempo_medio']:.2f}s")
            print(f"Primeiro processamento: {stats['primeiro_processamento']}")
            print(f"Último processamento: {stats['ultimo_processamento']}")
            
            # Métodos de sumarização
            if 'metodos_sumarizacao' in stats:
                print(f"\nMétodos de sumarização:")
                for method, count in stats['metodos_sumarizacao'].items():
                    print(f"  {method}: {count}")
            
            # Distribuição de qualidade
            if 'distribuicao_qualidade' in stats:
                print(f"\nDistribuição de qualidade:")
                qual_dist = stats['distribuicao_qualidade']
                print(f"  Alta qualidade (≥0.8): {qual_dist.get('alta_qualidade', 0)}")
                print(f"  Média qualidade (0.5-0.8): {qual_dist.get('media_qualidade', 0)}")
                print(f"  Baixa qualidade (<0.5): {qual_dist.get('baixa_qualidade', 0)}")
        else:
            print("Nenhum resultado de NLP encontrado.")
            print("Execute 'nlp process' para processar textos.")
        
        print("="*60)
        
    except Exception as e:
        logger.error(f"Erro ao exibir estatísticas NLP: {e}")
        print(f"Erro: {e}")


def export_nlp_results(db: DatabaseManager, output_file: str):
    """Exporta resultados de NLP para JSON"""
    logger = get_logger("CLI")
    
    try:
        print("Exportando resultados de NLP...")
        filepath = db.export_nlp_results(output_file)
        print(f"✅ Resultados exportados para: {filepath}")
        
    except Exception as e:
        logger.error(f"Erro ao exportar resultados NLP: {e}")
        print(f"Erro: {e}")


def validate_nlp_pipeline():
    """Valida o pipeline NLP"""
    logger = get_logger("CLI")
    
    try:
        print("Validando pipeline NLP...")
        pipeline = NLPPipeline()
        
        validation = pipeline.validate_pipeline()
        
        print("\n" + "="*50)
        print("VALIDAÇÃO DO PIPELINE NLP")
        print("="*50)
        
        for component, status in validation.items():
            if component == 'pipeline_valid':
                continue
                
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {component}")
        
        print("-" * 50)
        
        if validation['pipeline_valid']:
            print("✅ Pipeline NLP está funcionando corretamente!")
        else:
            print("❌ Pipeline NLP tem problemas!")
            print("\nPossíveis soluções:")
            print("1. Instale as dependências: pip install -r requirements.txt")
            print("2. Instale o modelo spaCy: python install_spacy_model.py")
            print("3. Verifique se todas as dependências estão instaladas")
        
        print("="*50)
        
    except Exception as e:
        logger.error(f"Erro na validação do pipeline: {e}")
        print(f"Erro: {e}")
        print("\nCertifique-se de que:")
        print("1. O modelo spaCy está instalado")
        print("2. Todas as dependências estão instaladas")
        print("3. Execute: python install_spacy_model.py")


def main():
    """Função principal do CLI"""
    parser = argparse.ArgumentParser(
        description="Ferramenta de Análise de Ações Coletivas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s stats                          # Exibe estatísticas
  %(prog)s import -f dados.xlsx -c numero # Importa processos do Excel
  %(prog)s export -o resultado.xlsx       # Exporta dados para Excel
  %(prog)s init                           # Inicializa banco de dados
  
  %(prog)s nlp validate                   # Valida pipeline NLP
  %(prog)s nlp process --limit 50         # Processa 50 textos com NLP
  %(prog)s nlp process --id 123           # Processa processo específico
  %(prog)s nlp stats                      # Estatísticas detalhadas de NLP
  %(prog)s nlp export -o resultados.json  # Exporta resultados NLP
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando: stats
    stats_parser = subparsers.add_parser('stats', help='Exibe estatísticas do banco de dados')
    
    # Comando: import
    import_parser = subparsers.add_parser('import', help='Importa processos de arquivo Excel')
    import_parser.add_argument('-f', '--file', required=True, help='Arquivo Excel')
    import_parser.add_argument('-c', '--column', required=True, help='Nome da coluna com números de processo')
    
    # Comando: export
    export_parser = subparsers.add_parser('export', help='Exporta dados para Excel')
    export_parser.add_argument('-o', '--output', required=True, help='Arquivo de saída')
    
    # Comando: init
    init_parser = subparsers.add_parser('init', help='Inicializa banco de dados')
    
    # Comando: scrape
    scrape_parser = subparsers.add_parser('scrape', help='Executa coleta de dados')
    scrape_parser.add_argument('-f', '--file', help='Arquivo Excel com processos')
    scrape_parser.add_argument('-c', '--column', help='Nome da coluna com números de processo')
    scrape_parser.add_argument('--headless', action='store_true', help='Executa em modo headless')
    
    # Comandos NLP
    nlp_parser = subparsers.add_parser('nlp', help='Comandos de processamento NLP')
    nlp_subparsers = nlp_parser.add_subparsers(dest='nlp_command', help='Comandos NLP disponíveis')
    
    # nlp process
    nlp_process_parser = nlp_subparsers.add_parser('process', help='Processa textos através do pipeline NLP')
    nlp_process_parser.add_argument('--id', type=int, help='ID do processo específico para processar')
    nlp_process_parser.add_argument('--limit', type=int, default=10, help='Número máximo de processos para processar em lote')
    
    # nlp stats
    nlp_stats_parser = nlp_subparsers.add_parser('stats', help='Exibe estatísticas detalhadas de NLP')
    
    # nlp export
    nlp_export_parser = nlp_subparsers.add_parser('export', help='Exporta resultados de NLP para JSON')
    nlp_export_parser.add_argument('-o', '--output', required=True, help='Arquivo de saída JSON')
    
    # nlp validate
    nlp_validate_parser = nlp_subparsers.add_parser('validate', help='Valida o pipeline NLP')
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_cli_logging()
    logger = get_logger("CLI")
    
    # Mostrar cabeçalho
    print("\n" + "="*60)
    print("FERRAMENTA DE ANÁLISE DE AÇÕES COLETIVAS")
    print("="*60)
    
    try:
        if args.command == 'init':
            db = init_database()
            print("Banco de dados inicializado com sucesso!")
            
        elif args.command == 'stats':
            db = init_database()
            show_stats(db)
            
        elif args.command == 'import':
            db = init_database()
            import_excel(db, args.file, args.column)
            
        elif args.command == 'export':
            db = init_database()
            export_data(db, args.output)
            
        elif args.command == 'scrape':
            print("Funcionalidade de scraping em desenvolvimento!")
            print("Use os scripts legados por enquanto:")
            print("- 1 - extrair dados selenium.py")
            print("- 1.1 - extrair dados.py")
            
        elif args.command == 'nlp':
            db = init_database()
            
            if args.nlp_command == 'process':
                process_nlp(db, args.id, args.limit)
                
            elif args.nlp_command == 'stats':
                show_nlp_stats(db)
                
            elif args.nlp_command == 'export':
                export_nlp_results(db, args.output)
                
            elif args.nlp_command == 'validate':
                validate_nlp_pipeline()
                
            else:
                nlp_parser.print_help()
            
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        logger.info("Operação cancelada pelo usuário")
        print("\nOperação cancelada pelo usuário.")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        print(f"Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 