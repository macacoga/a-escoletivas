# API RESTful - Ações Coletivas

## Visão Geral

Esta API fornece acesso aos dados processados do sistema de análise de ações coletivas trabalhistas. Ela permite consultar processos judiciais, buscar com filtros avançados, obter tópicos frequentes e visualizar estatísticas.

## Base URL

```
http://localhost:5000/api
```

## Autenticação

Atualmente, a API não requer autenticação. Para produção, recomenda-se implementar autenticação JWT ou similar.

## Formato das Respostas

Todas as respostas são em formato JSON com estrutura padronizada:

```json
{
  "data": {...},
  "pagination": {...},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Endpoints

### 1. Informações da API

#### GET /api
Retorna informações básicas da API.

**Resposta:**
```json
{
  "name": "Ações Coletivas API",
  "version": "1.0.0",
  "description": "API RESTful para análise de ações coletivas trabalhistas",
  "endpoints": {
    "acoes": "/api/acoes",
    "search": "/api/acoes/search",
    "topicos": "/api/topicos",
    "stats": "/api/stats"
  }
}
```

### 2. Health Check

#### GET /health
Verifica a saúde da API e conexão com banco de dados.

**Resposta:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "database": {
    "connected": true,
    "total_processos": 1250
  }
}
```

## Ações Coletivas

### 3. Listar Ações

#### GET /api/acoes
Lista todas as ações coletivas com paginação.

**Parâmetros:**
- `page` (int): Página (padrão: 1)
- `per_page` (int): Itens por página (padrão: 20, máx: 100)
- `include_content` (bool): Incluir conteúdo completo (padrão: false)

**Exemplo:**
```bash
curl "http://localhost:5000/api/acoes?page=1&per_page=10"
```

**Resposta:**
```json
{
  "data": [
    {
      "id": 1,
      "numero_processo": "0001234-56.2023.5.10.0001",
      "tribunal": "TRT10",
      "data_publicacao": "2023-12-15",
      "partes": "Sindicato dos Trabalhadores vs. Empresa XYZ",
      "processado_nlp": true,
      "tema_principal": "horas_extras",
      "qualidade_texto": 0.85,
      "confianca_global": 0.92
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 1250,
    "pages": 125,
    "has_next": true,
    "has_prev": false
  }
}
```

### 4. Obter Ação Específica

#### GET /api/acoes/{id}
Retorna detalhes completos de uma ação coletiva.

**Parâmetros:**
- `include_content` (bool): Incluir conteúdo completo (padrão: true)

**Exemplo:**
```bash
curl "http://localhost:5000/api/acoes/1"
```

**Resposta:**
```json
{
  "id": 1,
  "numero_processo": "0001234-56.2023.5.10.0001",
  "tribunal": "TRT10",
  "classe_processo": "Ação Coletiva",
  "data_julgamento": "2023-12-10",
  "data_publicacao": "2023-12-15",
  "relator": "Desembargador João Silva",
  "partes": "Sindicato dos Trabalhadores vs. Empresa XYZ",
  "processado_nlp": true,
  "conteudo_bruto_decisao": "Texto completo da decisão...",
  "resultado_nlp": {
    "resumo_extrativo": "Resumo do processo...",
    "tema_principal": "horas_extras",
    "qualidade_texto": 0.85,
    "confianca_global": 0.92,
    "entidades": [
      {
        "text": "Empresa XYZ",
        "label": "ORG",
        "confidence": 0.95
      }
    ],
    "direitos_trabalhistas": [
      {
        "type": "overtime",
        "description": "Horas extras",
        "decision_outcome": "granted",
        "confidence": 0.88
      }
    ]
  }
}
```

### 5. Buscar Ações

#### GET /api/acoes/search
Busca ações coletivas com filtros avançados.

**Parâmetros:**
- `page` (int): Página
- `per_page` (int): Itens por página
- `numero_processo` (str): Número do processo
- `tribunal` (str): Tribunal
- `partes` (str): Partes envolvidas
- `keywords` (str): Palavras-chave
- `data_publicacao_inicio` (date): Data início (YYYY-MM-DD)
- `data_publicacao_fim` (date): Data fim (YYYY-MM-DD)
- `processado_nlp` (bool): Processado pelo NLP
- `tema_principal` (str): Tema principal
- `qualidade_minima` (float): Qualidade mínima (0-1)
- `direito_trabalhista` (str): Direito trabalhista
- `sort_by` (str): Ordenar por
- `sort_order` (str): Ordem (asc/desc)

**Exemplo:**
```bash
curl "http://localhost:5000/api/acoes/search?keywords=horas%20extras&qualidade_minima=0.8&sort_by=data_publicacao"
```

