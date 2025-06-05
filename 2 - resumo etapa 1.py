import pandas as pd
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer as SumyTokenizer # Renomeado para evitar conflito
from sumy.summarizers.text_rank import TextRankSummarizer
import nltk

# --- Bloco para baixar o 'punkt' do NLTK se necessário ---
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    print("Baixando o recurso 'punkt' do NLTK para tokenização de sentenças...")
    nltk.download('punkt')
    print("Download do 'punkt' concluído.")
# --- Fim do bloco de download ---

# Nome do arquivo Excel de entrada e da coluna de texto
nome_arquivo_entrada = "processos_coletados_completo.xlsx"
coluna_texto_original = "texto_limpo_extraido" # Confirme se é este o nome da coluna
coluna_novo_resumo = "resumo_extrativo_sumy"

# Número de frases desejadas no resumo
NUMERO_DE_FRASES_NO_RESUMO = 10 # Você pode ajustar este valor

print(f"Lendo o arquivo: {nome_arquivo_entrada}...")
try:
    df = pd.read_excel(nome_arquivo_entrada)
except FileNotFoundError:
    print(f"ERRO: Arquivo '{nome_arquivo_entrada}' não encontrado. Verifique o nome e o local.")
    exit()

if coluna_texto_original not in df.columns:
    print(f"ERRO: A coluna '{coluna_texto_original}' não foi encontrada na planilha.")
    print(f"Colunas disponíveis: {df.columns.tolist()}")
    exit()

print(f"Coluna '{coluna_texto_original}' encontrada.")

# Inicializar o sumarizador e o tokenizer para português
sumarizador = TextRankSummarizer()
tokenizer_portugues = SumyTokenizer("portuguese")

resumos = []

# LIMITAR O PROCESSAMENTO ÀS PRIMEIRAS 5 LINHAS PARA TESTE INICIAL
# Se quiser processar tudo, comente ou remova as duas linhas abaixo:
# print("Processando apenas as primeiras 5 linhas para teste...")
# df_para_processar = df.head(5)
# Para processar tudo, substitua a linha acima por:
df_para_processar = df

print(f"Iniciando sumarização para {len(df_para_processar)} textos...")

for indice, linha in df_para_processar.iterrows():
    texto_original = str(linha[coluna_texto_original]) # Garante que é string
    
    if pd.isna(texto_original) or not texto_original.strip():
        print(f"  Linha {indice + 1}: Texto original vazio ou ausente. Pulando.")
        resumos.append("") # Adiciona resumo vazio
        continue

    # Criar o parser para o texto atual
    parser = PlaintextParser.from_string(texto_original, tokenizer_portugues)
    
    # Gerar o resumo
    try:
        resumo_sumy = sumarizador(parser.document, NUMERO_DE_FRASES_NO_RESUMO)
        
        # Juntar as frases do resumo em uma única string
        texto_resumido = " ".join([str(sentenca) for sentenca in resumo_sumy])
        resumos.append(texto_resumido)
        print(f"  Linha {indice + 1}: Resumo gerado ({len(texto_resumido)} chars).")
    except Exception as e_sumy:
        print(f"  Linha {indice + 1}: Erro ao sumarizar - {e_sumy}")
        resumos.append("Erro na sumarização")

# Adicionar a lista de resumos como uma nova coluna no DataFrame (apenas para as linhas processadas)
# Se estiver processando um subconjunto (df_para_processar), crie a coluna no subconjunto
if len(resumos) == len(df_para_processar):
    df_para_processar = df_para_processar.copy() # Para evitar SettingWithCopyWarning
    df_para_processar.loc[:, coluna_novo_resumo] = resumos
    
    # Se você processou apenas df.head(5), você pode querer salvar apenas essas 5 linhas 
    # ou juntar de volta ao df original se quiser manter as outras colunas/linhas intactas
    # Por enquanto, vamos salvar o resultado do processamento (as 5 primeiras linhas com resumo)
    df_saida = df_para_processar
else: # Se algo deu errado e o número de resumos não bate (improvável aqui)
    print("AVISO: O número de resumos não corresponde ao número de textos processados. Salvando o DataFrame original.")
    df_saida = df 

# Salvar o DataFrame com a nova coluna de resumos
nome_arquivo_saida = "processos_com_resumos_extrativos.xlsx"
try:
    df_saida.to_excel(nome_arquivo_saida, index=False, engine='openpyxl')
    print(f"\n!!! SUCESSO! Planilha com resumos salva como: {nome_arquivo_saida} !!!")
    if len(df_para_processar) < len(df):
        print(f"Lembre-se: Apenas as primeiras {len(df_para_processar)} linhas foram processadas e salvas com resumo.")
except Exception as e_save:
    print(f"ERRO ao salvar a planilha com resumos: {e_save}")