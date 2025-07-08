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
    
    # Obter estatísticas adicionais de scraping
    processos_sem_conteudo = db.get_processos_sem_conteudo(limit=10000)  # Limite alto para contar todos
    processos_com_conteudo_nao_processados = db.get_processos_nao_processados(limit=10000)
    
    pendentes_scrape = len(processos_sem_conteudo)
    pendentes_nlp = len(processos_com_conteudo_nao_processados)
    
    print("\n" + "="*50)
    print("ESTATÍSTICAS DO BANCO DE DADOS")
    print("="*50)
    print(f"Total de processos: {stats['total_processos']}")
    print(f"Processos processados: {stats['processos_processados']}")
    print(f"Resultados NLP: {stats['resultados_nlp']}")
    print(f"Pendentes para scrape: {pendentes_scrape}")
    print(f"Pendentes para NLP: {pendentes_nlp}")
    print(f"Total de logs: {stats['total_logs']}")
    print(f"Tribunais únicos: {stats['tribunais_unicos']}")
    print(f"Última coleta: {stats['ultima_coleta'] or 'N/A'}")
    
    # Mostrar próximos passos se houver pendências
    if pendentes_scrape > 0:
        print(f"\n💡 Próximos passos:")
        print(f"   Execute: python acoes_coletivas.py scrape --limit {min(pendentes_scrape, 50)}")
    elif pendentes_nlp > 0:
        print(f"\n💡 Próximos passos:")
        print(f"   Execute: python acoes_coletivas.py nlp process --limit {min(pendentes_nlp, 20)}")
    else:
        print(f"\n✅ Todos os processos estão atualizados!")
    
    print("="*50)


def import_excel(db: DatabaseManager, excel_file: str, column_name: str):
    """Importa processos de arquivo Excel ou CSV com filtros específicos"""
    logger = get_logger("CLI")
    
    try:
        from ..database.models import ProcessoJudicial
        
        handler = ExcelHandler()
        
        # Aplicar filtros específicos: polo_ativo contendo "SIND" (em JSON) e uf_oj igual a "DF"
        filters = {
            'polo_ativo': {'json_contains': 'SIND'},
            'uf_oj': {'equals': 'DF'}
        }
        
        print(f"📋 Aplicando filtros:")
        print(f"   • polo_ativo: contém 'SIND' (em JSON)")
        print(f"   • uf_oj: igual a 'DF'")
        
        processos = handler.read_filtered_processo_numbers(excel_file, column_name, filters)
        
        logger.info(f"Encontrados {len(processos)} processos no arquivo após filtros")
        
        print(f"\nProcessos encontrados após filtros: {len(processos)}")
        for i, processo in enumerate(processos[:5]):  # Mostra apenas os primeiros 5
            print(f"{i+1}. {processo}")
        
        if len(processos) > 5:
            print(f"... e mais {len(processos) - 5} processos")
        
        if len(processos) == 0:
            print("\n⚠️  Nenhum processo encontrado com os filtros aplicados!")
            print("   Verifique se as colunas 'polo_ativo' e 'uf_oj' existem no arquivo")
            print("   e se existem processos com polo_ativo iniciando com 'SIND' e uf_oj = 'DF'")
            return
        
        # Salvar os números de processo no banco como registros "vazios"
        print(f"\n💾 Salvando processos no banco de dados...")
        
        processos_salvos = 0
        processos_existentes = 0
        
        for numero_processo in processos:
            try:
                # Verificar se já existe (usando numero_processo_planilha como chave única)
                if not db.processo_existe(numero_processo, "import_placeholder"):
                    # Criar registro vazio para ser preenchido pelo scraper
                    processo = ProcessoJudicial(
                        numero_processo="",  # Será preenchido pelo scraper
                        numero_processo_planilha=numero_processo,
                        tribunal="",  # Será preenchido pelo scraper
                        classe_processo="",
                        tipo_documento="",
                        data_julgamento="",
                        data_publicacao="",
                        relator="",
                        partes="",
                        link_decisao="",
                        conteudo_bruto_decisao="",  # Campo vazio indica que precisa de scraping
                        origem_texto="Importação CSV/Excel - Filtrado (SIND/DF)",
                        colecao_api="",
                        id_documento_api="import_placeholder",
                        metadados=f'{{"fonte": "{excel_file}", "coluna": "{column_name}", "filtros": {{"polo_ativo": "SIND (JSON)", "uf_oj": "DF"}}}}'
                    )
                    
                    db.insert_processo(processo)
                    processos_salvos += 1
                else:
                    processos_existentes += 1
                    
            except Exception as e:
                logger.error(f"Erro ao salvar processo {numero_processo}: {e}")
                continue
        
        print(f"✅ Importação concluída!")
        print(f"   📊 Processos salvos: {processos_salvos}")
        if processos_existentes > 0:
            print(f"   🔄 Processos já existentes: {processos_existentes}")
        
        print(f"\n🔄 Próximos passos:")
        print(f"   1. Execute 'python acoes_coletivas.py scrape' para coletar dados completos")
        print(f"   2. Execute 'python acoes_coletivas.py nlp process' para processar com NLP")
        
    except Exception as e:
        logger.error(f"Erro ao importar arquivo: {e}")
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