## Tópicos

### 6. Listar Tópicos

#### GET /api/topicos
Lista os tópicos mais frequentes encontrados nas decisões.

**Parâmetros:**
- `limite` (int): Limite de tópicos por categoria (padrão: 20)
- `apenas_nlp` (bool): Apenas processos com NLP (padrão: true)

**Exemplo:**
```bash
curl "http://localhost:5000/api/topicos?limite=10"
```

**Resposta:**
```json
{
  "temas_principais": [
    {
      "nome": "horas_extras",
      "descricao": "Horas extras",
      "frequencia": 145,
      "porcentagem": 15.2
    }
  ],
  "direitos_trabalhistas": [
    {
      "nome": "overtime",
      "descricao": "Horas extras",
      "frequencia": 178,
      "porcentagem": 18.7
    }
  ],
  "tribunais": [
    {
      "nome": "TRT10",
      "descricao": "Tribunal Regional do Trabalho da 10ª Região",
      "frequencia": 256,
      "porcentagem": 26.9
    }
  ]
}
```

### 7. Direitos Trabalhistas

#### GET /api/topicos/direitos
Lista direitos trabalhistas com estatísticas detalhadas.

**Parâmetros:**
- `limite` (int): Limite de direitos
- `resultado` (str): Filtrar por resultado (granted/denied/partially_granted)
- `detalhado` (bool): Incluir detalhes das decisões

**Exemplo:**
```bash
curl "http://localhost:5000/api/topicos/direitos?resultado=granted&detalhado=true"
```

## Estatísticas

### 8. Estatísticas Gerais

#### GET /api/stats/geral
Estatísticas gerais do sistema.

**Resposta:**
```json
{
  "total_processos": 1250,
  "processos_processados": 1180,
  "resultados_nlp": 1150,
  "tribunais_unicos": 15,
  "qualidade_media": 0.762,
  "confianca_media": 0.845,
  "tempo_processamento_medio": 2.3
}
```

### 9. Distribuição

#### GET /api/stats/distribuicao
Distribuição por categoria.

**Parâmetros:**
- `categoria` (str): tribunal, qualidade, tema, direito
- `limite` (int): Limite de resultados

**Exemplo:**
```bash
curl "http://localhost:5000/api/stats/distribuicao?categoria=tribunal&limite=5"
```

### 10. Timeline

#### GET /api/stats/timeline
Estatísticas temporais.

**Parâmetros:**
- `periodo` (str): dia, semana, mes, ano
- `limite` (int): Limite de períodos

### 11. Qualidade NLP

#### GET /api/stats/qualidade
Estatísticas de qualidade do processamento NLP.

**Resposta:**
```json
{
  "qualidade_texto": {
    "media": 0.762,
    "mediana": 0.780,
    "desvio_padrao": 0.156
  },
  "distribuicao_qualidade": {
    "excelente": {
      "quantidade": 234,
      "porcentagem": 20.4
    }
  },
  "taxa_sucesso": {
    "resumo": 94.5,
    "tema": 87.2,
    "direitos": 91.8
  }
}
```

## Códigos de Status

- `200 OK`: Sucesso
- `400 Bad Request`: Parâmetros inválidos
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro interno

## Tratamento de Erros

Erros retornam estrutura padronizada:

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

## Paginação

Endpoints que retornam listas incluem metadados de paginação:

```json
{
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1250,
    "pages": 63,
    "has_next": true,
    "has_prev": false,
    "next_page": 2,
    "prev_page": null
  }
}
```

## Exemplos de Uso

### Buscar processos sobre horas extras

```bash
curl "http://localhost:5000/api/acoes/search?keywords=horas%20extras&processado_nlp=true"
```

### Obter estatísticas de qualidade

```bash
curl "http://localhost:5000/api/stats/qualidade"
```

### Listar tópicos mais frequentes

```bash
curl "http://localhost:5000/api/topicos?limite=10"
```

## Documentação Interativa

A API inclui documentação interativa Swagger/OpenAPI disponível em:
- `/api/docs/` - Interface Swagger UI

## Execução da API

### Desenvolvimento

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export FLASK_ENV=development
export DATABASE_URL=sqlite:///data/acoes_coletivas.db

# Executar
python app.py
```

### Produção

```bash
# Usar Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Ou Waitress
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

## Considerações de Performance

- Use paginação para grandes conjuntos de dados
- Evite `include_content=true` em listagens
- Implemente cache para consultas frequentes
- Monitore uso de recursos com muitos filtros

## Suporte

Para suporte técnico ou dúvidas sobre a API, consulte:
- Documentação completa no código
- Logs da aplicação
- Exemplos de uso em `examples/` 