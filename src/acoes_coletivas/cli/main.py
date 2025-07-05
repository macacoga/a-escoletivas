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
            df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
            
            df.to_excel(output_file, index=False, engine='openpyxl')
            logger.info(f"Dados exportados para {output_file}")
            print(f"Dados exportados com sucesso para: {output_file}")
            
    except Exception as e:
        logger.error(f"Erro ao exportar dados: {e}")
        print(f"Erro: {e}")


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