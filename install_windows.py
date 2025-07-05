#!/usr/bin/env python3
"""
Script de instalação para Windows
Instala as dependências de forma segura, evitando problemas de compilação.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Executa um comando e mostra o resultado"""
    print(f"\n{description}...")
    print(f"Executando: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Sucesso!")
            if result.stdout:
                print(result.stdout)
        else:
            print("✗ Erro!")
            if result.stderr:
                print(f"Erro: {result.stderr}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Erro ao executar comando: {e}")
        return False

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    version_info = sys.version_info
    if version_info.major == 3 and version_info.minor >= 8:
        print(f"✓ Python {version_info.major}.{version_info.minor}.{version_info.micro} é compatível")
        return True
    else:
        print(f"✗ Python {version_info.major}.{version_info.minor}.{version_info.micro} não é compatível")
        print("Requer Python 3.8 ou superior")
        return False

def install_basic_packages():
    """Instala pacotes básicos que raramente dão problema"""
    basic_packages = [
        "requests",
        "beautifulsoup4",
        "selenium",
        "lxml",
        "openpyxl",
        "python-dotenv",
        "click",
        "tqdm",
        "colorama",
        "jsonschema",
        "bleach",
        "html2text",
        "flask",
        "flask-restx",
        "flask-cors",
        "marshmallow",
        "waitress",
        "structlog",
        "python-dateutil",
        "pytest",
        "pytest-cov",
        "black",
        "flake8",
        "webdriver-manager",
        "textstat",
        "sumy",
        "alembic",
    ]
    
    for package in basic_packages:
        if not run_command(f"pip install {package}", f"Instalando {package}"):
            print(f"Falha ao instalar {package}, mas continuando...")
    
    return True

def install_scientific_packages():
    """Instala pacotes científicos usando wheels pré-compilados"""
    print("\nInstalando pacotes científicos (numpy, pandas, scikit-learn)...")
    
    # Tenta instalar usando wheels pré-compilados
    scientific_packages = [
        "numpy",
        "pandas", 
        "scikit-learn",
        "scipy",
    ]
    
    for package in scientific_packages:
        success = run_command(
            f"pip install --only-binary={package} {package}",
            f"Instalando {package} (wheel pré-compilado)"
        )
        
        if not success:
            print(f"Tentando instalar {package} de forma padrão...")
            run_command(f"pip install {package}", f"Instalando {package}")

def install_nlp_packages():
    """Instala pacotes de NLP"""
    print("\nInstalando pacotes de NLP...")
    
    nlp_packages = [
        "spacy",
        "nltk",
        "transformers",
        "wordcloud",
        "pydantic",
        "pydantic-settings",
    ]
    
    for package in nlp_packages:
        run_command(f"pip install {package}", f"Instalando {package}")

def install_database_packages():
    """Instala pacotes de banco de dados"""
    print("\nInstalando pacotes de banco de dados...")
    
    # SQLAlchemy
    run_command("pip install sqlalchemy", "Instalando SQLAlchemy")
    
    # PostgreSQL (opcional)
    print("\nTentando instalar suporte ao PostgreSQL (opcional)...")
    if not run_command("pip install psycopg2-binary", "Instalando psycopg2-binary"):
        print("Não foi possível instalar suporte ao PostgreSQL, mas não é obrigatório")

def download_nlp_models():
    """Baixa modelos do spaCy e dados do NLTK"""
    print("\nBaixando modelos de NLP...")
    
    # Modelo do spaCy
    run_command(
        "python -m spacy download pt_core_news_sm",
        "Baixando modelo português do spaCy"
    )
    
    # Dados do NLTK
    nltk_downloads = [
        "punkt",
        "stopwords", 
        "wordnet",
        "vader_lexicon",
    ]
    
    for data in nltk_downloads:
        run_command(
            f"python -c \"import nltk; nltk.download('{data}')\"",
            f"Baixando dados do NLTK: {data}"
        )

def main():
    """Função principal"""
    print("="*60)
    print("INSTALAÇÃO AUTOMÁTICA - PROJETO AÇÕES COLETIVAS")
    print("="*60)
    
    # Verifica a versão do Python
    if not check_python_version():
        print("\nPor favor, instale Python 3.8 ou superior antes de continuar.")
        return False
    
    # Atualiza o pip
    print("\nAtualizando pip...")
    run_command("python -m pip install --upgrade pip", "Atualizando pip")
    
    # Instala setuptools e wheel
    print("\nInstalando ferramentas de compilação...")
    run_command("pip install setuptools wheel", "Instalando setuptools e wheel")
    
    # Instala pacotes básicos
    print("\n" + "="*40)
    print("INSTALANDO PACOTES BÁSICOS")
    print("="*40)
    install_basic_packages()
    
    # Instala pacotes científicos
    print("\n" + "="*40)
    print("INSTALANDO PACOTES CIENTÍFICOS")
    print("="*40)
    install_scientific_packages()
    
    # Instala pacotes de NLP
    print("\n" + "="*40)
    print("INSTALANDO PACOTES DE NLP")
    print("="*40)
    install_nlp_packages()
    
    # Instala pacotes de banco de dados
    print("\n" + "="*40)
    print("INSTALANDO PACOTES DE BANCO DE DADOS")
    print("="*40)
    install_database_packages()
    
    # Baixa modelos de NLP
    print("\n" + "="*40)
    print("BAIXANDO MODELOS DE NLP")
    print("="*40)
    download_nlp_models()
    
    # Verifica a instalação
    print("\n" + "="*40)
    print("VERIFICANDO INSTALAÇÃO")
    print("="*40)
    
    if Path("verify_installation.py").exists():
        print("Executando verificação automática...")
        run_command("python verify_installation.py", "Verificando instalação")
    else:
        print("Arquivo de verificação não encontrado. Instalação concluída.")
    
    print("\n" + "="*60)
    print("INSTALAÇÃO CONCLUÍDA!")
    print("="*60)
    print("\nSe houver problemas, consulte o arquivo INSTALL_WINDOWS.md")
    print("para soluções alternativas.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Instalação bem-sucedida!")
        else:
            print("\n⚠️  Instalação com problemas. Consulte as mensagens acima.")
    except KeyboardInterrupt:
        print("\n\nInstalação interrompida pelo usuário.")
    except Exception as e:
        print(f"\n\nErro inesperado: {e}")
        print("Consulte o arquivo INSTALL_WINDOWS.md para soluções manuais.") 