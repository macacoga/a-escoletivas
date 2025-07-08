"""
Aplicação Flask principal para API RESTful
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restx import Api, Namespace
import logging
from datetime import datetime

from ..database.manager import DatabaseManager
from ..config.settings import settings
from ..utils.logging import setup_logging, get_logger


def create_app(config_name: str = 'production'):
    """Cria e configura a aplicação Flask"""
    
    app = Flask(__name__)
    
    # Configuração básica
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Configuração de ambiente
    if config_name == 'development':
        app.config['DEBUG'] = True
        app.config['TESTING'] = False
    elif config_name == 'testing':
        app.config['DEBUG'] = False
        app.config['TESTING'] = True
    else:
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
    
    # Configurar CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Configurar logging
    setup_logging(
        level="DEBUG" if app.config['DEBUG'] else "INFO",
        log_file=None,  # Log apenas no console para API
        json_format=True
    )
    
    # Configurar API com documentação
    api = Api(
        app,
        version='1.0.0',
        title='Ações Coletivas API',
        description='API RESTful para análise de ações coletivas trabalhistas',
        doc='/api/docs/',
        prefix='/api'
    )
    
    # Registrar blueprints/namespaces
    from .routes.acoes import acoes_ns
    from .routes.topicos import topicos_ns
    from .routes.stats import stats_ns
    
    api.add_namespace(acoes_ns, path='/acoes')
    api.add_namespace(topicos_ns, path='/topicos')
    api.add_namespace(stats_ns, path='/stats')
    
    # Middleware para logging de requests
    @app.before_request
    def log_request_info():
        logger = get_logger("API")
        logger.info(f"Request: {request.method} {request.url}")
    
    # Handler de erro global
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status': 404,
            'timestamp': datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger = get_logger("API")
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An internal server error occurred',
            'status': 500,
            'timestamp': datetime.now().isoformat()
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood or was missing required parameters',
            'status': 400,
            'timestamp': datetime.now().isoformat()
        }), 400
    
    # Endpoint de health check
    @app.route('/health')
    def health_check():
        """Endpoint para verificação de saúde da API"""
        try:
            # Testar conexão com banco
            db = DatabaseManager()
            stats = db.get_stats()
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'database': {
                    'connected': True,
                    'total_processos': stats.get('total_processos', 0)
                }
            })
        except Exception as e:
            logger = get_logger("API")
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'error': str(e)
            }), 503
    
    # Endpoint raiz da API
    @app.route('/api')
    def api_info():
        """Informações básicas da API"""
        return jsonify({
            'name': 'Ações Coletivas API',
            'version': '1.0.0',
            'description': 'API RESTful para análise de ações coletivas trabalhistas',
            'endpoints': {
                'acoes': '/api/acoes',
                'search': '/api/acoes/search',
                'topicos': '/api/topicos',
                'stats': '/api/stats',
                'docs': '/api/docs/'
            },
            'timestamp': datetime.now().isoformat()
        })
    
    return app


def get_database():
    """Obtém instância do gerenciador de banco de dados"""
    db_path = str(settings.database_url.replace("sqlite:///", ""))
    return DatabaseManager(db_path)


if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000, debug=True) 