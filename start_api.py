#!/usr/bin/env python3
"""
Script para iniciar a API com verificação de dependências
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Verifica se a versão do Python é adequada"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou superior é necessário")
        print(f"   Versão atual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_dependencies():
    """Instala as dependências necessárias"""
    print("📦 Instalando dependências...")
    
    try:
        # Instalar dependências principais
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True)
        
        print("✅ Dependências instaladas com sucesso")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        print(f"   Saída: {e.stdout.decode()}")
        print(f"   Erro: {e.stderr.decode()}")
        return False

def install_spacy_model():
    """Instala o modelo spaCy português"""
    print("🤖 Instalando modelo spaCy português...")
    
    try:
        # Executar script de instalação do modelo
        if os.path.exists("install_spacy_model.py"):
            subprocess.run([sys.executable, "install_spacy_model.py"], check=True)
            print("✅ Modelo spaCy instalado com sucesso")
        else:
            print("⚠️  Script install_spacy_model.py não encontrado")
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar modelo spaCy: {e}")
        return False

def create_directories():
    """Cria diretórios necessários"""
    print("📁 Criando diretórios...")
    
    directories = [
        "data",
        "logs",
        "data/backup"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   📁 {directory}")
    
    print("✅ Diretórios criados")

def check_database():
    """Verifica se o banco de dados existe"""
    print("🗄️  Verificando banco de dados...")
    
    db_path = Path("data/acoes_coletivas.db")
    
    if db_path.exists():
        print(f"✅ Banco encontrado: {db_path}")
        print(f"   Tamanho: {db_path.stat().st_size / (1024*1024):.2f} MB")
        return True
    else:
        print("⚠️  Banco de dados não encontrado")
        print("   Execute primeiro os scripts de coleta de dados:")
        print("   1. python '1 - extrair dados selenium.py'")
        print("   2. python '2 - resumo etapa 1.py'")
        print("   3. python '3 - resumo_etapa_2.py'")
        print("   4. python '4 - última etapa.py'")
        return False

def start_api():
    """Inicia a API"""
    print("🚀 Iniciando API...")
    
    # Configurar variáveis de ambiente
    os.environ['FLASK_ENV'] = 'development'
    os.environ['DATABASE_URL'] = 'sqlite:///data/acoes_coletivas.db'
    
    try:
        # Executar a API
        subprocess.run([sys.executable, "app.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n⏹️  API interrompida pelo usuário")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao iniciar API: {e}")

def main():
    """Função principal"""
    print("🏗️  INICIALIZADOR DA API - AÇÕES COLETIVAS")
    print("=" * 50)
    
    # Verificar Python
    if not check_python_version():
        return
    
    # Criar diretórios
    create_directories()
    
    # Verificar se requirements.txt existe
    if not Path("requirements.txt").exists():
        print("❌ Arquivo requirements.txt não encontrado")
        return
    
    # Instalar dependências
    if not install_dependencies():
        return
    
    # Instalar modelo spaCy
    install_spacy_model()
    
    # Verificar banco de dados
    has_database = check_database()
    
    # Perguntar se deve continuar sem banco
    if not has_database:
        response = input("\n❓ Deseja continuar sem banco de dados? (y/N): ")
        if response.lower() not in ['y', 'yes', 's', 'sim']:
            print("⏹️  Instalação cancelada")
            return
    
    print("\n" + "=" * 50)
    print("🎯 CONFIGURAÇÃO CONCLUÍDA")
    print("=" * 50)
    
    # Mostrar informações da API
    print("\n📋 Informações da API:")
    print("   URL: http://localhost:5000")
    print("   Documentação: http://localhost:5000/api/docs/")
    print("   Health Check: http://localhost:5000/health")
    print("   Endpoints principais:")
    print("     - GET /api/acoes - Listar ações")
    print("     - GET /api/acoes/search - Buscar ações")
    print("     - GET /api/topicos - Listar tópicos")
    print("     - GET /api/stats/geral - Estatísticas")
    
    print("\n💡 Para testar a API:")
    print("   python test_api.py")
    
    # Perguntar se deve iniciar a API
    response = input("\n❓ Deseja iniciar a API agora? (Y/n): ")
    if response.lower() not in ['n', 'no', 'nao', 'não']:
        print("\n🚀 Iniciando API...")
        print("   Pressione Ctrl+C para parar")
        print("   Aguarde alguns segundos para a API inicializar")
        print("=" * 50)
        
        start_api()
    else:
        print("\n💡 Para iniciar a API manualmente:")
        print("   python app.py")

if __name__ == "__main__":
    main() 