def process_nlp(db: DatabaseManager, process_id: Optional[int] = None, process_ids: Optional[List[int]] = None, limit: int = 10):
    """Processa textos através do pipeline NLP aprimorado"""
    logger = get_logger("CLI")
    
    try:
        # Inicializar pipeline
        print("🤖 Inicializando pipeline NLP aprimorado...")
        pipeline = NLPPipeline()
        
        # Validar pipeline
        print("🔍 Validando componentes do pipeline aprimorado...")
        validation = pipeline.validate_pipeline()
        
        if not validation['pipeline_valid']:
            print("❌ Erro: Pipeline NLP inválido!")
            failed_components = [comp for comp, status in validation.items() if not status]
            print(f"Componentes com falha: {failed_components}")
            return
        
        print("✅ Pipeline NLP aprimorado validado com sucesso!")
        print("🚀 Recursos disponíveis:")
        print("   • Extração de entidades nomeadas")
        print("   • Análise de direitos trabalhistas")
        print("   • Extração de partes do processo")
        print("   • Extração de referências legislativas")
        print("   • Resumo estruturado")
        print("   • Análise de valores monetários")
        
        if process_ids:
            # Processar múltiplos processos específicos
            print(f"Processando {len(process_ids)} processos específicos: {process_ids}")
            
            sucessos = 0
            erros = 0
            
            for pid in process_ids:
                try:
                    print(f"  Processando processo ID: {pid}")
                    success = db.processar_texto_nlp(pid, pipeline)
                    
                    if success:
                        print(f"  ✅ Processo {pid} processado com sucesso!")
                        sucessos += 1
                    else:
                        print(f"  ❌ Erro ao processar processo {pid}")
                        erros += 1
                        
                except Exception as e:
                    print(f"  ❌ Erro ao processar processo {pid}: {e}")
                    erros += 1
                    
            print(f"\n📊 Resumo do processamento:")
            print(f"   Total: {len(process_ids)}")
            print(f"   Sucessos: {sucessos}")
            print(f"   Erros: {erros}")
            
        elif process_id:
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
            elif 'message' in result:
                print(f"ℹ️ {result['message']}")
                print("💡 Importe processos primeiro com: python acoes_coletivas.py import -f arquivo.csv -c coluna")
            else:
                print(f"✅ Processamento concluído!")
                print(f"   Total: {result.get('total_processos', 0)}")
                print(f"   Sucessos: {result.get('sucessos', 0)}")
                print(f"   Erros: {result.get('erros', 0)}")
                
                # Mostrar estatísticas atualizadas
                show_nlp_stats(db)
        
    except Exception as e:
        logger.error(f"Erro no processamento NLP: {e}")
        print(f"Erro: {e}")


