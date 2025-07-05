# API RESTful - Ações Coletivas Trabalhistas

## 🚀 Visão Geral

Esta API RESTful fornece acesso completo aos dados processados do sistema de análise de ações coletivas trabalhistas. Ela oferece endpoints para consultar processos judiciais, buscar com filtros avançados, analisar tópicos frequentes e visualizar estatísticas detalhadas.

## 📋 Características

- **RESTful**: Arquitetura REST com endpoints padronizados
- **Documentação Automática**: Swagger/OpenAPI integrado
- **Paginação**: Suporte a paginação em todas as listagens
- **Filtros Avançados**: Busca por múltiplos critérios
- **Serialização**: Respostas JSON estruturadas com Marshmallow
- **Tratamento de Erros**: Respostas de erro padronizadas
- **Performance**: Otimizada para consultas eficientes
- **Logging**: Sistema de logs detalhado

## 🏗️ Arquitetura

```
src/acoes_coletivas/api/
├── __init__.py
├── app.py                 # Aplicação Flask principal
├── schemas.py             # Schemas Marshmallow
├── routes/
│   ├── __init__.py
│   ├── acoes.py          # Endpoints das ações
│   ├── topicos.py        # Endpoints dos tópicos
│   └── stats.py          # Endpoints das estatísticas
app.py                     # Arquivo principal da API
test_api.py               # Script de testes
start_api.py              # Script de inicialização
```

## 🔧 Instalação e Execução

### Método 1: Script Automático (Recomendado)

```bash
# Instalar e executar automaticamente
python start_api.py
```

### Método 2: Manual

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Instalar modelo spaCy
python install_spacy_model.py

# 3. Configurar variáveis de ambiente
export FLASK_ENV=development
export DATABASE_URL=sqlite:///data/acoes_coletivas.db

# 4. Executar API
python app.py
```

### Método 3: Produção

```bash
# Usando Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Usando Waitress (incluído nas dependências)
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

## 🌐 Endpoints

### 📊 Informações Gerais

