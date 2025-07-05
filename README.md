# Ferramenta de Análise de Ações Coletivas

Uma ferramenta profissional para automatizar a coleta, processamento e visualização de dados de ações coletivas judiciais, com foco em execuções individuais pós-conhecimento.

## 🎯 Objetivo

Automatizar o processo de análise de ações coletivas judiciais, permitindo:
- Coleta automática de dados do sistema Falcão
- Processamento de linguagem natural para extrair insights
- Armazenamento estruturado em banco de dados
- Visualização e análise de dados

## 🏗️ Arquitetura

```
src/acoes_coletivas/
├── core/           # Funcionalidades principais
├── scraper/        # Módulos de extração de dados
├── database/       # Gerenciamento de dados
├── nlp/           # Processamento de linguagem natural
├── config/        # Configurações do sistema
└── utils/         # Utilitários diversos
```

## 🚀 Funcionalidades

### Fase 1: Coleta e Armazenamento ✅
- [x] Configuração profissional do ambiente
- [x] Módulo de coleta via Selenium e requests
- [x] Banco de dados SQLite estruturado
- [x] Sistema de logging avançado
- [x] Configuração centralizada
- [x] Tratamento de erros robusto

### Fase 2: Processamento NLP (Em desenvolvimento)
- [ ] Sumarização automática de textos
- [ ] Extração de palavras-chave
- [ ] Classificação de temas
- [ ] Análise de sentimentos
- [ ] Identificação de entidades nomeadas

### Fase 3: Interface e Visualização (Planejado)
- [ ] Interface web com Flask
- [ ] Dashboard interativo
- [ ] Relatórios automatizados
- [ ] Exportação de dados
- [ ] API REST

## 📋 Pré-requisitos

- Python 3.8+
- Chrome ou Firefox (para Selenium)
- Pelo menos 2GB de espaço em disco
- Conexão com internet

## 🔧 Instalação

1. **Clone o repositório:**
```bash
git clone <repository-url>
cd a-escoletivas
```

2. **Crie um ambiente virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure o ambiente:**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

## 🔧 Configuração

### Variáveis de Ambiente

Principais configurações no arquivo `.env`:

```env
# Configurações da aplicação
APP_NAME="Ferramenta de Análise de Ações Coletivas"
DEBUG=false

# Configurações do banco de dados
DATABASE_URL="sqlite:///./data/acoes_coletivas.db"

# Configurações do scraper
SELENIUM_TIMEOUT=30
REQUEST_DELAY=2.0
SELENIUM_HEADLESS=true

# Configurações de busca
DEFAULT_DEFENDANT="Banco do Brasil"
DEFAULT_COLLECTIONS=["acordaos", "sentencas"]
```

### Configuração do WebDriver

Para uso com Chrome:
```bash
# Instale o ChromeDriver
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
# Adicione ao PATH ou configure no código
```

## 🎮 Uso

### Estrutura de Dados

O sistema trabalha com três principais entidades:

1. **ProcessoJudicial**: Dados dos processos coletados
2. **ResultadoNLP**: Resultados do processamento de linguagem natural
3. **LogExecucao**: Logs de operações do sistema

### Exemplo de Uso Básico

```python
from src.acoes_coletivas.database.manager import DatabaseManager
from src.acoes_coletivas.scraper.base import BaseScraper
from src.acoes_coletivas.config.settings import settings

# Inicializar o banco de dados
db = DatabaseManager()

# Verificar estatísticas
stats = db.get_stats()
print(f"Total de processos: {stats['total_processos']}")
print(f"Processos processados: {stats['processos_processados']}")
```

### Coleta de Dados

```python
# Exemplo de coleta manual
scraper = SeleniumScraper()  # Implementar baseado em BaseScraper

# Inicializar sessão
if scraper.initialize_session():
    # Definir tokens (obtidos manualmente)
    scraper.set_tokens(session_id="seu_session_id", juris_token="seu_token")
    
    # Processar lista de processos
    processos = ["0001203-03.2018.5.10.0021", "0001204-03.2018.5.10.0021"]
    documents = scraper.process_processo_list(processos)
    
    # Salvar no banco
    for doc in documents:
        processo = ProcessoJudicial.from_dict(doc)
        db.insert_processo(processo)
```

## 📊 Estrutura do Banco de Dados

