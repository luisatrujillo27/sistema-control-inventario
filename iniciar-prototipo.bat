@echo off
REM Sirve el prototipo navegable por HTTP.
REM Es necesario: abierto como file:// el navegador no carga CSS ni JS.
setlocal
set "RAIZ=%~dp0"
cd /d "%RAIZ%prototipo"
title Prototipo navegable - Inventario

set "PY_EXE="
if exist "%RAIZ%.venv\Scripts\python.exe" set "PY_EXE=%RAIZ%.venv\Scripts\python.exe"
if not defined PY_EXE (
    where py >nul 2>&1 && set "PY_EXE=py"
)
if not defined PY_EXE (
    where python >nul 2>&1 && set "PY_EXE=python"
)
if not defined PY_EXE (
    echo [ERROR] No se encontro Python en el sistema.
    echo         Instalalo desde https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Sirviendo el prototipo en http://127.0.0.1:5500
echo Para detenerlo, pulsa Ctrl+C en esta ventana.
echo.
start "" "http://127.0.0.1:5500/index.html"
"%PY_EXE%" -m http.server 5500 --bind 127.0.0.1

pause