- **GET /health** - Health check da API
- **GET /api** - Informações da API
- **GET /api/docs/** - Documentação Swagger

### 📋 Ações Coletivas

- **GET /api/acoes** - Listar ações com paginação
- **GET /api/acoes/{id}** - Obter ação específica
- **GET /api/acoes/search** - Buscar ações com filtros

### 🏷️ Tópicos e Temas

- **GET /api/topicos** - Listar tópicos frequentes
- **GET /api/topicos/direitos** - Direitos trabalhistas detalhados

### 📈 Estatísticas

- **GET /api/stats/geral** - Estatísticas gerais
- **GET /api/stats/distribuicao** - Distribuição por categoria
- **GET /api/stats/timeline** - Estatísticas temporais
- **GET /api/stats/qualidade** - Qualidade do processamento NLP

## 🧪 Testes

```bash
# Executar todos os testes
python test_api.py

# Teste específico
python test_api.py --test health

# Teste com detalhes
python test_api.py --verbose

# Teste em URL diferente
python test_api.py --url http://localhost:8000
```

## 🔍 Exemplos de Uso

### Listar Ações

```bash
curl "http://localhost:5000/api/acoes?page=1&per_page=10"
```

### Buscar por Palavras-chave

```bash
curl "http://localhost:5000/api/acoes/search?keywords=horas%20extras&processado_nlp=true"
```

### Obter Estatísticas

```bash
curl "http://localhost:5000/api/stats/geral"
```

### Filtrar por Tribunal

```bash
curl "http://localhost:5000/api/acoes/search?tribunal=TRT10&qualidade_minima=0.8"
```

## 📱 Estrutura das Respostas

### Sucesso (200 OK)

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1250,
    "pages": 63,
    "has_next": true,
    "has_prev": false
  },
  "total_found": 1250,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Erro (400/404/500)

```json
{
  "error": "Bad Request",
  "message": "Parâmetros inválidos",
  "status": 400,
  "timestamp": "2024-01-15T10:30:00Z",
  "details": {
    "campo": "erro específico"
  }
}
```

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Configurações da API
FLASK_ENV=development          # development/production
HOST=0.0.0.0                  # Host da API
PORT=5000                     # Porta da API
SECRET_KEY=your-secret-key    # Chave secreta

# Banco de dados
DATABASE_URL=sqlite:///data/acoes_coletivas.db

# Logging
LOG_LEVEL=INFO               # DEBUG/INFO/WARNING/ERROR
LOG_FILE=logs/api.log        # Arquivo de log (opcional)
LOG_JSON_FORMAT=true         # Formato JSON para logs

# Performance
MAX_CONTENT_LENGTH=16777216  # Tamanho máximo do conteúdo
THREADS=6                    # Número de threads
```

### Arquivo de Configuração

Copie `config.env.example` para `config.env` e ajuste as configurações.

## 🚀 Performance

### Otimizações Implementadas

- **Paginação**: Limitação de resultados por página
- **Índices**: Índices otimizados no banco de dados
- **Conexões**: Pool de conexões SQLite
- **Serialização**: Schemas Marshmallow otimizados
- **Logging**: Logging estruturado para monitoramento

### Recomendações

- Use paginação (`per_page` máximo: 100)
- Evite `include_content=true` em listagens grandes
- Implemente cache para consultas frequentes
- Monitore logs para identificar consultas lentas

## 🔒 Segurança

### Implementado

- **CORS**: Configuração de CORS para acesso cross-origin
- **Validação**: Validação de entrada com Marshmallow
- **Sanitização**: Sanitização de parâmetros SQL
- **Logging**: Log de todas as requisições

### Recomendações para Produção

- Implementar autenticação JWT
- Configurar HTTPS
- Usar proxy reverso (Nginx)
- Implementar rate limiting
- Configurar firewall

## 📊 Monitoramento

### Logs

```bash
# Logs da aplicação
tail -f logs/api.log

# Logs estruturados (JSON)
tail -f logs/api.log | jq .
```

### Métricas

- **Health Check**: `/health`
- **Estatísticas**: `/api/stats/geral`
- **Performance**: Tempo de resposta nos logs

## 🐛 Troubleshooting

### Problemas Comuns

1. **Erro 404 - API não encontrada**
   - Verifique se a API está rodando
   - Confirme a URL base correta

2. **Erro 500 - Erro interno**
   - Verifique os logs da aplicação
   - Confirme se o banco de dados está acessível

3. **Erro de conexão com banco**
   - Verifique se o arquivo `data/acoes_coletivas.db` existe
   - Execute os scripts de coleta de dados

4. **Dependências em falta**
   - Execute `pip install -r requirements.txt`
   - Instale o modelo spaCy: `python install_spacy_model.py`

### Comandos de Diagnóstico

```bash
# Verificar dependências
pip list | grep -E "(flask|marshmallow|spacy)"

# Testar conexão com banco
python -c "from src.acoes_coletivas.database.manager import DatabaseManager; print(DatabaseManager().get_stats())"

# Verificar modelo spaCy
python -c "import spacy; nlp = spacy.load('pt_core_news_sm'); print('Modelo OK')"
```

## 📚 Documentação Adicional

- **Documentação Completa**: `docs/API.md`
- **Documentação Interativa**: `http://localhost:5000/api/docs/`
- **Exemplos de Código**: `examples/`
- **Schemas**: Documentação dos schemas em `src/acoes_coletivas/api/schemas.py`

## 🤝 Contribuição

1. **Desenvolvimento**: Use `FLASK_ENV=development`
2. **Testes**: Execute `python test_api.py` antes de commits
3. **Documentação**: Mantenha a documentação atualizada
4. **Performance**: Monitore impacto nos tempos de resposta

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🔄 Versionamento

- **v1.0.0**: Versão inicial com endpoints básicos
- **Futuro**: Autenticação, cache, websockets para notificações

## 📞 Suporte

Para suporte técnico:
- Verifique os logs em `logs/api.log`
- Execute testes com `python test_api.py`
- Consulte documentação em `docs/API.md`
- Verifique exemplos em `examples/`

---

**Feito com ❤️ para análise de ações coletivas trabalhistas** 