@echo off
echo ===================================
echo    Iniciando PyWallet - Setup    
echo ===================================
echo.

REM Matar processos python existentes que possam estar usando a porta do Streamlit
echo Verificando e encerrando instancias anteriores do Streamlit...
taskkill /F /FI "WINDOWTITLE eq Streamlit*" /T >nul 2>&1
taskkill /F /FI "IMAGENAME eq streamlit.exe" /T >nul 2>&1
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Streamlit*" /T >nul 2>&1

REM Matar processo na porta 8501 (usada pelo Streamlit por padrão)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Pequena pausa para garantir que os processos foram encerrados
timeout /t 1 /nobreak >nul

REM Verificar se o Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado. Tentando com Python3...
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERRO: Python3 tambem nao encontrado.
        echo Por favor, instale o Python 3.7 ou superior e tente novamente.
        echo Voce pode baixar o Python em: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

REM Verificar se o pip está disponível
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: pip nao encontrado.
    echo Por favor, instale o pip e tente novamente.
    pause
    exit /b 1
)

echo Python encontrado. Instalando dependencias...

REM Instalar dependências diretamente (sem ambiente virtual)
echo Instalando dependencias...
%PYTHON_CMD% -m pip install --user streamlit pandas numpy plotly openpyxl xlrd yfinance
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar dependencias.
    pause
    exit /b 1
)

REM Verificar se a pasta data existe
if not exist "data" (
    echo Criando estrutura de pastas...
    mkdir data
    mkdir data\portfolios
)

REM Verificar se os diretórios components e utils têm arquivos __init__.py
if not exist "components\__init__.py" (
    echo Criando arquivos de inicialização de pacotes...
    echo # Este arquivo permite que Python trate o diretório como um pacote > components\__init__.py
)

if not exist "utils\__init__.py" (
    echo # Este arquivo permite que Python trate o diretório como um pacote > utils\__init__.py
)

REM Verificar se a pasta .streamlit existe e criar se necessário
if not exist ".streamlit" (
    mkdir .streamlit
)

REM Criar ou atualizar arquivo de configuração do Streamlit para acesso em rede
echo Configurando Streamlit...
echo [server] > .streamlit\config.toml
echo headless = false >> .streamlit\config.toml
echo port = 8501 >> .streamlit\config.toml
echo enableCORS = false >> .streamlit\config.toml
echo runOnSave = true >> .streamlit\config.toml
echo address = "0.0.0.0" >> .streamlit\config.toml
echo. >> .streamlit\config.toml
echo [browser] >> .streamlit\config.toml
echo serverAddress = "localhost" >> .streamlit\config.toml
echo serverPort = 8501 >> .streamlit\config.toml
echo gatherUsageStats = false >> .streamlit\config.toml

echo.
echo ===================================
echo    Iniciando PyWallet    
echo ===================================
echo.

REM Obter e mostrar IPs da máquina para facilitar acesso via rede
echo Enderecos IP para acesso:
ipconfig | findstr /i "ipv4"
echo.
echo Voce pode acessar o aplicativo em:
echo - Localmente: http://localhost:8501
echo - Em rede: http://SEU_IP:8501 (substitua SEU_IP por um dos enderecos acima)
echo.

REM Configurar para abrir automaticamente no navegador
set STREAMLIT_SERVER_HEADLESS=false
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
set STREAMLIT_SERVER_PORT=8501
set STREAMLIT_SERVER_ADDRESS=0.0.0.0
set STREAMLIT_BROWSER_SERVER_ADDRESS=localhost

REM Iniciar a aplicação com abertura automática do navegador
%PYTHON_CMD% -m streamlit run app.py

REM Pausar para ver qualquer erro
pause