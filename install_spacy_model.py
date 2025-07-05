#!/usr/bin/env python3
"""
Script para instalar modelo spaCy em português
"""

import subprocess
import sys
import spacy
from pathlib import Path

def install_spacy_model():
    """Instala o modelo spaCy em português"""
    
    model_name = "pt_core_news_sm"
    
    print(f"Instalando modelo spaCy: {model_name}")
    
    try:
        # Tentar carregar o modelo para ver se já está instalado
        nlp = spacy.load(model_name)
        print(f"✅ Modelo {model_name} já está instalado!")
        return True
        
    except OSError:
        print(f"📦 Modelo {model_name} não encontrado. Instalando...")
        
        try:
            # Instalar o modelo
            subprocess.check_call([
                sys.executable, "-m", "spacy", "download", model_name
            ])
            
            # Testar se a instalação foi bem-sucedida
            nlp = spacy.load(model_name)
            print(f"✅ Modelo {model_name} instalado com sucesso!")
            
            # Testar o modelo
            doc = nlp("O Banco do Brasil foi condenado a pagar indenização de R$ 10.000 ao trabalhador.")
            print(f"🧪 Teste do modelo:")
            print(f"  - Tokens: {len(doc)}")
            print(f"  - Entidades: {[(ent.text, ent.label_) for ent in doc.ents]}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar modelo: {e}")
            return False
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return False

if __name__ == "__main__":
    success = install_spacy_model()
    sys.exit(0 if success else 1) 