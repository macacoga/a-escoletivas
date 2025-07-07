# 🚀 Guia de Utilização - Ferramenta de Análise de Ações Coletivas

## 📋 Visão Geral

Sua ferramenta está **100% funcional** com as 3 fases implementadas:

✅ **Fase 1**: Coleta de dados (Selenium + Requests)  
✅ **Fase 2**: Processamento NLP (Sumarização, palavras-chave, temas)  
✅ **Fase 3**: API RESTful (Flask + Endpoints completos)

## 🎯 Como Usar a Ferramenta

### 1. **Instalação Rápida** (Primeira vez)

```bash
# Opção 1: Instalação automática (Recomendado)
python quick_install.py

# Opção 2: Instalação manual
python install_windows.py

# Opção 3: Instalação tradicional
pip install -r requirements.txt
python install_spacy_model.py
```

### 2. **Verificar Instalação**

```bash
python verify_installation.py
```

### 3. **Iniciar a API**

```bash
# Inicializador completo (recomendado)
python start_api.py

# Ou diretamente
python app.py
```

## 🔍 **Como Usar a API**

### **Acessar a API:**
- **URL Principal**: http://localhost:5000
- **Documentação**: http://localhost:5000/api/docs/
- **Health Check**: http://localhost:5000/health

### **Endpoints Principais:**

#### 1. **Listar Todas as Ações** (com paginação)
```bash
GET http://localhost:5000/api/acoes?page=1&per_page=10
```

#### 2. **Buscar Ações Específicas**
```bash
# Por palavras-chave
GET http://localhost:5000/api/acoes/search?keywords=banco brasil

# Por número do processo
GET http://localhost:5000/api/acoes/search?processo=0001203-03.2018.5.10.0021

# Por partes envolvidas
GET http://localhost:5000/api/acoes/search?partes=Banco do Brasil

# Por data de publicação
GET http://localhost:5000/api/acoes/search?data_inicio=2023-01-01&data_fim=2023-12-31
```

#### 3. **Ver Detalhes de uma Ação**
```bash
GET http://localhost:5000/api/acoes/1
```

#### 4. **Listar Tópicos Frequentes**
```bash
GET http://localhost:5000/api/topicos
```

#### 5. **Ver Estatísticas**
```bash
GET http://localhost:5000/api/stats/geral
```

## 🧪 **Testar a API**

```bash
# Executar testes automatizados
python test_api.py

# Ou usar curl/exemplos
```

## 📊 **Exemplos Práticos de Uso**

### **Exemplo 1: Encontrar ações sobre "Banco do Brasil"**
```bash
curl "http://localhost:5000/api/acoes/search?keywords=banco%20brasil&page=1&per_page=5"
```

### **Exemplo 2: Ver ações de 2023**
```bash
curl "http://localhost:5000/api/acoes/search?data_inicio=2023-01-01&data_fim=2023-12-31"
```

### **Exemplo 3: Ver detalhes de uma ação específica**
```bash
curl "http://localhost:5000/api/acoes/1"
```

## 🎮 **Interface Web (Swagger UI)**

1. Acesse: http://localhost:5000/api/docs/
2. Teste os endpoints diretamente no navegador
3. Veja a documentação completa de cada endpoint

## 📁 **Estrutura dos Dados**

### **Resposta Típica de uma Ação:**
```json
{
  "id": 1,
  "numero_processo": "0001203-03.2018.5.10.0021",
  "tribunal": "TRT-10",
  "classe_processo": "Ação Coletiva",
  "data_publicacao": "2023-01-15",
  "relator": "Dr. João Silva",
  "partes": "Banco do Brasil vs. Sindicato dos Bancários",
  "resumo": "Ação coletiva sobre pagamento de horas extras...",
  "palavras_chave": ["horas extras", "banco", "sindicato"],
  "tema_principal": "Direito do Trabalho",
  "sentimento": "neutro"
}
```

## 🔧 **Configurações Avançadas**

### **Variáveis de Ambiente** (arquivo `.env`):
```env
FLASK_ENV=development
DATABASE_URL=sqlite:///data/acoes_coletivas.db
DEBUG=true
```

### **Logs da Aplicação:**
- **Arquivo**: `logs/api.log`
- **Nível**: INFO, ERROR, DEBUG

## 🚨 **Solução de Problemas**

### **API não inicia:**
```bash
# Verificar se as dependências estão instaladas
python verify_installation.py

# Reinstalar dependências
python quick_install.py
```

### **Banco de dados não encontrado:**
```bash
# Executar os scripts de coleta primeiro:
python "1 - extrair dados selenium.py"
python "2 - resumo etapa 1.py"
python "3 - resumo_etapa_2.py"
python "4 - última etapa.py"
```

### **Erro de porta em uso:**
```bash
# Mudar porta no app.py ou matar processo na porta 5000
```

## 📈 **Fluxo Completo de Trabalho**

### **1. Coleta de Dados** (já feito)
- Scripts 1-4 já executados
- Dados no banco SQLite

### **2. Processamento NLP** (já feito)
- Resumos extraídos
- Palavras-chave identificadas
- Temas classificados

### **3. Consulta via API** (uso atual)
```bash
# Iniciar API
python start_api.py

# Consultar dados
curl http://localhost:5000/api/acoes
```

## 🎯 **Casos de Uso Típicos**

### **Para Pesquisadores:**
- Buscar ações por tema específico
- Analisar tendências temporais
- Extrair resumos para análise qualitativa

### **Para Advogados:**
- Encontrar jurisprudência similar
- Analisar argumentos utilizados
- Verificar posicionamentos dos tribunais

### **Para Analistas:**
- Gerar relatórios estatísticos
- Identificar padrões nos dados
- Exportar dados para análise externa

## 💡 **Dicas de Uso**

1. **Use a documentação Swagger** para explorar todos os endpoints
2. **Combine filtros** para buscas mais precisas
3. **Use paginação** para grandes volumes de dados
4. **Monitore os logs** para debug
5. **Faça backup** do banco de dados regularmente

## 🔄 **Próximos Passos**

A ferramenta está **pronta para uso**! Você pode:

1. **Usar a API** para consultar os dados
2. **Integrar com outras ferramentas** (Excel, Power BI, etc.)
3. **Desenvolver interfaces** específicas
4. **Adicionar novos endpoints** conforme necessário

---

## 🆘 **Suporte**

Se encontrar problemas:
1. Verifique os logs em `logs/`
2. Execute `python verify_installation.py`
3. Consulte a documentação em `README_API.md`
4. Use `python test_api.py` para verificar funcionamento

**🎉 Sua ferramenta está 100% operacional!** 