def show_nlp_stats(db: DatabaseManager):
    """Exibe estatísticas detalhadas de NLP aprimorado"""
    logger = get_logger("CLI")
    
    try:
        stats = db.get_nlp_stats()
        
        print("\n" + "="*60)
        print("ESTATÍSTICAS DETALHADAS DE NLP APRIMORADO")
        print("="*60)
        print(f"📊 Total de processos: {stats.get('total_processos', 0)}")
        print(f"🤖 Processos com NLP: {stats.get('processos_com_nlp', 0)}")
        print(f"📈 Taxa de cobertura: {stats.get('taxa_cobertura', 0):.1f}%")
        print(f"🎯 Qualidade média: {stats.get('qualidade_media', 0):.3f}")
        print(f"✅ Confiança média: {stats.get('confianca_media', 0):.3f}")
        print(f"⏱️ Tempo médio: {stats.get('tempo_medio', 0):.2f}s")
        
        # Métodos de sumarização
        if 'metodos_sumarizacao' in stats and stats['metodos_sumarizacao']:
            print(f"\n📝 Métodos de sumarização:")
            for metodo, count in stats['metodos_sumarizacao'].items():
                print(f"  • {metodo}: {count}")
        
        # Temas mais comuns
        if 'temas_comuns' in stats and stats['temas_comuns']:
            print(f"\n🏷️ Temas mais comuns:")
            for tema, count in stats['temas_comuns'][:5]:
                print(f"  • {tema}: {count}")
        
        # Tribunais
        if 'tribunais_distribuicao' in stats and stats['tribunais_distribuicao']:
            print(f"\n⚖️ Distribuição por tribunal:")
            for tribunal, count in stats['tribunais_distribuicao'][:5]:
                print(f"  • {tribunal}: {count}")
        
        print("="*60)
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas NLP: {e}")
        print(f"Erro: {e}")


def export_nlp_results(db: DatabaseManager, output_file: str):
    """Exporta resultados de NLP para JSON"""
    logger = get_logger("CLI")
    
    try:
        result_file = db.export_nlp_results(output_file)
        print(f"Resultados NLP exportados para: {result_file}")
        
    except Exception as e:
        logger.error(f"Erro ao exportar resultados NLP: {e}")
        print(f"Erro: {e}")


def validate_nlp_pipeline():
    """Valida o pipeline NLP aprimorado"""
    logger = get_logger("CLI")
    
    try:
        print("🔍 Validando pipeline NLP aprimorado...")
        pipeline = NLPPipeline()
        
        validation = pipeline.validate_pipeline()
        
        print("\n" + "="*50)
        print("VALIDAÇÃO DO PIPELINE NLP APRIMORADO")
        print("="*50)
        
        # Componentes básicos
        print("📋 COMPONENTES BÁSICOS:")
        basic_components = ['text_preprocessor', 'entity_extractor', 'rights_analyzer', 'extractive_summarizer']
        for component in basic_components:
            status = validation.get(component, False)
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component}: {'OK' if status else 'FALHA'}")
        
        # Componentes aprimorados
        print("\n🚀 COMPONENTES APRIMORADOS:")
        enhanced_components = ['parts_extractor', 'legal_references_extractor', 'structured_summarizer']
        for component in enhanced_components:
            status = validation.get(component, False)
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component}: {'OK' if status else 'FALHA'}")
        
        print("\n" + "="*50)
        overall_status = validation.get('pipeline_valid', False)
        status_icon = "✅" if overall_status else "❌"
        print(f"{status_icon} STATUS GERAL: {'VÁLIDO' if overall_status else 'INVÁLIDO'}")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Erro na validação do pipeline: {e}")
        print(f"Erro: {e}")
        print("\nCertifique-se de que:")
        print("1. O modelo spaCy está instalado")
        print("2. Todas as dependências estão instaladas")
        print("3. Execute: python install_spacy_model.py")


def scrape_data(db: DatabaseManager, limit: int = 100, collections: Optional[List[str]] = None):
    """Faz scraping dos processos importados"""
    logger = get_logger("CLI")
    
    try:
        from ..scraper.juristk_scraper import JurisprudenciaTrabalhoScraper
        from ..database.models import ProcessoJudicial
        
        # Buscar processos pendentes de coleta (sem conteúdo)
        processos_objetos = db.get_processos_sem_conteudo(limit)
        
        if not processos_objetos:
            print("🔍 Nenhum processo pendente de coleta encontrado")
            print("💡 Execute primeiro: python acoes_coletivas.py import -f arquivo.xlsx -c coluna")
            return
        
        # Extrair apenas os números dos processos
        processos_pendentes = [p.numero_processo_planilha for p in processos_objetos if p.numero_processo_planilha]
        
        print(f"🔍 Encontrados {len(processos_pendentes)} processos para coleta")
        print(f"📋 Primeiros 5 processos: {processos_pendentes[:5]}")
        
        # Inicializar scraper
        scraper = JurisprudenciaTrabalhoScraper()
        
        print("🚀 Inicializando scraper...")
        if not scraper.initialize_session():
            print("❌ Erro ao inicializar sessão do scraper")
            return
        
        # Definir coleções padrão se não especificadas
        if collections is None:
            collections = ['acordaos', 'decisoes', 'sentencas']
        
        print(f"📚 Coletando dados das coleções: {', '.join(collections)}")
        
        # Fazer scraping usando o novo método
        documentos = scraper.search_documents(processos_pendentes, batch_size=10)
        
        # Contar documentos coletados
        total_documentos = len(documentos)
        
        print(f"\n✅ Scraping concluído!")
        print(f"📊 Total de documentos coletados: {total_documentos}")
        print(f"🎯 Processos processados: {len(processos_pendentes)}")
        
        # Mostrar estatísticas do banco
        stats = db.get_stats()
        print(f"\n📈 Estatísticas do banco:")
        print(f"   Total de processos: {stats.get('total_processos', 0)}")
        print(f"   Processos com dados: {stats.get('processos_com_dados', 0)}")
        
    except Exception as e:
        logger.error(f"Erro durante scraping: {e}")
        print(f"❌ Erro: {e}")
    
    finally:
        # Garantir limpeza dos recursos
        if 'scraper' in locals():
            scraper.cleanup()


