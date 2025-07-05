# Instalação Rápida - Projeto Ações Coletivas

## Método 1: Instalação Automática (Recomendado)

```bash
# 1. Clone o repositório e entre na pasta
git clone <seu-repositorio>
cd acoes-coletivas

# 2. Crie e ative um ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# 3. Execute o script de instalação automática
python install_windows.py
```

## Método 2: Instalação Manual

### Passo 1: Instalar pacotes científicos primeiro
```bash
# Instale numpy, pandas e scikit-learn usando wheels pré-compilados
pip install --only-binary=numpy numpy
pip install --only-binary=pandas pandas
pip install --only-binary=scikit-learn scikit-learn
```

### Passo 2: Instalar o resto das dependências
```bash
# Use o requirements.txt padrão
pip install -r requirements.txt

# OU use a versão específica para Windows
pip install -r requirements-windows.txt
```

### Passo 3: Baixar modelos de NLP
```bash
# Modelo do spaCy
python -m spacy download pt_core_news_sm

# Dados do NLTK
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

## Método 3: Usando Conda (Mais Seguro)

```bash
# 1. Instale o Anaconda ou Miniconda
# 2. Crie um ambiente
conda create -n acoes-coletivas python=3.10
conda activate acoes-coletivas

# 3. Instale bibliotecas científicas via conda
conda install numpy pandas scikit-learn scipy
conda install -c conda-forge spacy nltk transformers

# 4. Instale o resto via pip
pip install flask flask-restx flask-cors marshmallow waitress
pip install beautifulsoup4 selenium lxml openpyxl
pip install sumy textstat bleach html2text wordcloud
pip install python-dotenv click tqdm colorama structlog
pip install jsonschema pydantic pydantic-settings
pip install sqlalchemy alembic python-dateutil

# 5. Baixe modelos
python -m spacy download pt_core_news_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

## Verificação da Instalação

Após a instalação, execute:
```bash
python verify_installation.py
```

## Problemas Comuns

### Erro: "Microsoft Visual C++ 14.0 is required"
**Solução 1:** Instale o Microsoft Build Tools
- Baixe de: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022

**Solução 2:** Use wheels pré-compilados
```bash
pip install --only-binary=all numpy pandas scipy scikit-learn
```

### Erro: "Failed building wheel for numpy"
```bash
pip install --only-binary=numpy numpy
```

### Erro: "No module named 'spacy'"
```bash
pip install spacy
python -m spacy download pt_core_news_sm
```

## Arquivos de Configuração

- `requirements.txt` - Dependências gerais (versões flexíveis)
- `requirements-windows.txt` - Versões específicas testadas no Windows
- `INSTALL_WINDOWS.md` - Instruções detalhadas para Windows
- `install_windows.py` - Script de instalação automática
- `verify_installation.py` - Verificação da instalação

## Próximos Passos

Após a instalação bem-sucedida:

1. **Configurar o banco de dados:**
   ```bash
   python -c "from src.acoes_coletivas.database.manager import DatabaseManager; DatabaseManager().create_tables()"
   ```

2. **Testar o sistema:**
   ```bash
   python -m pytest tests/
   ```

3. **Executar a API:**
   ```bash
   python app.py
   ```

4. **Usar a CLI:**
   ```bash
   python -m src.acoes_coletivas.cli.main --help
   ```

## Suporte

Se ainda tiver problemas:
1. Consulte `INSTALL_WINDOWS.md` para soluções detalhadas
2. Verifique se está usando Python 3.8 ou superior
3. Considere usar o Anaconda/Miniconda para evitar problemas de compilação
4. Execute `python verify_installation.py` para diagnóstico 