# 🚀 Como Usar a Ferramenta - Resumo Rápido

## ✅ Status: **PRONTA PARA USO**

Sua ferramenta está **100% funcional** com todas as 3 fases implementadas!

---

## 🎯 **3 Passos Simples para Usar**

### **Passo 1: Instalar (se ainda não fez)**
```bash
python quick_install.py
```

### **Passo 2: Iniciar a API**
```bash
python start_api.py
```

### **Passo 3: Usar a Ferramenta**
- **No navegador**: http://localhost:5000/api/docs/
- **Teste rápido**: `python demo_uso.py`

---

## 🔍 **Principais Funcionalidades**

### **1. Listar Todas as Ações**
```
GET http://localhost:5000/api/acoes?page=1&per_page=10
```

### **2. Buscar por Palavras-chave**
```
GET http://localhost:5000/api/acoes/search?keywords=banco brasil
```

### **3. Buscar por Data**
```
GET http://localhost:5000/api/acoes/search?data_inicio=2023-01-01&data_fim=2023-12-31
```

### **4. Ver Detalhes de uma Ação**
```
GET http://localhost:5000/api/acoes/1
```

### **5. Ver Tópicos Frequentes**
```
GET http://localhost:5000/api/topicos
```

### **6. Ver Estatísticas**
```
GET http://localhost:5000/api/stats/geral
```

---

## 🎮 **Interface Web (Mais Fácil)**

1. **Inicie a API**: `python start_api.py`
2. **Abra no navegador**: http://localhost:5000/api/docs/
3. **Teste os endpoints** diretamente na interface

---

## 📊 **O que Você Pode Fazer**

### **Para Pesquisadores:**
- Buscar ações por tema específico
- Analisar tendências temporais
- Extrair resumos para análise

### **Para Advogados:**
- Encontrar jurisprudência similar
- Analisar argumentos utilizados
- Verificar posicionamentos dos tribunais

### **Para Analistas:**
- Gerar relatórios estatísticos
- Identificar padrões nos dados
- Exportar dados para análise externa

---

## 🚨 **Se Algo Não Funcionar**

### **API não inicia:**
```bash
python verify_installation.py
python quick_install.py
```

### **Banco de dados não encontrado:**
```bash
# Execute os scripts de coleta primeiro:
python "1 - extrair dados selenium.py"
python "2 - resumo etapa 1.py"
python "3 - resumo_etapa_2.py"
python "4 - última etapa.py"
```

---

## 💡 **Dicas Rápidas**

1. **Use a interface Swagger** - É mais fácil que comandos
2. **Combine filtros** - Busque por palavra + data + tribunal
3. **Use paginação** - Para grandes volumes de dados
4. **Monitore os logs** - Em caso de problemas

---

## 🎉 **Pronto!**

Sua ferramenta está **operacional** e pronta para:
- ✅ Consultar dados coletados
- ✅ Buscar por critérios específicos
- ✅ Analisar resumos e temas
- ✅ Gerar estatísticas
- ✅ Integrar com outras ferramentas

**Agora é só usar!** 🚀 