### Tabela: processos_judiciais
```sql
CREATE TABLE processos_judiciais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_processo TEXT NOT NULL,
    numero_processo_planilha TEXT NOT NULL,
    tribunal TEXT,
    classe_processo TEXT,
    tipo_documento TEXT,
    data_julgamento TEXT,
    data_publicacao TEXT,
    relator TEXT,
    partes TEXT,
    link_decisao TEXT,
    conteudo_bruto_decisao TEXT,
    origem_texto TEXT,
    colecao_api TEXT,
    id_documento_api TEXT,
    processado_nlp BOOLEAN DEFAULT FALSE,
    data_coleta TEXT NOT NULL,
    data_processamento TEXT,
    metadados TEXT
);
```

### Tabela: resultados_nlp
```sql
CREATE TABLE resultados_nlp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processo_id INTEGER NOT NULL,
    resumo_extrativo TEXT,
    palavras_chave TEXT,
    tema_principal TEXT,
    sentimento TEXT,
    entidades_nomeadas TEXT,
    metadados_nlp TEXT,
    data_processamento TEXT NOT NULL,
    FOREIGN KEY (processo_id) REFERENCES processos_judiciais (id)
);
```

## 🔍 Sistema de Logging

O sistema utiliza logging estruturado com suporte a:
- Logs em arquivo e console
- Formato JSON para análise
- Métricas de performance
- Rastreamento de erros
- Contexto de operações

Exemplo de log:
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "info",
    "logger": "DatabaseManager",
    "event": "processo_inserted",
    "processo_id": 123,
    "numero_processo": "0001203-03.2018.5.10.0021"
}
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=src/acoes_coletivas

# Executar testes específicos
pytest tests/test_database.py
```

## 📈 Monitoramento

### Métricas Disponíveis

- Total de processos coletados
- Processos processados por NLP
- Taxa de sucesso das coletas
- Tempo de execução das operações
- Erros e exceções

### Logs de Operação

Todos os logs são armazenados em:
- `logs/acoes_coletivas.log` (arquivo)
- Console (durante execução)
- Banco de dados (tabela `logs_execucao`)

## 🔒 Segurança

- Tokens de autenticação não são armazenados em logs
- Configurações sensíveis via variáveis de ambiente
- Validação de entrada de dados
- Rate limiting para evitar bloqueios

## 🚀 Desenvolvimento

### Adicionando Novos Scrapers

1. Herde de `BaseScraper`
2. Implemente os métodos abstratos
3. Adicione logging apropriado
4. Inclua testes unitários

```python
from src.acoes_coletivas.scraper.base import BaseScraper, SearchParams, ScrapingResult

class MeuScraper(BaseScraper):
    def initialize_session(self) -> bool:
        # Implementar inicialização
        pass
    
    def search_documents(self, params: SearchParams) -> ScrapingResult:
        # Implementar busca
        pass
    
    def extract_document_content(self, document: dict) -> dict:
        # Implementar extração
        pass
    
    def cleanup(self):
        # Implementar limpeza
        pass
```

### Padrões de Código

- Use type hints
- Docstrings para funções públicas
- Logging estruturado
- Tratamento de exceções
- Testes unitários

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Abra um Pull Request

## 📄 Scripts Legados

Os scripts originais estão mantidos para referência:
- `1 - extrair dados selenium.py`
- `1.1 - extrair dados.py`
- `2 - resumo etapa 1.py`
- `3 - resumo_etapa_2.py`
- `4 - última etapa.py`

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs em `logs/acoes_coletivas.log`
2. Consulte a documentação técnica
3. Abra uma issue no repositório

## 🗺️ Roadmap

### Versão 1.1
- [ ] Interface CLI completa
- [ ] Processamento NLP avançado
- [ ] Exportação para Excel/PDF
- [ ] Relatórios automatizados

### Versão 1.2
- [ ] Interface web
- [ ] Dashboard interativo
- [ ] API REST
- [ ] Integração com PostgreSQL

### Versão 2.0
- [ ] Machine Learning para classificação
- [ ] Análise preditiva
- [ ] Integração com outros sistemas
- [ ] Escalabilidade para grandes volumes

## 📝 Changelog

### v1.0.0 (Atual)
- ✅ Estrutura profissional do projeto
- ✅ Sistema de banco de dados SQLite
- ✅ Logging estruturado
- ✅ Configuração centralizada
- ✅ Base para scrapers
- ✅ Documentação completa

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

**Desenvolvido com 💙 para automatizar a análise de ações coletivas judiciais** 