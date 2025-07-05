#!/usr/bin/env python3
"""
Exemplo básico de uso da Ferramenta de Análise de Ações Coletivas
"""

import sys
from pathlib import Path

# Adicionar src ao Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from acoes_coletivas.database.manager import DatabaseManager
from acoes_coletivas.database.models import ProcessoJudicial, ResultadoNLP
from acoes_coletivas.config.settings import settings
from acoes_coletivas.utils.logging import setup_logging, get_logger
from acoes_coletivas.utils.excel_handler import ExcelHandler
from datetime import datetime


def main():
    """Exemplo básico de uso do sistema"""
    
    # Configurar logging
    setup_logging(level="INFO", json_format=False)
    logger = get_logger("BasicUsage")
    
    logger.info("Iniciando exemplo básico de uso")
    
    # 1. Inicializar o banco de dados
    logger.info("Inicializando banco de dados...")
    db = DatabaseManager()
    
    # 2. Criar um processo de exemplo
    logger.info("Criando processo de exemplo...")
    processo_exemplo = ProcessoJudicial(
        numero_processo="0001203-03.2018.5.10.0021",
        numero_processo_planilha="0001203-03.2018.5.10.0021",
        tribunal="TRT10",
        classe_processo="Reclamação Trabalhista",
        tipo_documento="Sentença",
        data_julgamento="2024-01-15",
        relator="Juiz Exemplo",
        partes="Fulano vs Banco do Brasil",
        conteudo_bruto_decisao="Exemplo de decisão judicial...",
        origem_texto="ementa",
        colecao_api="sentencas",
        id_documento_api="12345"
    )
    
    # 3. Salvar processo no banco
    processo_id = db.insert_processo(processo_exemplo)
    logger.info(f"Processo salvo com ID: {processo_id}")
    
    # 4. Criar resultado NLP de exemplo
    logger.info("Criando resultado NLP de exemplo...")
    resultado_nlp = ResultadoNLP(
        processo_id=processo_id,
        resumo_extrativo="Resumo automático da decisão judicial...",
        palavras_chave='["banco", "trabalhista", "indenização"]',
        tema_principal="Direito Trabalhista",
        sentimento="neutro"
    )
    
    # 5. Salvar resultado NLP
    resultado_id = db.insert_resultado_nlp(resultado_nlp)
    logger.info(f"Resultado NLP salvo com ID: {resultado_id}")
    
    # 6. Marcar processo como processado
    db.update_processo_processado(processo_id)
    logger.info("Processo marcado como processado")
    
    # 7. Verificar estatísticas
    logger.info("Verificando estatísticas do banco...")
    stats = db.get_stats()
    
    print("\n" + "="*50)
    print("ESTATÍSTICAS DO BANCO DE DADOS")
    print("="*50)
    print(f"Total de processos: {stats['total_processos']}")
    print(f"Processos processados: {stats['processos_processados']}")
    print(f"Resultados NLP: {stats['resultados_nlp']}")
    print(f"Total de logs: {stats['total_logs']}")
    print("="*50)
    
    # 8. Buscar o processo criado
    logger.info("Buscando processo criado...")
    processo_encontrado = db.get_processo_by_id(processo_id)
    
    if processo_encontrado:
        print(f"\nProcesso encontrado: {processo_encontrado.numero_processo}")
        print(f"Tribunal: {processo_encontrado.tribunal}")
        print(f"Processado NLP: {processo_encontrado.processado_nlp}")
    
    # 9. Buscar resultado NLP
    logger.info("Buscando resultado NLP...")
    resultado_encontrado = db.get_resultado_nlp_by_processo(processo_id)
    
    if resultado_encontrado:
        print(f"\nResumo: {resultado_encontrado.resumo_extrativo}")
        print(f"Tema: {resultado_encontrado.tema_principal}")
    
    # 10. Exemplo de manipulação de Excel
    logger.info("Demonstrando manipulação de Excel...")
    excel_handler = ExcelHandler()
    
    # Verificar se existe arquivo de teste
    if Path("TESTE.xlsx").exists():
        try:
            info = excel_handler.get_excel_info("TESTE.xlsx")
            print(f"\nInformações do arquivo TESTE.xlsx:")
            print(f"Linhas: {info['total_rows']}")
            print(f"Colunas: {info['total_columns']}")
            print(f"Nomes das colunas: {info['column_names']}")
        except Exception as e:
            logger.error(f"Erro ao processar Excel: {e}")
    
    logger.info("Exemplo concluído com sucesso!")


if __name__ == "__main__":
    main() 