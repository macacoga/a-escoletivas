#!/usr/bin/env python3
"""
Arquivo principal da API Flask para Ações Coletivas
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório src ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.acoes_coletivas.api.app import create_app
from src.acoes_coletivas.utils.logging import setup_logging, get_logger

# Configurar logging
setup_logging(
    level="INFO",
    log_file=None,  # Console apenas
    json_format=True
)

logger = get_logger("API.Main")

# Criar aplicação Flask
app = create_app(
    config_name=os.environ.get('FLASK_ENV', 'production')
)

if __name__ == '__main__':
    try:
        # Configurações do servidor
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV') == 'development'
        
        logger.info(f"Iniciando API em {host}:{port} (debug={debug})")
        
        if debug:
            # Modo desenvolvimento
            app.run(host=host, port=port, debug=True, threaded=True)
        else:
            # Modo produção - usar waitress
            try:
                from waitress import serve
                logger.info("Usando Waitress para servir a aplicação")
                serve(app, host=host, port=port, threads=6)
            except ImportError:
                logger.warning("Waitress não encontrado, usando servidor Flask padrão")
                app.run(host=host, port=port, debug=False, threaded=True)
                
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
        sys.exit(1) 