def reprocess_nlp(db: DatabaseManager, force: bool = False, limit: Optional[int] = None):
    """Reprocessa todos os textos que já foram processados com NLP"""
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
        
        # Buscar processos que já foram processados com NLP E que têm conteúdo válido para reprocessar
        with db.get_connection() as conn:
            if limit:
                cursor = conn.execute("""
                    SELECT DISTINCT pj.id, pj.numero_processo_planilha 
                    FROM processos_judiciais pj
                    INNER JOIN resultados_nlp rn ON pj.id = rn.processo_id
                    WHERE pj.conteudo_bruto_decisao IS NOT NULL 
                    AND pj.conteudo_bruto_decisao != ''
                    AND LENGTH(pj.conteudo_bruto_decisao) > 100
                    ORDER BY pj.id
                    LIMIT ?
                """, (limit,))
            else:
                cursor = conn.execute("""
                    SELECT DISTINCT pj.id, pj.numero_processo_planilha 
                    FROM processos_judiciais pj
                    INNER JOIN resultados_nlp rn ON pj.id = rn.processo_id
                    WHERE pj.conteudo_bruto_decisao IS NOT NULL 
                    AND pj.conteudo_bruto_decisao != ''
                    AND LENGTH(pj.conteudo_bruto_decisao) > 100
                    ORDER BY pj.id
                """)
            
            processos_para_reprocessar = cursor.fetchall()
            
            # Contar total de processos com NLP (para comparação)
            cursor_total = conn.execute("""
                SELECT COUNT(DISTINCT pj.id) as total
                FROM processos_judiciais pj
                INNER JOIN resultados_nlp rn ON pj.id = rn.processo_id
            """)
            total_com_nlp = cursor_total.fetchone()[0]
        
        if not processos_para_reprocessar:
            print("🔍 Nenhum processo com NLP e conteúdo válido encontrado para reprocessar")
            print("💡 Execute primeiro: python acoes_coletivas.py nlp process")
            return
        
        total_reprocessaveis = len(processos_para_reprocessar)
        processos_sem_conteudo = total_com_nlp - total_reprocessaveis
        
        print(f"📊 Análise de reprocessamento:")
        print(f"   Total de processos com NLP: {total_com_nlp}")
        print(f"   Processos reprocessáveis: {total_reprocessaveis}")
        print(f"   Processos sem conteúdo válido: {processos_sem_conteudo}")
        
        if processos_sem_conteudo > 0:
            print(f"⚠️  ATENÇÃO: {processos_sem_conteudo} processos com NLP não serão reprocessados")
            print("   (não possuem conteúdo válido para reprocessamento)")
        
        if not force:
            print(f"\n⚠️  Esta operação irá reprocessar {total_reprocessaveis} processos!")
            print("   Os resultados NLP destes processos serão substituídos.")
            print("   Use --force para confirmar ou Ctrl+C para cancelar.")
            
            try:
                input("Pressione Enter para continuar ou Ctrl+C para cancelar...")
            except KeyboardInterrupt:
                print("\nOperação cancelada pelo usuário.")
                return
        
        print(f"🚀 Iniciando reprocessamento de {total_reprocessaveis} processos...")
        
        sucessos = 0
        erros = 0
        
        for i, (processo_id, numero_processo) in enumerate(processos_para_reprocessar, 1):
            try:
                print(f"  [{i}/{total_reprocessaveis}] Reprocessando processo ID {processo_id} ({numero_processo or 'N/A'})")
                
                # Deletar APENAS o resultado NLP deste processo específico
                with db.get_connection() as conn:
                    conn.execute("DELETE FROM resultados_nlp WHERE processo_id = ?", (processo_id,))
                    conn.commit()
                
                # Reprocessar com NLP
                success = db.processar_texto_nlp(processo_id, pipeline)
                
                if success:
                    sucessos += 1
                    if i % 10 == 0:  # Mostrar progresso a cada 10 processos
                        print(f"    ✅ Progresso: {i}/{total_reprocessaveis} ({sucessos} sucessos, {erros} erros)")
                else:
                    erros += 1
                    print(f"    ❌ Erro ao reprocessar processo {processo_id}")
                    
            except Exception as e:
                erros += 1
                print(f"    ❌ Erro ao reprocessar processo {processo_id}: {e}")
                continue
        
        print(f"\n📊 Reprocessamento concluído!")
        print(f"   Processos reprocessáveis: {total_reprocessaveis}")
        print(f"   Sucessos: {sucessos}")
        print(f"   Erros: {erros}")
        print(f"   Taxa de sucesso: {(sucessos/total_reprocessaveis)*100:.1f}%")
        
        if processos_sem_conteudo > 0:
            print(f"   Processos preservados: {processos_sem_conteudo}")
        
        # Mostrar estatísticas atualizadas
        if sucessos > 0:
            print(f"\n📈 Estatísticas atualizadas:")
            show_nlp_stats(db)
        
    except Exception as e:
        logger.error(f"Erro no reprocessamento NLP: {e}")
        print(f"Erro: {e}")


