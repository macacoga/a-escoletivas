# Migração para NLP Aprimorado - v2.0.0

## Resumo das Mudanças

O sistema foi migrado para usar o **pipeline NLP aprimorado** que oferece recursos muito mais avançados de análise de decisões judiciais.

## Principais Melhorias

### 🚀 Novos Recursos
- **Extração de partes do processo**: Identifica automaticamente reclamante e reclamado
- **Extração de referências legislativas**: Captura artigos de lei, constituição, etc.
- **Resumo estruturado**: Análise detalhada com pedidos, fundamentação e resultado
- **Análise de valores monetários**: Identifica valores envolvidos no processo
- **Score de confiança aprimorado**: Métrica mais precisa da qualidade da análise

### 📊 Melhorias nos Dados
- **Versão do pipeline**: Atualizada para 2.0.0
- **Método de sumarização**: Agora usa 'enhanced_structured'
- **Metadados expandidos**: Inclui partes formatadas e referências formatadas
- **Resultado principal**: Identificação clara do desfecho do processo

## Mudanças Técnicas

### Arquivos Modificados

1. **`src/acoes_coletivas/database/manager.py`**
   - Função `processar_texto_nlp()` agora usa `process_text_enhanced()`
   - Removida função duplicada `processar_texto_nlp_enhanced()`
   - Atualizada versão do pipeline para 2.0.0

2. **`src/acoes_coletivas/nlp/nlp_pipeline.py`**
   - Função `batch_process()` usa processamento aprimorado
   - Função `create_analysis_report()` adaptada para novos dados
   - Função `export_results_to_json()` atualizada
   - Função `get_pipeline_stats()` inclui novos componentes
   - Função `validate_pipeline()` testa todos os componentes

3. **`src/acoes_coletivas/cli/main.py`**
   - Interface atualizada para mostrar recursos aprimorados
   - Validação melhorada com separação de componentes básicos e aprimorados
   - Estatísticas expandidas com informações sobre métodos de sumarização

## Compatibilidade

### ✅ Compatível
- Todos os comandos CLI existentes continuam funcionando
- Estrutura do banco de dados permanece a mesma
- APIs existentes mantêm compatibilidade

### 🔄 Melhorias Automáticas
- Processamentos novos usam automaticamente o pipeline aprimorado
- Reprocessamento de NLPs existentes usa a nova versão
- Estatísticas incluem informações sobre recursos aprimorados

## Como Usar

### Validação do Pipeline
```bash
python acoes_coletivas.py nlp validate
```

### Processamento de Textos
```bash
# Processar lote
python acoes_coletivas.py nlp process --limit 50

# Processar processo específico
python acoes_coletivas.py nlp process --id 123

# Processar múltiplos processos
python acoes_coletivas.py nlp process --ids 123,456,789
```

### Estatísticas
```bash
python acoes_coletivas.py nlp stats
```

### Exportação
```bash
python acoes_coletivas.py nlp export -o resultados.json
```

## Novos Campos nos Resultados

### Dados Estruturados
- `structured_summary`: Resumo detalhado com pedidos, fundamentação e resultado
- `parts_data`: Informações sobre reclamante e reclamado
- `legal_references`: Referências legislativas extraídas
- `resultado_principal`: Desfecho principal do processo

### Metadados Aprimorados
- `partes_formatadas`: Texto formatado das partes
- `referencias_formatadas`: Texto formatado das referências
- `palavras_chave`: Lista de palavras-chave extraídas
- `versao_pipeline`: "2.0.0"
- `metodo_sumarizacao`: "enhanced_structured"

## Benefícios

### Para Usuários
- **Análise mais precisa**: Melhor identificação de entidades e direitos
- **Informações estruturadas**: Dados organizados e fáceis de consultar
- **Maior confiança**: Score de confiança mais preciso
- **Recursos avançados**: Extração de partes e referências legislativas

### Para Desenvolvedores
- **Código mais limpo**: Função única para processamento aprimorado
- **Melhor validação**: Testes completos de todos os componentes
- **Estatísticas detalhadas**: Métricas sobre todos os recursos
- **Compatibilidade mantida**: Não quebra funcionalidades existentes

## Próximos Passos

1. **Testar o pipeline**: Execute `python acoes_coletivas.py nlp validate`
2. **Processar alguns textos**: Use `python acoes_coletivas.py nlp process --limit 10`
3. **Verificar estatísticas**: Execute `python acoes_coletivas.py nlp stats`
4. **Explorar novos dados**: Analise os resultados JSON exportados

## Suporte

Se encontrar problemas:
1. Verifique se todos os componentes estão instalados
2. Execute a validação do pipeline
3. Consulte os logs para detalhes de erro
4. Reprocesse textos problemáticos se necessário 