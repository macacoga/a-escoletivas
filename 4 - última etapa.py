import pandas as pd
from transformers import AutoTokenizer, T5ForConditionalGeneration # Usando T5Tokenizer e T5ForConditionalGeneration explicitamente
import torch 
import time
import nltk 
import os

# --- Bloco para baixar 'punkt' e 'stopwords' do NLTK se necessário ---
recursos_nltk = {"tokenizers/punkt": "punkt", "corpora/stopwords": "stopwords"}
for recurso_path, recurso_nome in recursos_nltk.items():
    try:
        nltk.data.find(recurso_path)
    except nltk.downloader.DownloadError:
        print(f"Baixando o recurso '{recurso_nome}' do NLTK...")
        nltk.download(recurso_nome)
        print(f"Download de '{recurso_nome}' concluído.")
# --- Fim do bloco de download ---


# --- Nomes dos arquivos e colunas ---
nome_arquivo_entrada = "processos_com_META_RESUMOS_FILTRADOS.xlsx"
coluna_processo_original = "processo_planilha" 
coluna_texto_para_resumir = "meta_resumo_filtrado"
coluna_novo_resumo_abstractivo = "tema_fundo_stjiris_t5" # Novo nome de coluna

# --- Configurações do Modelo de Sumarização ---
NOME_MODELO = "stjiris/t5-portuguese-legal-summarization" # <<< SEU NOVO MODELO ESCOLHIDO

# Parâmetros para a geração do resumo abstractivo
MIN_COMPRIMENTO_RESUMO = 100  # AJUSTADO: Mínimo de tokens (palavras aproximadas)
MAX_COMPRIMENTO_RESUMO = 500 # AJUSTADO: Máximo de tokens (para um resumo conciso do tema)
NUM_BEAMS = 4 
NO_REPEAT_NGRAM_SIZE = 2 # Para evitar repetição de bigramas
EARLY_STOPPING = True

print(f"Carregando o modelo de sumarização abstractiva '{NOME_MODELO}' e o tokenizer...")
print("Este processo pode levar alguns minutos na primeira vez (download do modelo).")
try:
    # Usar as classes específicas T5Tokenizer e T5ForConditionalGeneration
    tokenizer = AutoTokenizer.from_pretrained(NOME_MODELO) 
    model = T5ForConditionalGeneration.from_pretrained(NOME_MODELO)
    print("Modelo e tokenizer carregados com sucesso!")
except Exception as e_load_model:
    print(f"ERRO CRÍTICO ao carregar o modelo/tokenizer: {e_load_model}")
    print(f"Verifique o nome do modelo ('{NOME_MODELO}') e sua conexão com a internet.")
    print("Certifique-se de que 'transformers' e 'torch' estão instalados: pip install transformers torch")
    exit()

print(f"\nLendo o arquivo com meta-resumos: {nome_arquivo_entrada}...")
try:
    df = pd.read_excel(nome_arquivo_entrada)
except FileNotFoundError:
    print(f"ERRO: Arquivo '{nome_arquivo_entrada}' não encontrado.")
    exit()

if coluna_texto_para_resumir not in df.columns:
    print(f"ERRO: A coluna '{coluna_texto_para_resumir}' não foi encontrada na planilha.")
    print(f"Colunas disponíveis: {df.columns.tolist()}")
    exit()

print(f"Coluna '{coluna_texto_para_resumir}' encontrada.")

resumos_abstractivos_finais = []
NUM_LINHAS_TESTE = 3 
print(f"\nAVISO: Processando apenas as primeiras {NUM_LINHAS_TESTE} linhas para teste inicial.")
df_para_processar = df.head(NUM_LINHAS_TESTE)
# Para processar TUDO, comente a linha acima e descomente a seguinte:
# df_para_processar = df

total_textos_para_processar = len(df_para_processar)
print(f"Iniciando sumarização abstractiva para {total_textos_para_processar} meta-resumos...")

