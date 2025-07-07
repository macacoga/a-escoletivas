#!/usr/bin/env python3
"""
Script para baixar dados do NLTK necessários
"""

import nltk
import sys
from pathlib import Path

def download_nltk_data():
    """Baixa os dados do NLTK necessários"""
    
    print("=" * 60)
    print("BAIXANDO DADOS DO NLTK")
    print("=" * 60)
    
    # Lista de recursos necessários
    resources = [
        'punkt',
        'punkt_tab',
        'averaged_perceptron_tagger',
        'maxent_ne_chunker',
        'words',
        'stopwords'
    ]
    
    for resource in resources:
        try:
            print(f"Baixando {resource}...")
            nltk.download(resource, quiet=True)
            print(f"✅ {resource} baixado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao baixar {resource}: {e}")
    
    # Verificar se os dados foram baixados
    try:
        from nltk.data import find
        punkt_path = find('tokenizers/punkt')
        print(f"\n✅ Dados do NLTK instalados em: {punkt_path}")
    except LookupError:
        print("\n❌ Erro: Dados do NLTK não foram encontrados")
        return False
    
    print("\n" + "=" * 60)
    print("DADOS DO NLTK INSTALADOS COM SUCESSO!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = download_nltk_data()
    sys.exit(0 if success else 1) 