def investigate_nlp_loss(db: DatabaseManager):
    """Investiga a perda de resultados NLP e sugere soluções"""
    logger = get_logger("CLI")
    
    try:
        with db.get_connection() as conn:
            # Verificar quantos processos têm conteúdo mas não têm NLP
            cursor = conn.execute("""
                SELECT COUNT(*) as total
                FROM processos_judiciais pj
                WHERE pj.conteudo_bruto_decisao IS NOT NULL 
                AND pj.conteudo_bruto_decisao != ''
                AND LENGTH(pj.conteudo_bruto_decisao) > 100
                AND NOT EXISTS (
                    SELECT 1 FROM resultados_nlp rn WHERE rn.processo_id = pj.id
                )
            """)
            processos_com_conteudo_sem_nlp = cursor.fetchone()[0]
            
            # Verificar quantos processos foram processados mas não têm conteúdo
            cursor = conn.execute("""
                SELECT COUNT(*) as total
                FROM processos_judiciais pj
                WHERE pj.processado_nlp = 1
                AND (pj.conteudo_bruto_decisao IS NULL OR pj.conteudo_bruto_decisao = '' OR LENGTH(pj.conteudo_bruto_decisao) <= 100)
            """)
            processos_processados_sem_conteudo = cursor.fetchone()[0]
            
            # Verificar quantos processos têm conteúdo válido no total
            cursor = conn.execute("""
                SELECT COUNT(*) as total
                FROM processos_judiciais pj
                WHERE pj.conteudo_bruto_decisao IS NOT NULL 
                AND pj.conteudo_bruto_decisao != ''
                AND LENGTH(pj.conteudo_bruto_decisao) > 100
            """)
            total_com_conteudo = cursor.fetchone()[0]
            
            # Verificar quantos processos têm NLP atualmente
            cursor = conn.execute("""
                SELECT COUNT(*) as total
                FROM resultados_nlp
            """)
            total_nlp_atual = cursor.fetchone()[0]
            
            # Verificar distribuição por origem
            cursor = conn.execute("""
                SELECT origem_texto, COUNT(*) as count
                FROM processos_judiciais
                GROUP BY origem_texto
                ORDER BY count DESC
            """)
            distribuicao_origem = cursor.fetchall()
        
        print("\n" + "="*60)
        print("DIAGNÓSTICO DE PERDA DE RESULTADOS NLP")
        print("="*60)
        
        print(f"📊 Situação atual:")
        print(f"   Processos com conteúdo válido: {total_com_conteudo}")
        print(f"   Processos com NLP atual: {total_nlp_atual}")
        print(f"   Processos com conteúdo SEM NLP: {processos_com_conteudo_sem_nlp}")
        print(f"   Processos processados SEM conteúdo: {processos_processados_sem_conteudo}")
        
        print(f"\n📋 Distribuição por origem:")
        for origem, count in distribuicao_origem:
            print(f"   • {origem or 'N/A'}: {count} processos")
        
        print(f"\n🔍 Análise:")
        if processos_com_conteudo_sem_nlp > 0:
            print(f"   ✅ {processos_com_conteudo_sem_nlp} processos podem ser recuperados com NLP")
        else:
            print(f"   ⚠️  Todos os processos com conteúdo válido já têm NLP")
        
        if processos_processados_sem_conteudo > 0:
            print(f"   ❌ {processos_processados_sem_conteudo} processos foram marcados como processados mas não têm conteúdo")
            print(f"      (provavelmente importados de planilhas)")
        
        print(f"\n💡 Recomendações:")
        if processos_com_conteudo_sem_nlp > 0:
            print(f"   1. Execute: python acoes_coletivas.py nlp process --limit {processos_com_conteudo_sem_nlp}")
            print(f"      Para recuperar os {processos_com_conteudo_sem_nlp} processos com conteúdo")
        
        if processos_processados_sem_conteudo > 0:
            print(f"   2. Execute: python acoes_coletivas.py scrape --limit 50")
            print(f"      Para coletar conteúdo dos processos sem dados")
        
        print(f"   3. Use 'nlp reprocess' apenas após fazer mudanças significativas no pipeline")
        print(f"="*60)
        
    except Exception as e:
        logger.error(f"Erro na investigação: {e}")
        print(f"Erro: {e}")