for indice, linha in df_para_processar.iterrows():
    indice_original_df = linha.name 
    processo_id_original = str(linha.get(coluna_processo_original, f"Linha {indice_original_df}"))
    texto_original_para_resumo = str(linha[coluna_texto_para_resumir])
    
    print(f"\n  Processando meta-resumo do processo: {processo_id_original} ({df_para_processar.index.get_loc(indice_original_df) + 1}/{total_textos_para_processar})")

    if pd.isna(texto_original_para_resumo) or not texto_original_para_resumo.strip() or \
       "Erro" in texto_original_para_resumo or \
       "Sem resumos individuais válidos" in texto_original_para_resumo or \
       "Texto concatenado dos resumos vazio" in texto_original_para_resumo:
        print(f"    -> Texto de entrada para {processo_id_original} inválido ou é uma mensagem de erro. Pulando.")
        resumos_abstractivos_finais.append("Entrada inválida para resumo abstractivo")
        continue

    try:
        # O prefixo "summarize: " é comum para modelos T5 afinados para sumarização
        input_text_com_prefixo = "summarize: " + texto_original_para_resumo

        # Tokenizar o texto
        # max_length=1024 é um limite comum para T5, mas pode ser ajustado se os meta-resumos forem menores.
        # O modelo stjiris/t5-portuguese-legal-summarization pode ter sido treinado com um max_length específico.
        # Vamos usar 1024 por segurança, mas o ideal seria verificar a documentação do modelo.
        tokenized_text_ids = tokenizer.encode(input_text_com_prefixo, return_tensors="pt", max_length=1024, truncation=True)
        
        # Gerar os IDs do resumo
        summary_ids = model.generate(
            tokenized_text_ids, 
            num_beams=NUM_BEAMS, 
            no_repeat_ngram_size=NO_REPEAT_NGRAM_SIZE,
            min_length=MIN_COMPRIMENTO_RESUMO, 
            max_length=MAX_COMPRIMENTO_RESUMO, 
            early_stopping=EARLY_STOPPING
        )
        
        # Decodificar os IDs de volta para texto
        resumo_gerado = tokenizer.decode(summary_ids[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
        resumos_abstractivos_finais.append(resumo_gerado)
        print(f"    -> Tema de fundo (STJIRIS T5): \"{resumo_gerado}\"")

    except Exception as e_summarize_abstractive:
        print(f"    ERRO ao gerar resumo abstractivo para processo {processo_id_original}: {e_summarize_abstractive}")
        resumos_abstractivos_finais.append("Erro na sumarização abstractiva")
    
    time.sleep(0.2) # Pequena pausa

# Lógica para adicionar a coluna de resumos ao DataFrame
if len(resumos_abstractivos_finais) == len(df_para_processar):
    if df_para_processar.shape[0] < df.shape[0]: # Se processou apenas o head
        df_saida = df_para_processar.copy()
        df_saida[coluna_novo_resumo_abstractivo] = resumos_abstractivos_finais
    else: # Processou o DataFrame completo
        df[coluna_novo_resumo_abstractivo] = resumos_abstractivos_finais
        df_saida = df
else:
    print("AVISO: Discrepância no número de resumos gerados. A coluna de resumo pode não ser adicionada corretamente.")
    df_saida = df.head(NUM_LINHAS_TESTE).copy()
    if len(resumos_abstractivos_finais) == len(df_saida):
         df_saida[coluna_novo_resumo_abstractivo] = resumos_abstractivos_finais
    else:
        print("Não foi possível alinhar os resumos com o DataFrame de saída para teste.")


nome_arquivo_saida_final = "processos_com_TEMA_DE_FUNDO_STJIRIS_T5.xlsx" 
try:
    df_saida.to_excel(nome_arquivo_saida_final, index=False, engine='openpyxl')
    print(f"\n!!! SUCESSO! Planilha com temas de fundo (modelo STJIRIS T5) salva como: {nome_arquivo_saida_final} !!!")
    if len(df_para_processar) < len(df):
        print(f"Lembre-se: Apenas as primeiras {len(df_para_processar)} linhas foram processadas para este teste.")
except Exception as e_save_final:
    print(f"ERRO ao salvar a planilha com resumos abstractivos: {e_save_final}")