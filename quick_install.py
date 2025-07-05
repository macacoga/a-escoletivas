#!/usr/bin/env python3
"""
Script de instalação rápida com múltiplas estratégias
Tenta diferentes métodos para resolver problemas de compatibilidade.
"""

import subprocess
import sys
import os
import platform

def run_command(cmd, description="", ignore_errors=False):
    """Executa um comando e retorna True se bem-sucedido"""
    if description:
        print(f"→ {description}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Sucesso")
            return True
        else:
            if not ignore_errors:
                print(f"✗ Erro: {result.stderr}")
            return False
    except Exception as e:
        if not ignore_errors:
            print(f"✗ Erro: {e}")
        return False

def check_conda():
    """Verifica se conda está disponível"""
    return run_command("conda --version", ignore_errors=True)

def method_1_precompiled():
    """Método 1: Instalar usando wheels pré-compilados"""
    print("\n" + "="*50)
    print("MÉTODO 1: WHEELS PRÉ-COMPILADOS")
    print("="*50)
    
    # Atualizar pip
    run_command("python -m pip install --upgrade pip", "Atualizando pip")
    
    # Instalar pacotes científicos com wheels
    scientific_packages = ["numpy", "pandas", "scikit-learn", "scipy"]
    
    for package in scientific_packages:
        success = run_command(
            f"pip install --only-binary={package} {package}",
            f"Instalando {package} (wheel)"
        )
        if not success:
            print(f"Tentando {package} sem restrições...")
            run_command(f"pip install {package}", f"Instalando {package}")
    
    # Instalar o resto
    print("\nInstalando outras dependências...")
    return run_command("pip install -r requirements.txt", "Instalando requirements.txt")

def method_2_conda():
    """Método 2: Usar conda para pacotes científicos"""
    print("\n" + "="*50)
    print("MÉTODO 2: CONDA + PIP")
    print("="*50)
    
    if not check_conda():
        print("Conda não encontrado. Pulando este método.")
        return False
    
    # Instalar pacotes científicos via conda
    scientific_packages = ["numpy", "pandas", "scikit-learn", "scipy"]
    
    for package in scientific_packages:
        run_command(f"conda install -y {package}", f"Instalando {package} via conda")
    
    # NLP packages via conda
    nlp_packages = ["spacy", "nltk"]
    for package in nlp_packages:
        run_command(f"conda install -y -c conda-forge {package}", f"Instalando {package} via conda")
    
    # Resto via pip
    basic_packages = [
        "flask", "flask-restx", "flask-cors", "marshmallow", "waitress",
        "beautifulsoup4", "selenium", "lxml", "openpyxl",
        "sumy", "textstat", "bleach", "html2text", "wordcloud",
        "python-dotenv", "click", "tqdm", "colorama", "structlog",
        "jsonschema", "pydantic", "pydantic-settings",
        "sqlalchemy", "alembic", "python-dateutil",
        "requests", "transformers"
    ]
    
    for package in basic_packages:
        run_command(f"pip install {package}", f"Instalando {package}")
    
    return True

def method_3_windows_specific():
    """Método 3: Versões específicas para Windows"""
    print("\n" + "="*50)
    print("MÉTODO 3: VERSÕES ESPECÍFICAS WINDOWS")
    print("="*50)
    
    return run_command("pip install -r requirements-windows.txt", "Instalando requirements-windows.txt")

def method_4_minimal():
    """Método 4: Instalação mínima essencial"""
    print("\n" + "="*50)
    print("MÉTODO 4: INSTALAÇÃO MÍNIMA")
    print("="*50)
    
    essential_packages = [
        "requests", "beautifulsoup4", "selenium", "lxml", "openpyxl",
        "flask", "flask-restx", "flask-cors", "marshmallow",
        "python-dotenv", "click", "tqdm", "colorama", "sqlalchemy"
    ]
    
    success = True
    for package in essential_packages:
        if not run_command(f"pip install {package}", f"Instalando {package}"):
            success = False
    
    return success

def install_nlp_models():
    """Instala modelos de NLP se possível"""
    print("\n" + "="*50)
    print("INSTALANDO MODELOS DE NLP")
    print("="*50)
    
    # spaCy model
    if run_command("python -c \"import spacy\"", ignore_errors=True):
        run_command("python -m spacy download pt_core_news_sm", "Baixando modelo spaCy")
    
    # NLTK data
    if run_command("python -c \"import nltk\"", ignore_errors=True):
        nltk_data = ["punkt", "stopwords", "wordnet"]
        for data in nltk_data:
            run_command(
                f"python -c \"import nltk; nltk.download('{data}')\"",
                f"Baixando {data}"
            )

def main():
    """Função principal - tenta diferentes métodos"""
    print("="*60)
    print("INSTALAÇÃO RÁPIDA - PROJETO AÇÕES COLETIVAS")
    print("="*60)
    
    print(f"Sistema: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    
    # Tenta diferentes métodos em ordem de preferência
    methods = [
        ("Wheels pré-compilados", method_1_precompiled),
        ("Conda + pip", method_2_conda),
        ("Versões específicas Windows", method_3_windows_specific),
        ("Instalação mínima", method_4_minimal),
    ]
    
    success = False
    for method_name, method_func in methods:
        print(f"\n🔄 Tentando: {method_name}")
        try:
            if method_func():
                print(f"✓ Sucesso com: {method_name}")
                success = True
                break
        except Exception as e:
            print(f"✗ Falha com {method_name}: {e}")
    
    if not success:
        print("\n❌ Todos os métodos falharam!")
        print("Sugestões:")
        print("1. Instale o Microsoft Build Tools")
        print("2. Use o Anaconda/Miniconda")
        print("3. Consulte INSTALL_WINDOWS.md")
        return False
    
    # Tentar instalar modelos de NLP
    install_nlp_models()
    
    # Verificar instalação
    print("\n" + "="*50)
    print("VERIFICANDO INSTALAÇÃO")
    print("="*50)
    
    if os.path.exists("verify_installation.py"):
        run_command("python verify_installation.py", "Executando verificação")
    
    print("\n" + "="*60)
    print("INSTALAÇÃO CONCLUÍDA!")
    print("="*60)
    print("Próximos passos:")
    print("1. Execute: python verify_installation.py")
    print("2. Configure o banco: python -c \"from src.acoes_coletivas.database.manager import DatabaseManager; DatabaseManager().create_tables()\"")
    print("3. Teste a API: python app.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Instalação bem-sucedida!")
        else:
            print("\n⚠️  Problemas na instalação. Consulte as instruções acima.")
    except KeyboardInterrupt:
        print("\n\nInstalação interrompida pelo usuário.")
    except Exception as e:
        print(f"\n\nErro inesperado: {e}")
        print("Consulte README_INSTALACAO.md para instruções manuais.") 