# Instalação no Windows

## Problemas Comuns e Soluções

### 1. Erro de Compilação C++

Se você encontrar erros como "Microsoft Visual C++ 14.0 is required", siga uma destas soluções:

#### Solução 1: Instalar Microsoft Build Tools
```bash
# Baixe e instale o Microsoft Build Tools for Visual Studio
# https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
```

#### Solução 2: Usar versões pré-compiladas
```bash
# Instale as bibliotecas problemáticas primeiro
pip install --only-binary=all numpy pandas scipy scikit-learn

# Depois instale o resto
pip install -r requirements.txt
```

#### Solução 3: Usar Conda (Recomendado)
```bash
# Instale o Anaconda ou Miniconda
# https://www.anaconda.com/products/distribution

# Crie um ambiente virtual
conda create -n acoes-coletivas python=3.10
conda activate acoes-coletivas

# Instale as bibliotecas científicas via conda
conda install numpy pandas scikit-learn scipy
conda install -c conda-forge spacy nltk

# Instale o resto via pip
pip install -r requirements.txt
```

### 2. Problemas com spaCy

```bash
# Instale o spaCy primeiro
pip install spacy

# Baixe o modelo português
python -m spacy download pt_core_news_sm
```

### 3. Problemas com NLTK

```bash
# Depois de instalar o NLTK, baixe os dados necessários
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

### 4. Problemas com Selenium

```bash
# Instale o webdriver-manager para gerenciar drivers automaticamente
pip install webdriver-manager
```

## Instalação Passo a Passo

### Método 1: Instalação Básica
```bash
# 1. Clone o repositório
git clone <seu-repositorio>
cd acoes-coletivas

# 2. Crie um ambiente virtual
python -m venv venv
venv\Scripts\activate

# 3. Atualize o pip
python -m pip install --upgrade pip

# 4. Instale as dependências
pip install -r requirements.txt

# 5. Execute o script de configuração
python setup.py
```

### Método 2: Instalação com Conda (Recomendado)
```bash
# 1. Instale o Anaconda/Miniconda
# 2. Crie um ambiente
conda create -n acoes-coletivas python=3.10
conda activate acoes-coletivas

# 3. Instale bibliotecas científicas
conda install numpy pandas scikit-learn scipy matplotlib seaborn
conda install -c conda-forge spacy nltk transformers

# 4. Instale o resto via pip
pip install flask flask-restx flask-cors marshmallow waitress
pip install beautifulsoup4 selenium lxml openpyxl
pip install sumy textstat bleach html2text wordcloud
pip install pytest pytest-cov black flake8
pip install python-dotenv click tqdm colorama structlog
pip install jsonschema pydantic pydantic-settings
pip install sqlalchemy alembic python-dateutil

# 5. Baixe modelos do spaCy e NLTK
python -m spacy download pt_core_news_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

### Método 3: Instalação com Python do Microsoft Store
```bash
# 1. Instale o Python do Microsoft Store
# 2. Use o método básico acima
```

## Verificação da Instalação

Execute o script de verificação:
```bash
python verify_installation.py
```

## Problemas Específicos

### Erro: "Failed building wheel for numpy"
```bash
pip install --only-binary=numpy numpy
```

### Erro: "Failed building wheel for pandas"
```bash
pip install --only-binary=pandas pandas
```

### Erro: "Failed building wheel for scikit-learn"
```bash
pip install --only-binary=scikit-learn scikit-learn
```

### Erro de encoding no Windows
```bash
# Defina a variável de ambiente
set PYTHONIOENCODING=utf-8
```

## Alternativas de Instalação

### requirements-windows.txt (Versões Específicas)
Se ainda tiver problemas, use o arquivo `requirements-windows.txt` com versões específicas testadas no Windows.

### Docker (Avançado)
```bash
# Use o Docker para evitar problemas de compatibilidade
docker build -t acoes-coletivas .
docker run -p 5000:5000 acoes-coletivas
``` 