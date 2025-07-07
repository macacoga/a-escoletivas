import pandas as pd
import json

# Ler o arquivo CSV
df = pd.read_csv('tbl_TRT10.csv', sep=';', encoding='utf-8')

print("=== ANÁLISE DOS DADOS ===")
print(f"Total de linhas: {len(df)}")
print(f"Colunas disponíveis: {list(df.columns)}")

# Verificar alguns exemplos de polo_ativo
print("\n=== EXEMPLOS DE POLO_ATIVO ===")
polo_ativo_samples = df['polo_ativo'].dropna().head(10)
for i, sample in enumerate(polo_ativo_samples):
    print(f"{i+1}. {sample}")

# Verificar alguns exemplos de uf_oj
print("\n=== EXEMPLOS DE UF_OJ ===")
uf_oj_samples = df['uf_oj'].dropna().head(10)
for i, sample in enumerate(uf_oj_samples):
    print(f"{i+1}. {sample}")

# Testar filtros corrigidos
print("\n=== TESTANDO FILTROS CORRIGIDOS ===")

# Filtro 1: polo_ativo que contenha "SIND" (dentro do JSON)
def contains_sind(value):
    if pd.isna(value):
        return False
    try:
        # Tentar parsear como JSON
        if isinstance(value, str) and value.startswith('{'):
            parsed = json.loads(value)
            if isinstance(parsed, list) and len(parsed) > 0:
                return "SIND" in parsed[0].upper()
            elif isinstance(parsed, str):
                return "SIND" in parsed.upper()
        # Se não for JSON, verificar diretamente
        return "SIND" in str(value).upper()
    except:
        return "SIND" in str(value).upper()

# Filtro 2: uf_oj igual a "DF"
def is_df(value):
    if pd.isna(value):
        return False
    return str(value).strip() == "DF"

# Aplicar filtros
mask_sind = df['polo_ativo'].apply(contains_sind)
mask_df = df['uf_oj'].apply(is_df)
mask_combined = mask_sind & mask_df

print(f"Processos com polo_ativo contendo 'SIND': {mask_sind.sum()}")
print(f"Processos com uf_oj = 'DF': {mask_df.sum()}")
print(f"Processos com AMBOS filtros: {mask_combined.sum()}")

# Mostrar alguns resultados
if mask_combined.sum() > 0:
    print("\n=== PROCESSOS ENCONTRADOS ===")
    filtered_df = df[mask_combined]
    for i, (_, row) in enumerate(filtered_df.head(5).iterrows()):
        print(f"{i+1}. Processo: {row['numero_sigilo']}")
        print(f"   Polo ativo: {row['polo_ativo']}")
        print(f"   UF OJ: {row['uf_oj']}")
        print()

# Verificar se há processos com "SIND" mas não "DF"
sind_only = mask_sind & ~mask_df
if sind_only.sum() > 0:
    print(f"\n=== PROCESSOS COM SIND MAS NÃO DF ({sind_only.sum()}) ===")
    sind_df = df[sind_only]
    for i, (_, row) in enumerate(sind_df.head(3).iterrows()):
        print(f"{i+1}. Processo: {row['numero_sigilo']}")
        print(f"   Polo ativo: {row['polo_ativo']}")
        print(f"   UF OJ: {row['uf_oj']}")
        print()

# Verificar se há processos com "DF" mas não "SIND"
df_only = mask_df & ~mask_sind
if df_only.sum() > 0:
    print(f"\n=== PROCESSOS COM DF MAS NÃO SIND ({df_only.sum()}) ===")
    df_only_df = df[df_only]
    for i, (_, row) in enumerate(df_only_df.head(3).iterrows()):
        print(f"{i+1}. Processo: {row['numero_sigilo']}")
        print(f"   Polo ativo: {row['polo_ativo']}")
        print(f"   UF OJ: {row['uf_oj']}")
        print() 