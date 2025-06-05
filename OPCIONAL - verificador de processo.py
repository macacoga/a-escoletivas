import pandas as pd
import os

# --- Nomes dos arquivos e colunas ---
# Substitua pelos nomes exatos dos seus arquivos, se forem diferentes.
arquivo_dados_coletados_api = "processos_coletados_completo.xlsx" # Saída da coleta da API
arquivo_resumos_individuais = "processos_com_resumos_extrativos.xlsx" # Saída do 1º script de resumo
arquivo_meta_resumos = "processos_com_META_RESUMOS_FILTRADOS.xlsx" # Saída do 2º script de resumo (meta)

col_processo_original = "processo_planilha"
col_texto_limpo_coletado = "texto_limpo_extraido" # Do arquivo_dados_coletados_api
col_resumo_individual = "resumo_extrativo_sumy" # Do arquivo_resumos_individuais
col_meta_resumo = "meta_resumo_filtrado" # Do arquivo_meta_resumos

# --- Função para carregar DataFrame e lidar com erros ---
def carregar_df(nome_arquivo, col_processo):
    if not os.path.exists(nome_arquivo):
        print(f"AVISO: Arquivo '{nome_arquivo}' não encontrado. Pulando análise deste arquivo.")
        return None, set()
    try:
        df = pd.read_excel(nome_arquivo)
        if col_processo not in df.columns:
            print(f"AVISO: Coluna '{col_processo}' não encontrada em '{nome_arquivo}'. Pulando.")
            return None, set()
        # Garante que a coluna do processo seja tratada como string para evitar problemas com tipos mistos
        processos_unicos = set(df[col_processo].dropna().astype(str).unique())
        print(f"Arquivo '{nome_arquivo}' carregado. Encontrados {len(processos_unicos)} processos únicos.")
        return df, processos_unicos
    except Exception as e:
        print(f"Erro ao carregar ou processar '{nome_arquivo}': {e}")
        return None, set()

print("--- INÍCIO DO DIAGNÓSTICO DE CONTAGEM ---")

# 1. Análise do arquivo da coleta da API
print(f"\n1. Analisando arquivo de coleta da API: '{arquivo_dados_coletados_api}'")
df_coleta_api, processos_na_coleta = carregar_df(arquivo_dados_coletados_api, col_processo_original)
processos_com_texto_valido_na_coleta = set()
if df_coleta_api is not None and col_texto_limpo_coletado in df_coleta_api.columns:
    df_com_texto = df_coleta_api[
        df_coleta_api[col_texto_limpo_coletado].notna() &
        (df_coleta_api[col_texto_limpo_coletado].astype(str).str.strip() != "") &
        (~df_coleta_api[col_texto_limpo_coletado].astype(str).str.contains("Erro ao parsear HTML", case=False, na=False)) &
        (~df_coleta_api[col_texto_limpo_coletado].astype(str).str.contains("Conteúdo HTML não era string", case=False, na=False))
    ]
    if not df_com_texto.empty:
        processos_com_texto_valido_na_coleta = set(df_com_texto[col_processo_original].dropna().astype(str).unique())
    print(f"   - Processos com pelo menos um documento com texto limpo válido na coleta: {len(processos_com_texto_valido_na_coleta)}")
    if len(processos_na_coleta) > len(processos_com_texto_valido_na_coleta):
        print(f"   - Processos da coleta original que podem não ter tido texto válido: {len(processos_na_coleta) - len(processos_com_texto_valido_na_coleta)}")
        print(f"     Exemplos: {list(processos_na_coleta - processos_com_texto_valido_na_coleta)[:5]}")


# 2. Análise do arquivo de resumos individuais
print(f"\n2. Analisando arquivo de resumos individuais: '{arquivo_resumos_individuais}'")
df_res_individuais, processos_no_resumo_individual = carregar_df(arquivo_resumos_individuais, col_processo_original)
processos_com_resumo_individual_valido = set()
if df_res_individuais is not None and col_resumo_individual in df_res_individuais.columns:
    df_com_res_ind = df_res_individuais[
        df_res_individuais[col_resumo_individual].notna() &
        (df_res_individuais[col_resumo_individual].astype(str).str.strip() != "") &
        (~df_res_individuais[col_resumo_individual].astype(str).str.contains("Erro na sumarização", case=False, na=False)) &
        (~df_res_individuais[col_resumo_individual].astype(str).str.contains("Texto original vazio", case=False, na=False))
    ]
    if not df_com_res_ind.empty:
        # Agrupa para garantir que o processo tenha pelo menos UM resumo individual válido.
        # O .groupby().filter() pode ser pesado. Uma alternativa é pegar unique após o filtro.
        processos_com_resumo_individual_valido = set(df_com_res_ind[col_processo_original].dropna().astype(str).unique())

    print(f"   - Processos com pelo menos um resumo individual válido: {len(processos_com_resumo_individual_valido)}")
    if len(processos_no_resumo_individual) > len(processos_com_resumo_individual_valido):
        print(f"   - Processos que estavam no arquivo de resumos, mas podem não ter tido resumos individuais válidos: {len(processos_no_resumo_individual) - len(processos_com_resumo_individual_valido)}")
        print(f"     Exemplos: {list(processos_no_resumo_individual - processos_com_resumo_individual_valido)[:5]}")


