import pandas as pd
import requests # Mantido para compatibilidade com session, embora não usado para chamadas API de dados
import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs, quote
import os
import re

# --- Configurações Iniciais ---
nome_do_arquivo_excel_entrada = "TESTE.xlsx"
nome_da_coluna_processos = "numero do processo"
nome_arquivo_saida = "processos_coletados_LOTE_COMPLETO.xlsx" # Nome para o arquivo final

dados_finais_coletados = []
# session_requests = requests.Session() # Se não for usar requests para API, pode ser removido

# --- Selenium: Obtenção de Tokens/Cookies ---
print("Iniciando Selenium...")
url_pagina_pesquisa = "https://jurisprudencia.jt.jus.br/jurisprudencia-nacional/pesquisa"
processo_exemplo_para_busca_inicial = "0001203-03.2018.5.10.0021" 
ID_CAMPO_BUSCA_PROCESSO = "pesquisaPrincipal" 
XPATH_BOTAO_BUSCA = "//i[@id='botaoPesquisaPrincipal']" 
XPATH_BOTAO_ACEITAR_COOKIES = "//button[contains(text(), 'Aceitar') or contains(text(), 'OK') or contains(text(), 'Entendi') or contains(text(), 'Prosseguir')]"

auto_session_id = None
manual_juristkn_para_sessao_atual = None
selenium_driver = None 

try:
    selenium_driver = webdriver.Chrome() 
    print(f"Navegador Selenium. Acessando: {url_pagina_pesquisa}")
    selenium_driver.get(url_pagina_pesquisa)
    selenium_driver.maximize_window()
    time.sleep(3)

    try:
        print("Tentando fechar banner de cookies...")
        botao_cookie = WebDriverWait(selenium_driver, 7).until(EC.element_to_be_clickable((By.XPATH, XPATH_BOTAO_ACEITAR_COOKIES)))
        botao_cookie.click()
        print("Banner de cookies fechado.")
        time.sleep(2)
    except Exception:
        print("Banner de cookies não encontrado/interagido.")

    campo_busca = WebDriverWait(selenium_driver, 20).until(EC.element_to_be_clickable((By.ID, ID_CAMPO_BUSCA_PROCESSO)))
    selenium_driver.execute_script("arguments[0].value='';", campo_busca) 
    campo_busca.send_keys(processo_exemplo_para_busca_inicial)
    print(f"Texto '{processo_exemplo_para_busca_inicial}' inserido.")

    botao_busca = WebDriverWait(selenium_driver, 10).until(EC.element_to_be_clickable((By.XPATH, XPATH_BOTAO_BUSCA)))
    try: botao_busca.click()
    except: selenium_driver.execute_script("arguments[0].click();", botao_busca)
    print("Botão de busca inicial clicado pelo Selenium.")
    print("Aguardando 5 segundos...")
    time.sleep(5) 

    cookies_selenium = selenium_driver.get_cookies()
    for cookie in cookies_selenium:
        if cookie['name'] == 'SESSION_ID_COOKIE_PUJ':
            auto_session_id = cookie['value']
            print(f"SUCESSO Selenium: 'SESSION_ID_COOKIE_PUJ' (para sessionId) encontrado: {auto_session_id}")
            break
    
    if not auto_session_id:
        print("ERRO: 'SESSION_ID_COOKIE_PUJ' não encontrado nos cookies após a busca inicial do Selenium.")
        auto_session_id = input("Por favor, insira manualmente o 'sessionId' da URL da API na aba Network do Selenium: ")

    print("\n" + "="*50)
    print("AÇÃO NECESSÁRIA DO USUÁRIO:")
    print("1. Olhe a janela do Chrome que o Selenium abriu.")
    print("2. Se necessário, abra as Ferramentas do Desenvolvedor (F12) -> Aba 'Network'.")
    print("3. Verifique a ÚLTIMA requisição para '.../api/no-auth/pesquisa?...' que o Selenium fez.")
    print("4. Copie o valor do parâmetro 'juristkn' dessa requisição.")
    print("="*50)
    manual_juristkn_para_sessao_atual = input(">>> Cole aqui o valor do 'juristkn' FRESCO e pressione Enter: ")
    
    if not manual_juristkn_para_sessao_atual:
        print("ERRO: juristkn não fornecido. Saindo.")
        if selenium_driver: selenium_driver.quit()
        exit()
    
except Exception as e_selenium:
    print(f"ERRO FATAL durante a automação com Selenium: {e_selenium}")
    print("Não foi possível obter os tokens/cookies dinamicamente. O script não pode continuar.")
    if selenium_driver: selenium_driver.quit()
    exit()
# Não fechamos o driver aqui ainda, pois ele será usado para as chamadas fetch

# Cabeçalhos para as chamadas fetch via Selenium (o cookie é gerenciado pelo navegador)
js_headers_para_fetch_obj = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7', # Use o seu valor exato
    'referer': url_pagina_pesquisa,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 OPR/119.0.0.0', # Use o seu valor exato
    'priority': 'u=1, i',
    'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Opera GX";v="119"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'cache-control': 'no-cache',
    'pragma': 'no-cache'
}
js_headers_string_para_fetch = json.dumps(js_headers_para_fetch_obj)


