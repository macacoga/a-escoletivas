#!/usr/bin/env python3
"""
Ferramenta de Análise de Ações Coletivas
Ponto de entrada principal para a aplicação
"""

import sys
from pathlib import Path

# Adicionar src ao Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from acoes_coletivas.cli.main import main

if __name__ == "__main__":
    main() 