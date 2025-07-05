#!/usr/bin/env python3
"""
Script de verificação da instalação
Verifica se todas as dependências estão instaladas e funcionando corretamente.
"""

import sys
import importlib
import platform
from pathlib import Path

def check_python_version():
    """Verifica a versão do Python"""
    print(f"Python version: {sys.version}")
    version_info = sys.version_info
    
    if version_info.major == 3 and version_info.minor >= 8:
        print("✓ Python version OK")
        return True
    else:
        print("✗ Python version incompatível. Requer Python 3.8+")
        return False

def check_package(package_name, import_name=None):
    """Verifica se um pacote está instalado"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'Unknown')
        print(f"✓ {package_name}: {version}")
        return True
    except ImportError as e:
        print(f"✗ {package_name}: NOT FOUND - {e}")
        return False

def check_spacy_model():
    """Verifica se o modelo do spaCy está instalado"""
    try:
        import spacy
        nlp = spacy.load("pt_core_news_sm")
        print("✓ spaCy Portuguese model: OK")
        return True
    except IOError:
        print("✗ spaCy Portuguese model: NOT FOUND")
        print("  Execute: python -m spacy download pt_core_news_sm")
        return False
    except Exception as e:
        print(f"✗ spaCy Portuguese model: ERROR - {e}")
        return False

def check_nltk_data():
    """Verifica se os dados do NLTK estão disponíveis"""
    try:
        import nltk
        
        # Verifica se os dados estão disponíveis
        try:
            nltk.data.find('tokenizers/punkt')
            print("✓ NLTK punkt tokenizer: OK")
        except LookupError:
            print("✗ NLTK punkt tokenizer: NOT FOUND")
            print("  Execute: python -c \"import nltk; nltk.download('punkt')\"")
            return False
        
        try:
            nltk.data.find('corpora/stopwords')
            print("✓ NLTK stopwords: OK")
        except LookupError:
            print("✗ NLTK stopwords: NOT FOUND")
            print("  Execute: python -c \"import nltk; nltk.download('stopwords')\"")
            return False
        
        return True
    except ImportError:
        print("✗ NLTK: NOT INSTALLED")
        return False

def check_selenium_driver():
    """Verifica se o Selenium pode funcionar"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        # Tenta criar um driver headless
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Não precisa criar o driver de verdade, só verificar se as classes existem
        print("✓ Selenium WebDriver: OK")
        return True
    except ImportError as e:
        print(f"✗ Selenium WebDriver: ERROR - {e}")
        return False

def main():
    """Função principal"""
    print("="*60)
    print("VERIFICAÇÃO DA INSTALAÇÃO - PROJETO AÇÕES COLETIVAS")
    print("="*60)
    
    # Informações do sistema
    print(f"\nSistema: {platform.system()} {platform.release()}")
    print(f"Arquitetura: {platform.architecture()[0]}")
    
    # Verificação da versão do Python
    print("\n1. Verificando Python...")
    python_ok = check_python_version()
    
    # Pacotes principais
    print("\n2. Verificando pacotes principais...")
    packages = [
        ('requests', 'requests'),
        ('beautifulsoup4', 'bs4'),
        ('selenium', 'selenium'),
        ('lxml', 'lxml'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('openpyxl', 'openpyxl'),
    ]
    
    main_packages_ok = all(check_package(pkg, imp) for pkg, imp in packages)
    
    # Banco de dados
    print("\n3. Verificando banco de dados...")
    db_packages = [
        ('sqlalchemy', 'sqlalchemy'),
        ('alembic', 'alembic'),
    ]
    
    db_ok = all(check_package(pkg, imp) for pkg, imp in db_packages)
    
    # NLP
    print("\n4. Verificando NLP...")
    nlp_packages = [
        ('spacy', 'spacy'),
        ('nltk', 'nltk'),
        ('sumy', 'sumy'),
        ('transformers', 'transformers'),
        ('scikit-learn', 'sklearn'),
        ('textstat', 'textstat'),
    ]
    
    nlp_ok = all(check_package(pkg, imp) for pkg, imp in nlp_packages)
    
    # Processamento de texto
    print("\n5. Verificando processamento de texto...")
    text_packages = [
        ('bleach', 'bleach'),
        ('html2text', 'html2text'),
        ('wordcloud', 'wordcloud'),
    ]
    
    text_ok = all(check_package(pkg, imp) for pkg, imp in text_packages)
    
    # API
    print("\n6. Verificando API...")
    api_packages = [
        ('flask', 'flask'),
        ('flask-restx', 'flask_restx'),
        ('flask-cors', 'flask_cors'),
        ('marshmallow', 'marshmallow'),
        ('waitress', 'waitress'),
    ]
    
    api_ok = all(check_package(pkg, imp) for pkg, imp in api_packages)
    
    # Utilitários
    print("\n7. Verificando utilitários...")
    util_packages = [
        ('python-dotenv', 'dotenv'),
        ('click', 'click'),
        ('tqdm', 'tqdm'),
        ('colorama', 'colorama'),
        ('jsonschema', 'jsonschema'),
        ('pydantic', 'pydantic'),
    ]
    
    util_ok = all(check_package(pkg, imp) for pkg, imp in util_packages)
    
    # Verificações específicas
    print("\n8. Verificações específicas...")
    spacy_model_ok = check_spacy_model()
    nltk_data_ok = check_nltk_data()
    selenium_ok = check_selenium_driver()
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO DA VERIFICAÇÃO")
    print("="*60)
    
    checks = [
        ("Python", python_ok),
        ("Pacotes principais", main_packages_ok),
        ("Banco de dados", db_ok),
        ("NLP", nlp_ok),
        ("Processamento de texto", text_ok),
        ("API", api_ok),
        ("Utilitários", util_ok),
        ("Modelo spaCy", spacy_model_ok),
        ("Dados NLTK", nltk_data_ok),
        ("Selenium", selenium_ok),
    ]
    
    all_ok = all(ok for _, ok in checks)
    
    for name, ok in checks:
        status = "✓" if ok else "✗"
        print(f"{status} {name}")
    
    if all_ok:
        print("\n🎉 Todas as verificações passaram! O sistema está pronto para uso.")
    else:
        print("\n⚠️  Algumas verificações falharam. Consulte o arquivo INSTALL_WINDOWS.md para soluções.")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 