# 3. Análise do arquivo de meta-resumos
print(f"\n3. Analisando arquivo de meta-resumos: '{arquivo_meta_resumos}'")
df_meta, processos_no_meta_resumo = carregar_df(arquivo_meta_resumos, col_processo_original)
processos_com_meta_resumo_valido = set()
if df_meta is not None and col_meta_resumo in df_meta.columns:
    df_com_meta = df_meta[
        df_meta[col_meta_resumo].notna() &
        (df_meta[col_meta_resumo].astype(str).str.strip() != "") &
        (~df_meta[col_meta_resumo].astype(str).str.contains("Erro na meta-sumarização", case=False, na=False)) &
        (~df_meta[col_meta_resumo].astype(str).str.contains("Sem resumos individuais válidos", case=False, na=False)) &
        (~df_meta[col_meta_resumo].astype(str).str.contains("Texto concatenado dos resumos vazio", case=False, na=False))
    ]
    if not df_com_meta.empty:
        processos_com_meta_resumo_valido = set(df_com_meta[col_processo_original].dropna().astype(str).unique())
    print(f"   - Processos com meta-resumo válido final: {len(processos_com_meta_resumo_valido)}")
    if len(processos_no_meta_resumo) > len(processos_com_meta_resumo_valido):
         print(f"  - Processos que estavam no arquivo de meta-resumos, mas podem não ter tido meta-resumos válidos: {len(processos_no_meta_resumo) - len(processos_com_meta_resumo_valido)}")
         print(f"    Exemplos: {list(processos_no_meta_resumo - processos_com_meta_resumo_valido)[:5]}")


# --- Comparação entre as etapas ---
print("\n--- SUMÁRIO DAS PERDAS/DIFERENÇAS ---")

print(f"Processos únicos na coleta da API (considerando todos os documentos): {len(processos_na_coleta)}")
print(f"Processos com pelo menos um TEXTO VÁLIDO na coleta da API: {len(processos_com_texto_valido_na_coleta)}")
processos_sem_texto_valido_inicial = processos_na_coleta - processos_com_texto_valido_na_coleta
if processos_sem_texto_valido_inicial:
    print(f"  -> {len(processos_sem_texto_valido_inicial)} processos podem não ter tido nenhum documento com texto válido na coleta inicial.")
    print(f"     Exemplos: {list(processos_sem_texto_valido_inicial)[:10]}")

print(f"\nProcessos únicos no arquivo de RESUMOS INDIVIDUAIS: {len(processos_no_resumo_individual)}")
print(f"Processos com pelo menos um RESUMO INDIVIDUAL VÁLIDO: {len(processos_com_resumo_individual_valido)}")
processos_perdidos_na_sumarizacao_individual = processos_com_texto_valido_na_coleta - processos_com_resumo_individual_valido
if processos_perdidos_na_sumarizacao_individual:
    print(f"  -> {len(processos_perdidos_na_sumarizacao_individual)} processos tinham texto válido, mas não geraram resumo individual válido.")
    print(f"     Exemplos: {list(processos_perdidos_na_sumarizacao_individual)[:10]}")

print(f"\nProcessos únicos no arquivo de META-RESUMOS: {len(processos_no_meta_resumo)}") # Deveria ser 134, conforme você disse
print(f"Processos com META-RESUMO VÁLIDO: {len(processos_com_meta_resumo_valido)}")
processos_perdidos_na_meta_sumarizacao = processos_com_resumo_individual_valido - processos_com_meta_resumo_valido
if processos_perdidos_na_meta_sumarizacao:
    print(f"  -> {len(processos_perdidos_na_meta_sumarizacao)} processos tinham resumos individuais válidos, mas não geraram meta-resumo válido.")
    print(f"     Exemplos: {list(processos_perdidos_na_meta_sumarizacao)[:10]}")

print("\n--- FIM DO DIAGNÓSTICO ---")