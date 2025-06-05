import pandas as pd
import requests
import time
import json
from bs4 import BeautifulSoup

# Configurações iniciais
nome_do_arquivo_excel = "TESTE.xlsx"
nome_da_coluna_processos = "numero do processo"

# Lista para armazenar todos os dados extraídos
dados_finais_coletados = []

try:
    # Leitura da planilha de entrada
    df = pd.read_excel(nome_do_arquivo_excel)
    if nome_da_coluna_processos not in df.columns:
        print(f"Erro: A coluna '{nome_da_coluna_processos}' não foi encontrada em '{nome_do_arquivo_excel}'.")
        print(f"Colunas disponíveis: {df.columns.tolist()}")
        exit(1)

    # Garante que cada número de processo é string
    lista_de_processos = df[nome_da_coluna_processos].astype(str).tolist()
    print(f"Sucesso! Fornecidos {len(lista_de_processos)} números de processo.")

    colecoes_a_pesquisar = ['acordaos', 'sentencas']

    # --------------------------------------------------
    # Atenção: atualize estes valores com tokens atuais
    seu_session_id = "_si2oq0t"      # Substitua pelo valor mais recente
    seu_juristkn   = "784de2cc882300"   # Substitua pelo valor mais recente
    # --------------------------------------------------

    print("\nIniciando as consultas à API para todos os processos...")
    for indice, numero_processo_original in enumerate(lista_de_processos, start=1):
        print(f"\nProcessando {indice}/{len(lista_de_processos)}: {numero_processo_original}")

        for nome_colecao in colecoes_a_pesquisar:
            print(f"  - Consultando coleção '{nome_colecao}'")

            url_api = "https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa"
            params = {
                'texto': numero_processo_original,
                'colecao': nome_colecao,
                'page': 0,
                'size': 10,
                'pesquisaSomenteNasEmentas': 'false',
                'verTodosPrecedentes': 'false',
                'tribunais': '',
                'sessionId': seu_session_id,
                'juristkn': seu_juristkn
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            try:
                response = requests.get(url_api, params=params, headers=headers, timeout=30)
                print(f"    → Status da resposta: {response.status_code}")

                if not response.ok:
                    print(f"    ! Erro na requisição: HTTP {response.status_code}")
                    continue

                dados_json = response.json()
                if not isinstance(dados_json.get('documentos'), list):
                    print("    ! A chave 'documentos' não existe ou não é lista.")
                    continue

                documentos = dados_json['documentos']
                print(f"    → {len(documentos)} documento(s) encontrado(s)")

                # Itera por cada documento retornado
                for doc in documentos:
                    # Campos básicos
                    id_doc              = doc.get('idDocumentoAcordao', doc.get('idSentenca', 'N/A'))
                    numero_doc_api      = doc.get('numeroProcesso', 'N/A')
                    classe_doc          = doc.get('classeProcesso', doc.get('classeProcessualPorExtenso', 'N/A'))
                    relator_doc         = doc.get('relator', doc.get('nomeRedator', 'N/A'))
                    data_julgamento_doc = doc.get('dataJulgamento', 'N/A')
                    tribunal_doc        = doc.get('tribunal', 'N/A')
                    tipo_doc_api        = doc.get('tipoDocumento', 'N/A')

                    # Extrai o HTML principal (ementa, textoAcordao ou textoSentenca)
                    texto_html = doc.get('ementa')
                    origem_texto = "ementa"
                    if not texto_html:
                        texto_html = doc.get('textoAcordao')
                        origem_texto = "textoAcordao"
                    if not texto_html:
                        texto_html = doc.get('textoSentenca')
                        origem_texto = "textoSentenca"
                    if not texto_html:
                        texto_html = ""
                        origem_texto = "Nenhum"

                    # Converte HTML em texto limpo, sem cortes
                    texto_limpo = ""
                    if isinstance(texto_html, str) and texto_html.strip():
                        try:
                            soup = BeautifulSoup(texto_html, 'html.parser')
                            texto_limpo = soup.get_text(separator=' ', strip=True)
                        except Exception as e_parse:
                            texto_limpo = f"Erro ao parsear HTML: {e_parse}"
                    else:
                        texto_limpo = ""

                    # Armazena todas as informações em um dicionário
                    info_documento = {
                        'processo_planilha':            numero_processo_original,
                        'colecao_api':                  nome_colecao,
                        'id_documento_api':             id_doc,
                        'numero_documento_api':         numero_doc_api,
                        'classe_documento_api':         classe_doc,
                        'tipo_documento_api':           tipo_doc_api,
                        'tribunal_api':                 tribunal_doc,
                        'relator_redator_api':          relator_doc,
                        'data_julgamento_api':          data_julgamento_doc,
                        'origem_texto_extraido':        origem_texto,
                        'texto_limpo_extraido':         texto_limpo  # texto completo, sem cortes
                    }
                    dados_finais_coletados.append(info_documento)

                # Pausa breve antes da próxima coleção
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"    ! Erro de requisição: {e}")
                continue

        # Pausa antes de processar o próximo número de processo
        time.sleep(2)

    # Ao final de todas as consultas, salva tudo em um único Excel
    if dados_finais_coletados:
        print(f"\nPreparando para salvar {len(dados_finais_coletados)} registros em Excel...")
        df_resultados = pd.DataFrame(dados_finais_coletados)
        nome_arquivo_saida = "processos_coletados_completo.xlsx"
        try:
            df_resultados.to_excel(nome_arquivo_saida, index=False, engine='openpyxl')
            print(f"!!! Sucesso! Arquivo salvo: {nome_arquivo_saida} !!!")
        except Exception as e_save:
            print(f"!!! Erro ao salvar Excel: {e_save} !!!")
    else:
        print("\nNenhum dado coletado para salvar em Excel.")

except FileNotFoundError:
    print(f"Erro: Arquivo '{nome_do_arquivo_excel}' não encontrado.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