# --- Início do processamento da planilha Excel ---
try:
    df_entrada = pd.read_excel(nome_do_arquivo_excel_entrada)
    if nome_da_coluna_processos in df_entrada.columns:
        lista_de_processos_total = df_entrada[nome_da_coluna_processos].astype(str).tolist()
        
        processos_ja_coletados = set()
        if os.path.exists(nome_arquivo_saida):
            try:
                print(f"Lendo arquivo de saída existente: {nome_arquivo_saida}")
                df_existente = pd.read_excel(nome_arquivo_saida)
                if 'processo_planilha' in df_existente.columns:
                    processos_ja_coletados = set(df_existente['processo_planilha'].astype(str).tolist())
                print(f"{len(processos_ja_coletados)} processos já encontrados no arquivo de saída.")
            except Exception as e_read_exist:
                print(f"Erro ao ler arquivo de saída existente: {e_read_exist}. Começando do zero ou apenas com novos.")
        
        lista_de_processos_a_fazer = [p for p in lista_de_processos_total if p not in processos_ja_coletados]
        
        if not lista_de_processos_a_fazer:
             print("Todos os processos da planilha já foram coletados anteriormente.")
             if selenium_driver: selenium_driver.quit() # Fecha o driver se não há nada a fazer
             exit()
        else:
            print(f"Sucesso! Total de processos na planilha: {len(lista_de_processos_total)}.")
            print(f"Processando {len(lista_de_processos_a_fazer)} processos restantes.")

        colecoes_a_pesquisar = ['acordaos', 'sentencas'] 
        print(f"\nUsando para API: sessionId='{auto_session_id}', juristkn='{manual_juristkn_para_sessao_atual}'")

        for indice, numero_processo_original in enumerate(lista_de_processos_a_fazer):
            print(f"\nProcessando item {indice + 1}/{len(lista_de_processos_a_fazer)}: {numero_processo_original}")

            # Flag para interromper o processo se os tokens expirarem
            tokens_expiraram = False

            for nome_colecao in colecoes_a_pesquisar:
                print(f"  Buscando na coleção: '{nome_colecao}'...")
                
                # Reduzido para size=10 (ou 5), pois 50 deu erro de permissão. Ajuste conforme necessário.
                params_string = f"texto={quote(numero_processo_original)}&colecao={nome_colecao}&page=0&size=10&pesquisaSomenteNasEmentas=false&verTodosPrecedentes=false&tribunais=&sessionId={auto_session_id}&juristkn={manual_juristkn_para_sessao_atual}"
                url_api_completa_para_fetch = f"https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa?{params_string}"
                
                # print(f"    Executando fetch via Selenium para URL (início): {url_api_completa_para_fetch[:120]}...")

                javascript_code = f"""
                    const url = '{url_api_completa_para_fetch}';
                    const headers = {js_headers_string_para_fetch}; 
                    const done = arguments[arguments.length - 1];
                    
                    fetch(url, {{ headers: headers, cache: "no-store" }})
                        .then(response => {{
                            const status = response.status;
                            if (!response.ok) {{
                                return response.text().then(text => done({{ error: `HTTP error!`, status: status, body: text.substring(0, 500) }}));
                            }}
                            return response.json().then(data => done({{data: data, status: status}}));
                        }})
                        .catch(error => done({{ error: error.toString(), status: 0 }}));
                """
                
                dados_api = None
                try:
                    selenium_driver.set_script_timeout(40) 
                    dados_api = selenium_driver.execute_async_script(javascript_code)
                except Exception as e_fetch:
                    print(f"    ERRO ao executar fetch no Selenium: {e_fetch}")
                    dados_api = {"error": str(e_fetch), "status": 0}

                status_code_api = dados_api.get('status', 0) if isinstance(dados_api, dict) else 0
                print(f"    Status da resposta (via fetch Selenium) para '{nome_colecao}': {status_code_api}")

                if isinstance(dados_api, dict) and 'data' in dados_api and status_code_api == 200:
                    dados_json = dados_api['data']
                    if 'documentos' in dados_json and isinstance(dados_json.get('documentos'), list):
                        lista_docs_da_api = dados_json['documentos']
                        for doc_idx, documento_atual in enumerate(lista_docs_da_api):
                            id_doc = documento_atual.get('idDocumentoAcordao', documento_atual.get('idSentenca', f"ID_NAO_ENCONTRADO_{doc_idx}"))
                            texto_principal_html = None; origem_texto_principal = "Nenhum"
                            if nome_colecao == 'acordaos':
                                texto_principal_html = documento_atual.get('textoAcordao') or documento_atual.get('ementa')
                                origem_texto_principal = "textoAcordao/ementa" if texto_principal_html else "Nenhum"
                            elif nome_colecao == 'sentencas':
                                texto_principal_html = documento_atual.get('textoSentenca')
                                origem_texto_principal = "textoSentenca" if texto_principal_html else "Nenhum"
                            if not texto_principal_html: texto_principal_html = ""; origem_texto_principal = "Nenhum (não encontrado)"
                            
                            texto_limpo_final = ""
                            if isinstance(texto_principal_html, str) and texto_principal_html.strip():
                                try:
                                    soup = BeautifulSoup(texto_principal_html, 'lxml')
                                    texto_limpo_final = soup.get_text(separator=' ', strip=True)
                                except Exception as ex_parse: texto_limpo_final = f"Erro ao parsear HTML: {ex_parse}"
                            
                            info_documento = {
                                'processo_planilha': str(numero_processo_original), 'colecao_api': nome_colecao,
                                'id_documento_api': id_doc, 
                                'numero_documento_api': documento_atual.get('numeroProcesso', 'N/A'),
                                'classe_documento_api': documento_atual.get('classeProcesso', documento_atual.get('classeProcessualPorExtenso', 'N/A')),
                                'data_julgamento_api': documento_atual.get('dataJulgamento', 'N/A'),
                                'texto_limpo_extraido': texto_limpo_final 
                            }
                            dados_finais_coletados.append(info_documento)
                    else: print(f"      JSON da API (via Selenium fetch) sem 'documentos' ou formato inesperado.")
                elif isinstance(dados_api, dict) and dados_api.get('error'):
                    print(f"    ERRO na chamada fetch via Selenium para '{nome_colecao}': {dados_api.get('error')}")
                    if 'body' in dados_api: print(f"      Corpo do erro: {dados_api['body']}")
                    if status_code_api in [401, 403]: 
                        print("!!! ATENÇÃO: ERRO 401/403 NA API! Tokens/Sessão podem ter expirado.")
                        tokens_expiraram = True # Sinaliza para interromper após este processo
                        break # Sai do loop de coleções para este processo
                else:
                    print(f"    Nenhuma resposta ou resposta inesperada do fetch via Selenium para '{nome_colecao}'. Resposta: {dados_api}")
                
                print(f"    Pausa de 1.5 seg...") # Pausa entre coleções
                time.sleep(1.5) 
            
            if tokens_expiraram:
                print(f"Interrompendo coleta devido à expiração de tokens/sessão no processo: {numero_processo_original}.")
                break # Sai do loop principal de processos

            print(f"  Processo {numero_processo_original} finalizado. Pausa de 3 seg...") # Pausa entre processos
            time.sleep(3) 

            # REMOVIDO O BREAK QUE LIMITAVA A 1 PROCESSO
            # if indice == 0: 
            #     print("\nINTERROMPENDO APÓS O PRIMEIRO NÚMERO DE PROCESSO DA PLANILHA (MODO DE TESTE).")
            #     break 
        
        if dados_finais_coletados:
            print(f"\n--- Salvando {len(dados_finais_coletados)} registros de documentos coletados em Excel ---")
            # Adiciona novos dados ao DataFrame existente, se houver, ou cria um novo
            if os.path.exists(nome_arquivo_saida) and not processos_ja_coletados: # Se o arquivo existe mas começamos do zero (ex: arquivo corrompido)
                 df_final = pd.DataFrame(dados_finais_coletados)
            elif os.path.exists(nome_arquivo_saida) and processos_ja_coletados:
                df_antigo = pd.read_excel(nome_arquivo_saida)
                df_novo = pd.DataFrame(dados_finais_coletados)
                df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
                # Remover duplicatas caso algum processo tenha sido reprocessado por engano
                df_final.drop_duplicates(subset=['processo_planilha', 'id_documento_api', 'colecao_api'], keep='last', inplace=True)
            else:
                df_final = pd.DataFrame(dados_finais_coletados)
            
            try:
                df_final.to_excel(nome_arquivo_saida, index=False, engine='openpyxl') 
                print(f"!!! SUCESSO! Os dados foram salvos no arquivo: {nome_arquivo_saida} !!!")
            except Exception as e_save: print(f"--- ERRO AO SALVAR O ARQUIVO EXCEL: {e_save} ---")
        elif not lista_de_processos_a_fazer and processos_ja_coletados : # Caso onde não havia novos processos a fazer
            pass # A mensagem de "todos já coletados" já foi dada
        else: 
            print("\nNenhum novo dado foi coletado nesta execução para salvar em Excel.")
            
    else: print(f"Erro: Coluna '{nome_da_coluna_processos}' não foi encontrada...")
except FileNotFoundError: print(f"Erro: Arquivo '{nome_do_arquivo_excel_entrada}' não encontrado...")
except Exception as e: print(f"Ocorreu um erro inesperado geral: {e}")
finally: 
    if 'selenium_driver' in locals() and selenium_driver:
        if selenium_driver.session_id:
            selenium_driver.quit()
            print("Navegador Selenium fechado (no bloco finally geral).")