def fix_nlp_status(db: DatabaseManager, force: bool = False):
    """Corrige o status de processamento NLP para processos que não têm resultados"""
    logger = get_logger("CLI")
    
    try:
        with db.get_connection() as conn:
            # Encontrar processos marcados como processados mas sem resultados NLP
            cursor = conn.execute("""
                SELECT pj.id, pj.numero_processo_planilha 
                FROM processos_judiciais pj
                WHERE pj.processado_nlp = 1
                AND NOT EXISTS (
                    SELECT 1 FROM resultados_nlp rn WHERE rn.processo_id = pj.id
                )
                AND pj.conteudo_bruto_decisao IS NOT NULL 
                AND LENGTH(pj.conteudo_bruto_decisao) > 100
            """)
            
            processos_para_corrigir = cursor.fetchall()
        
        if not processos_para_corrigir:
            print("✅ Todos os processos têm status correto!")
            return
        
        total_para_corrigir = len(processos_para_corrigir)
        print(f"🔍 Encontrados {total_para_corrigir} processos com status inconsistente")
        print("   (marcados como processados mas sem resultados NLP)")
        
        if not force:
            print(f"\n⚠️  Esta operação irá resetar o status de {total_para_corrigir} processos")
            print("   para que possam ser reprocessados.")
            print("   Use --force para confirmar ou Ctrl+C para cancelar.")
            
            try:
                input("Pressione Enter para continuar ou Ctrl+C para cancelar...")
            except KeyboardInterrupt:
                print("\nOperação cancelada pelo usuário.")
                return
        
        print(f"🔧 Corrigindo status de {total_para_corrigir} processos...")
        
        # Resetar o status dos processos
        with db.get_connection() as conn:
            for processo_id, numero_processo in processos_para_corrigir:
                conn.execute("""
                    UPDATE processos_judiciais 
                    SET processado_nlp = 0, data_processamento = NULL
                    WHERE id = ?
                """, (processo_id,))
            
            conn.commit()
        
        print(f"✅ Status corrigido para {total_para_corrigir} processos!")
        print("   Agora eles podem ser reprocessados com 'nlp process'")
        
        # Mostrar estatísticas atualizadas
        print("\n📊 Estatísticas após correção:")
        with db.get_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM processos_judiciais WHERE processado_nlp = 0 AND LENGTH(conteudo_bruto_decisao) > 100')
            pendentes = cursor.fetchone()[0]
            cursor = conn.execute('SELECT COUNT(*) FROM processos_judiciais WHERE processado_nlp = 1')
            processados = cursor.fetchone()[0]
            cursor = conn.execute('SELECT COUNT(*) FROM resultados_nlp')
            resultados = cursor.fetchone()[0]
            
            print(f"   Processos pendentes: {pendentes}")
            print(f"   Processos processados: {processados}")
            print(f"   Resultados NLP: {resultados}")
        
    except Exception as e:
        logger.error(f"Erro na correção de status: {e}")
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
  
  %(prog)s nlp validate                   # Valida pipeline NLP aprimorado
  %(prog)s nlp process --limit 50         # Processa 50 textos com NLP aprimorado
  %(prog)s nlp process --id 123           # Processa processo específico
  %(prog)s nlp process --ids 123,456,789  # Processa múltiplos processos específicos
  %(prog)s nlp reprocess                  # Reprocessa todos os NLPs existentes
  %(prog)s nlp reprocess --force --limit 100  # Reprocessa até 100 NLPs sem confirmação
  %(prog)s nlp investigate               # Investiga problemas com NLPs perdidos
  %(prog)s nlp fix                        # Corrige status inconsistente de NLP
  %(prog)s nlp stats                      # Estatísticas detalhadas de NLP aprimorado
  %(prog)s nlp export -o resultados.json  # Exporta resultados NLP aprimorado
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
    scrape_parser.add_argument('--limit', type=int, default=100, help='Número máximo de processos para coletar')
    scrape_parser.add_argument('--collections', nargs='+', help='Coleções para pesquisar (acordaos, sentencas)', default=['acordaos', 'sentencas'])
    
    # Comandos NLP
    nlp_parser = subparsers.add_parser('nlp', help='Comandos de processamento NLP aprimorado')
    nlp_subparsers = nlp_parser.add_subparsers(dest='nlp_command', help='Comandos NLP disponíveis')
    
    # nlp process
    nlp_process_parser = nlp_subparsers.add_parser('process', help='Processa textos através do pipeline NLP aprimorado')
    nlp_process_parser.add_argument('--id', type=int, help='ID do processo específico para processar')
    nlp_process_parser.add_argument('--ids', type=str, help='IDs dos processos específicos para processar (separados por vírgula)')
    nlp_process_parser.add_argument('--limit', type=int, default=10, help='Número máximo de processos para processar em lote')
    
    # nlp stats
    nlp_stats_parser = nlp_subparsers.add_parser('stats', help='Exibe estatísticas detalhadas de NLP aprimorado')
    
    # nlp export
    nlp_export_parser = nlp_subparsers.add_parser('export', help='Exporta resultados de NLP aprimorado para JSON')
    nlp_export_parser.add_argument('-o', '--output', required=True, help='Arquivo de saída JSON')
    
    # nlp validate
    nlp_validate_parser = nlp_subparsers.add_parser('validate', help='Valida o pipeline NLP aprimorado')
    
    # nlp reprocess
    nlp_reprocess_parser = nlp_subparsers.add_parser('reprocess', help='Reprocessa todos os textos que já foram processados com NLP')
    nlp_reprocess_parser.add_argument('--force', action='store_true', help='Força o reprocessamento sem confirmação')
    nlp_reprocess_parser.add_argument('--limit', type=int, help='Número máximo de processos para reprocessar')
    
    # nlp investigate
    nlp_investigate_parser = nlp_subparsers.add_parser('investigate', help='Investiga problemas com resultados NLP perdidos')
    
    # nlp fix
    nlp_fix_parser = nlp_subparsers.add_parser('fix', help='Corrige status inconsistente de processamento NLP')
    nlp_fix_parser.add_argument('--force', action='store_true', help='Força a correção sem confirmação')

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
            db = init_database()
            scrape_data(db, args.limit, args.collections)
            
        elif args.command == 'nlp':
            db = init_database()
            
            if args.nlp_command == 'process':
                # Processar argumentos de IDs
                process_ids = None
                if args.ids:
                    try:
                        process_ids = [int(id_str.strip()) for id_str in args.ids.split(',')]
                    except ValueError:
                        print("❌ Erro: IDs devem ser números inteiros separados por vírgula")
                        sys.exit(1)
                
                process_nlp(db, args.id, process_ids, args.limit)
                
            elif args.nlp_command == 'stats':
                show_nlp_stats(db)
                
            elif args.nlp_command == 'export':
                export_nlp_results(db, args.output)
                
            elif args.nlp_command == 'validate':
                validate_nlp_pipeline()
                
            elif args.nlp_command == 'reprocess':
                reprocess_nlp(db, args.force, args.limit)
                
            elif args.nlp_command == 'investigate':
                investigate_nlp_loss(db)
                
            elif args.nlp_command == 'fix':
                fix_nlp_status(db, args.force)
                
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