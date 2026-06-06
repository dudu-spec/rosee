@echo off
title Rosee - Instagram Automation

echo ============================================
echo  Rosee - Automacao Instagram
echo ============================================
echo.
echo Escolha uma opcao:
echo  1 - Iniciar Backend (FastAPI :8000)
echo  2 - Iniciar Frontend (Streamlit :8501)
echo  3 - Iniciar Ambos (2 janelas)
echo  4 - Inicializar Banco e Templates
echo  5 - Sair
echo.

set /p opt="Opcao: "

if "%opt%"=="1" (
    cd /d "%~dp0app"
    python main.py backend
    pause
)
if "%opt%"=="2" (
    cd /d "%~dp0app"
    python main.py frontend
    pause
)
if "%opt%"=="3" (
    start "Rosee Backend" cmd /c "cd /d %~dp0app && python main.py backend"
    timeout /t 3 /nobreak >nul
    start "Rosee Frontend" cmd /c "cd /d %~dp0app && python main.py frontend"
    echo.
    echo Backend: http://localhost:8000
    echo Frontend: http://localhost:8501
    echo.
    echo Pressione qualquer tecla para encerrar ambos...
    pause >nul
    taskkill /f /fi "WINDOWTITLE eq Rosee Backend" >nul 2>&1
    taskkill /f /fi "WINDOWTITLE eq Rosee Frontend" >nul 2>&1
)
if "%opt%"=="4" (
    cd /d "%~dp0app"
    python main.py init
    pause
)
if "%opt%"=="5" (
    exit /b
)
if "%opt%"=="" (
    echo Opcao invalida.
    pause
    goto :eof
)
