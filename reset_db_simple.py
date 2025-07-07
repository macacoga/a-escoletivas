#!/usr/bin/env python3
"""
Script simples para resetar o banco de dados
"""

import os
import sys
from pathlib import Path
import shutil
from datetime import datetime

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.acoes_coletivas.config.settings import settings
from src.acoes_coletivas.database.manager import DatabaseManager


def reset_database_simple():
    """Reseta o banco de dados de forma simples"""
    
    print("="*50)
    print("RESET SIMPLES DO BANCO DE DADOS")
    print("="*50)
    
    # Obter caminho do banco de dados
    db_path = str(settings.database_url.replace("sqlite:///", ""))
    db_file = Path(db_path)
    
    print(f"📁 Banco: {db_file}")
    
    # Fazer backup se existir
    if db_file.exists():
        backup_dir = Path("data/backup")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.db"
        
        print(f"💾 Backup: {backup_file}")
        try:
            shutil.copy2(db_file, backup_file)
            print("   ✅ Backup criado")
        except Exception as e:
            print(f"   ⚠️  Erro no backup: {e}")
        
        # Remover banco atual
        print("🗑️  Removendo banco atual...")
        try:
            os.remove(db_file)
            print("   ✅ Banco removido")
        except Exception as e:
            print(f"   ❌ Erro ao remover: {e}")
            return False
    
    # Criar novo banco
    print("🔧 Criando novo banco...")
    try:
        # Garantir diretório
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar banco
        db = DatabaseManager(str(db_file))
        
        # Verificar tabelas
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
        
        print(f"   ✅ Banco criado")
        print(f"   📋 Tabelas: {', '.join(tables)}")
        
        # Estatísticas
        stats = db.get_stats()
        print(f"\n📊 Banco vazio:")
        print(f"   Processos: {stats.get('total_processos', 0)}")
        print(f"   NLP: {stats.get('resultados_nlp', 0)}")
        
        print(f"\n✅ Reset concluído!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


if __name__ == "__main__":
    print("Resetando banco de dados...")
    success = reset_database_simple()
    
    if success:
        print("\n🔄 Próximos passos:")
        print("   1. python acoes_coletivas.py import -f arquivo.xlsx -c coluna")
        print("   2. python acoes_coletivas.py scrape")
        print("   3. python acoes_coletivas.py nlp process")
    else:
        print("\n❌ Reset falhou")
        sys.exit(1) 