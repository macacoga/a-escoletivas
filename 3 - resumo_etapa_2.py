import pandas as pd
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer as SumyTokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
import nltk
import os # Necessário se for usar os.path.exists

# --- Bloco para baixar o 'punkt' do NLTK se necessário ---
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    print("Baixando o recurso 'punkt' do NLTK para tokenização de sentenças...")
    nltk.download('punkt')
    print("Download do 'punkt' concluído.")
# --- Fim do bloco de download ---

# Nomes dos arquivos e colunas
nome_arquivo_entrada_com_resumos = "processos_com_resumos_extrativos.xlsx"
coluna_processo_original = "processo_planilha"
coluna_resumos_individuais = "resumo_extrativo_sumy"
coluna_data_julgamento = "data_julgamento_api" 
coluna_novo_meta_resumo = "meta_resumo_filtrado" # Nome da nova coluna

# Número de frases desejadas no META-RESUMO
NUMERO_DE_FRASES_NO_META_RESUMO = 10 # Ajuste conforme sua necessidade

# Lista de termos processuais para tentar filtrar resumos individuais
# Esta lista pode e deve ser expandida por você com base no seu conhecimento!
termos_processuais_para_filtrar = [
    "nulidade de citação", "intempestividade", "deserção", 
    "preliminar de ilegitimidade", "cerceamento de defesa", 
    "pressupostos de admissibilidade", "não conheço do recurso",
    "recurso não conhecido", "prequestionamento", "óbice da súmula",
    "custas processuais", "justiça gratuita", "honorários de sucumbência",
    "embargos de declaração", "agravo de instrumento", "despacho de mero expediente",
    "negar seguimento", "dar provimento parcial apenas para", "ilegitimidade sindical", 
    "legitimidade sindical", "acordam os", "precedente", "repercussão geral", "esclarecimento",
    "omissão", "declaratório", "contradição", "TRIBUNAL REGIONAL DO TRABALHO", 
    "recurso de revista"
    # Cuidado com termos muito genéricos
]

print(f"Lendo o arquivo com resumos individuais: {nome_arquivo_entrada_com_resumos}...")
try:
    df = pd.read_excel(nome_arquivo_entrada_com_resumos)
except FileNotFoundError:
    print(f"ERRO: Arquivo '{nome_arquivo_entrada_com_resumos}' não encontrado.")
    exit()

colunas_necessarias = [coluna_processo_original, coluna_resumos_individuais, coluna_data_julgamento]
for col in colunas_necessarias:
    if col not in df.columns:
        print(f"ERRO: A coluna '{col}' não foi encontrada na planilha.")
        print(f"Colunas disponíveis: {df.columns.tolist()}")
        exit()

print("Colunas necessárias encontradas.")

df[coluna_data_julgamento] = pd.to_datetime(df[coluna_data_julgamento], errors='coerce', dayfirst=True)
agrupado_por_processo = df.groupby(coluna_processo_original)
meta_resumos_finais = [] 
sumarizador = TextRankSummarizer()
tokenizer_portugues = SumyTokenizer("portuguese")

total_processos_unicos = df[coluna_processo_original].nunique()
print(f"Iniciando a geração de meta-resumos para {total_processos_unicos} processos únicos...")

contador_processos_processados = 0
for nome_processo, grupo in agrupado_por_processo:
    contador_processos_processados += 1
    print(f"\nProcessando meta-resumo para: {nome_processo} ({contador_processos_processados}/{total_processos_unicos})")

    grupo_com_resumos_validos = grupo.dropna(subset=[coluna_resumos_individuais])
    grupo_com_resumos_validos = grupo_com_resumos_validos[grupo_com_resumos_validos[coluna_resumos_individuais].str.strip() != '']
    
    if grupo_com_resumos_validos.empty:
        print(f"  Processo {nome_processo}: Nenhum resumo individual válido encontrado. Pulando meta-resumo.")
        meta_resumos_finais.append({
            coluna_processo_original: nome_processo,
            coluna_novo_meta_resumo: "Sem resumos individuais válidos para processar"
        })
        continue

    grupo_ordenado = grupo_com_resumos_validos.sort_values(by=coluna_data_julgamento, ascending=True)
    
    # --- INÍCIO DA LÓGICA DE FILTRAGEM ---
    textos_para_meta_resumo = []
    resumos_individuais_originais_do_grupo = grupo_ordenado[coluna_resumos_individuais].astype(str).tolist()
    
    for resumo_individual in resumos_individuais_originais_do_grupo:
        ignorar_este_resumo = False
        for termo_processual in termos_processuais_para_filtrar:
            if termo_processual.lower() in resumo_individual.lower():
                ignorar_este_resumo = True
                print(f"      -> Resumo individual (início: '{resumo_individual[:70]}...') ignorado por conter termo: '{termo_processual}'")
                break 
        if not ignorar_este_resumo:
            textos_para_meta_resumo.append(resumo_individual)
    # --- FIM DA LÓGICA DE FILTRAGEM ---

    texto_concatenado_para_sumarizar = ""
    if not textos_para_meta_resumo: # Se todos os resumos foram filtrados
        print(f"      AVISO: Todos os resumos individuais de '{nome_processo}' foram filtrados por termos processuais. Usando todos os resumos originais do grupo como fallback.")
        texto_concatenado_para_sumarizar = " ".join(resumos_individuais_originais_do_grupo)
    else:
        print(f"      {len(textos_para_meta_resumo)} resumos individuais selecionados (após filtro) para o meta-resumo.")
        texto_concatenado_para_sumarizar = " ".join(textos_para_meta_resumo)

    if not texto_concatenado_para_sumarizar.strip():
        print(f"  Processo {nome_processo}: Texto concatenado dos resumos está vazio após filtro/fallback. Pulando meta-resumo.")
        meta_resumos_finais.append({
            coluna_processo_original: nome_processo,
            coluna_novo_meta_resumo: "Texto concatenado dos resumos vazio"
        })
        continue

    parser = PlaintextParser.from_string(texto_concatenado_para_sumarizar, tokenizer_portugues)
    
    try:
        meta_resumo_sumy = sumarizador(parser.document, NUMERO_DE_FRASES_NO_META_RESUMO)
        texto_meta_resumido = " ".join([str(sentenca) for sentenca in meta_resumo_sumy])
        
        meta_resumos_finais.append({
            coluna_processo_original: nome_processo,
            coluna_novo_meta_resumo: texto_meta_resumido
        })
        print(f"  Meta-resumo gerado para {nome_processo} ({len(texto_meta_resumido)} chars).")
    except Exception as e_meta_sumy:
        print(f"  Erro ao gerar meta-resumo para {nome_processo}: {e_meta_sumy}")
        meta_resumos_finais.append({
            coluna_processo_original: nome_processo,
            coluna_novo_meta_resumo: "Erro na meta-sumarização"
        })

df_meta_resumos = pd.DataFrame(meta_resumos_finais)

nome_arquivo_saida_meta = "processos_com_META_RESUMOS_FILTRADOS.xlsx"
try:
    df_meta_resumos.to_excel(nome_arquivo_saida_meta, index=False, engine='openpyxl')
    print(f"\n!!! SUCESSO! Planilha com meta-resumos (filtrados) salva como: {nome_arquivo_saida_meta} !!!")
except Exception as e_save_meta:
    print(f"ERRO ao salvar a planilha com meta-resumos: {e_save_meta}")